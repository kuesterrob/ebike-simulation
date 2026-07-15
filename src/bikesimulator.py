import logging
from pathlib import Path
import numpy as np
import pandas as pd

from src.gps_reader import GPSReader
from src.route_calculator import RouteCalculator
from src.motor import Motor
from src.lipo_battery import LiPoBatteryPack
from src.nmc_battery import NMCBatteryPack


logger = logging.getLogger(__name__)


class BikeSimulator:
    """Führt die komplette E-Bike-Simulation durch."""

    def __init__(
        self,
        gps_file: Path,
        battery_capacity_ah: float = 50.0,
        initial_soc: float = 1.0,
        filter_window: int = 5,
    ) -> None:
        self.gps_file = Path(gps_file)
        self.battery_capacity_ah = battery_capacity_ah
        self.initial_soc = initial_soc
        self.filter_window = filter_window

        self._validate_parameters()

    def _validate_parameters(self) -> None:
        """Überprüft die Simulationsparameter."""

        if self.battery_capacity_ah <= 0:
            raise ValueError(
                "Die Akkukapazität muss größer "
                "als 0 sein."
            )

        if not 0 < self.initial_soc <= 1:
            raise ValueError(
                "Der Ladezustand muss zwischen "
                "0 und 1 liegen."
            )

        if self.filter_window < 1:
            raise ValueError(
                "Die Filtergröße muss mindestens "
                "1 sein."
            )

    def run(self) -> dict:
        """Führt die Simulation aus."""

        logger.info(
            "E-Bike-Simulation wird ausgeführt"
        )

    
        # GPS-Daten
        reader = GPSReader()

        dataframe = reader.load_file(
            self.gps_file
        )

        distances = reader.calculate_distances()

        dataframe["time"] = pd.to_datetime(dataframe["time"], utc=True)
        dataframe["time"] = dataframe["time"].dt.tz_convert("Europe/Vienna")

        time = dataframe["time"].dt.tz_localize(None).to_numpy()

        time_deltas = (
            dataframe["time"]
            .diff()
            .dt.total_seconds()
            .to_numpy()
        )

        # Der erste Wert ist NaN.
        time_deltas = time_deltas[1:]

        total_distance = np.concatenate(
            (
                [0.0],
                np.cumsum(distances),
            )
        )

        # Route
        route_calculator = RouteCalculator()

        speeds = (
            route_calculator.calculate_speed(
                time_deltas,
                distances,
            )
        )

        accelerations = (
            route_calculator.calculate_acceleration(
                time_deltas,
                speeds,
            )
        )

        # Auffällige Beschleunigungswerte melden.
        outlier_count = int(
            np.sum(
                np.abs(accelerations) > 3.0
            )
        )

        if outlier_count > 0:
            logger.warning(
                "%d Beschleunigungswerte liegen "
                "außerhalb von ±3 m/s²",
                outlier_count,
            )

        elevations = dataframe[
            "ele"
        ].to_numpy(
            dtype=float
        )

        slopes = (
            route_calculator.calculate_slope(
                distances,
                elevations,
            )
        )

        interval_time = time[1:]

        slope_degrees = np.degrees(
            np.arcsin(
                np.clip(
                    slopes,
                    -1.0,
                    1.0,
                )
            )
        )

        # Ungültige oder negative Zeitintervalle entfernen.
        valid_time_deltas = np.nan_to_num(
            time_deltas,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        valid_time_deltas = np.clip(
            valid_time_deltas,
            0.0,
            None,
        )


        # Motor
        motor = Motor()

        motor_results = motor.calculate(
            speeds=speeds,
            accelerations=accelerations,
            slopes=slopes,
        )

        forces = motor_results[
            "force_n"
        ]

        powers = motor_results[
            "power_w"
        ]

        torques = motor_results[
            "torque_nm"
        ]

        motor_currents = motor_results[
            "current_a"
        ]

        # Negative Ströme werden nicht als Rekuperation verwendet.
        negative_current_count = int(
            np.sum(
                motor_currents < 0
            )
        )

        if negative_current_count > 0:
            logger.info(
                "%d negative Motorströme werden "
                "wegen fehlender Rekuperation auf "
                "0 A gesetzt",
                negative_current_count,
            )

        battery_currents = np.clip(
            motor_currents,
            0.0,
            None,
        )

        battery_currents = np.nan_to_num(
            battery_currents,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        # Akkus
        lipo = LiPoBatteryPack(
            capacity_nom_Ah=(
                self.battery_capacity_ah
            ),
            internal_resistance_mOhm=80.0,
            initial_soc=self.initial_soc,
            Vmin=32.0,
            Vmax=42.0,
        )

        nmc = NMCBatteryPack(
            capacity_nom_Ah=(
                self.battery_capacity_ah
            ),
            internal_resistance_mOhm=70.0,
            initial_soc=self.initial_soc,
            Vmin=32.0,
            Vmax=42.0,
        )

        lipo_voltages = []
        nmc_voltages = []

        for current, duration in zip(
            battery_currents,
            valid_time_deltas,
        ):
            current = float(current)
            duration = float(duration)

            lipo.apply_current(
                current=current,
                duration=duration,
            )

            nmc.apply_current(
                current=current,
                duration=duration,
            )

            lipo_voltages.append(
                lipo.voltage(
                    current=current
                )
            )

            nmc_voltages.append(
                nmc.voltage(
                    current=current
                )
            )

        lipo_voltages = np.asarray(
            lipo_voltages,
            dtype=float,
        )

        nmc_voltages = np.asarray(
            nmc_voltages,
            dtype=float,
        )

        # Ungültige Batteriespannungen erkennen.
        if not np.all(
            np.isfinite(lipo_voltages)
        ):
            raise ValueError(
                "Die LiPo-Spannungen enthalten "
                "ungültige Werte."
            )

        if not np.all(
            np.isfinite(nmc_voltages)
        ):
            raise ValueError(
                "Die NMC-Spannungen enthalten "
                "ungültige Werte."
            )


        # Kennzahlen
        duration_seconds = float(
            np.sum(valid_time_deltas)
        )

        distance_meters = float(
            total_distance[-1]
        )

        if duration_seconds > 0:
            average_speed_kmh = (
                distance_meters
                / duration_seconds
                * 3.6
            )
        else:
            average_speed_kmh = 0.0

        positive_powers = np.clip(
            powers,
            0.0,
            None,
        )

        mechanical_energy_wh = float(
            np.sum(
                positive_powers
                * valid_time_deltas
            )
            / 3600.0
        )

        metrics = {
            "total_distance_km": (
                distance_meters / 1000.0
            ),
            "duration_minutes": (
                duration_seconds / 60.0
            ),
            "average_speed_kmh": (
                average_speed_kmh
            ),
            "max_speed_kmh": float(
                np.max(speeds) * 3.6
            ),
            "ascent_m": float(
                reader.climb
            ),
            "descent_m": float(
                reader.descent
            ),
            "max_power_w": float(
                np.max(positive_powers)
            ),
            "max_motor_current_a": float(
                np.max(battery_currents)
            ),
            "mechanical_energy_wh": (
                mechanical_energy_wh
            ),
            "lipo_soc_percent": (
                lipo.soc * 100.0
            ),
            "nmc_soc_percent": (
                nmc.soc * 100.0
            ),
            "min_lipo_voltage_v": float(
                np.min(lipo_voltages)
            ),
            "min_nmc_voltage_v": float(
                np.min(nmc_voltages)
            ),
        }

        logger.info(
            "Simulation abgeschlossen: "
            "%.2f km, LiPo-SOC %.1f %%, "
            "NMC-SOC %.1f %%",
            metrics["total_distance_km"],
            metrics["lipo_soc_percent"],
            metrics["nmc_soc_percent"],
        )

    
        # Ergebnisse zurückgeben
        return {
            "metrics": metrics,

            "time": {
                "all": time,
                "intervals": interval_time,
                "deltas_s": valid_time_deltas,
            },

            "route": {
                "distance_m": distances,
                "total_distance_m": (
                    total_distance
                ),
                "elevation_m": elevations,
                "filtered_elevation_m": (
                    elevations
                ),
                "raw_speed_mps": speeds,
                "speed_mps": speeds,
                "raw_acceleration_mps2": (
                    accelerations
                ),
                "acceleration_mps2": (
                    accelerations
                ),
                "slope": slopes,
                "slope_degrees": (
                    slope_degrees
                ),
            },

            "motor": {
                "force_n": forces,
                "power_w": powers,
                "torque_nm": torques,
                "current_a": motor_currents,
                "battery_current_a": (
                    battery_currents
                ),
            },

            "battery": {
                "lipo_voltage_v": (
                    lipo_voltages
                ),
                "nmc_voltage_v": (
                    nmc_voltages
                ),
                "lipo_soc_percent": (
                    lipo.soc * 100.0
                ),
                "nmc_soc_percent": (
                    nmc.soc * 100.0
                ),
            },
        }