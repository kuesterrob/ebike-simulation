import logging
from pathlib import Path
import numpy as np
import pandas as pd

from src.gps_reader import GPSReader
from src.route_calculator import RouteCalculator
from src.motor import Motor
from src.lipo_battery import LiPoBatteryPack
from src.nmc_battery import NMCBatteryPack
from src.air_density import calculate_air_density
from src.gps_plot_route_on_map import GPSMap
from src.reverse_geocoding import Reverse_Geocoder


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
    
        #Route auf Karte visualisieren
        lats = dataframe["lat"].to_numpy(
            dtype=float
        )
        lons = dataframe["lon"].to_numpy(
            dtype=float
        )
        map_module = GPSMap(lats,lons)
        map_module.save()

        #Reverse Geocoding Daten fetchen
        geo = Reverse_Geocoder(dataframe)
        locations = geo.get_results()

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

        temperatures = dataframe[
            "temperature"
        ].to_numpy(
            dtype=float
        )


        # Geschwindigkeit, Beschleunigung und Steigung beziehen sich immer auf den Abschnitt zwischen zwei GPS-Punkten.
        # Aus beiden Werten wird die mittlere Höhe des Abschnitts gebildet.
        interval_elevations = (
            elevations[:-1]
            + elevations[1:]
        ) / 2.0

        # Auch die Temperatur wird für jeden Streckenabschnitt aus dem Mittelwert von Start- und Endtemperatur bestimmt.
        interval_temperatures = (
            temperatures[:-1]
            + temperatures[1:]
        ) / 2.0

        # Für jeden Streckenabschnitt wird aus der mittleren Temperatur und Höhe eine eigene Luftdichte berechnet.
        air_densities = calculate_air_density(
            temperatures_c=interval_temperatures,
            altitudes_m=interval_elevations,
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
            air_density_kg_per_m3=air_densities,
        )

        forces = motor_results[
            "force_n"
        ]

        rolling_forces = motor_results[
            "rolling_force_n"
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

        # Der Akku stand vor der Fahrt lange genug in derselben Umgebung. Seine Anfangstemperatu entspricht deshalb dem ersten Temperaturwert der CSV-Datei.
        initial_battery_temperature_c = float(
            temperatures[0]
        )

        # Die Anzahl paralleler Zellstränge ist nicht bekannt.
        # Deshalb wird zunächst ein paralleler Strang angenommen.
        battery_parallel_cells = 1

        # Freie thermische Modellannahmen, weil keine
        # Daten für den Akkupack vorhanden sind.
        battery_thermal_capacity_j_per_k = 10_000.0
        battery_thermal_resistance_k_per_w = 2.0

        # Modellannahme:
        # Der Innenwiderstand verändert sich um 1 % pro Kelvin.
        battery_resistance_temperature_coefficient = 0.01

        # Die angegebenen Widerstände werden als Werte
        # bei einer Referenztemperatur von 25 °C interpretiert.
        battery_reference_temperature_c = 25.0

        lipo = LiPoBatteryPack(
            capacity_nom_Ah=(
                self.battery_capacity_ah
            ),
            internal_resistance_mOhm=80.0,
            initial_soc=self.initial_soc,
            Vmin=32.0,
            Vmax=42.0,
            parallel_cells=(
                battery_parallel_cells
            ),
            initial_temperature_c=(
                initial_battery_temperature_c
            ),
            thermal_capacity_j_per_k=(
                battery_thermal_capacity_j_per_k
            ),
            thermal_resistance_k_per_w=(
                battery_thermal_resistance_k_per_w
            ),
            resistance_temperature_coefficient_per_k=(
                battery_resistance_temperature_coefficient
            ),
            reference_temperature_c=(
                battery_reference_temperature_c
            ),
        )

        nmc = NMCBatteryPack(
            capacity_nom_Ah=(
                self.battery_capacity_ah
            ),
            internal_resistance_mOhm=70.0,
            initial_soc=self.initial_soc,
            Vmin=32.0,
            Vmax=42.0,
            parallel_cells=(
                battery_parallel_cells
            ),
            initial_temperature_c=(
                initial_battery_temperature_c
            ),
            thermal_capacity_j_per_k=(
                battery_thermal_capacity_j_per_k
            ),
            thermal_resistance_k_per_w=(
                battery_thermal_resistance_k_per_w
            ),
            resistance_temperature_coefficient_per_k=(
                battery_resistance_temperature_coefficient
            ),
            reference_temperature_c=(
                battery_reference_temperature_c
            ),
        )

        lipo_voltages = []
        nmc_voltages = []

        lipo_temperatures = []
        nmc_temperatures = []

        lipo_internal_resistances = []
        nmc_internal_resistances = []

        for current, duration, ambient_temperature in zip(
            battery_currents,
            valid_time_deltas,
            interval_temperatures,
        ):
            current = float(current)
            duration = float(duration)
            ambient_temperature = float(
                ambient_temperature
            )

            # Zuerst wird der Ladezustand für das
            # aktuelle Zeitintervall aktualisiert.
            lipo.apply_current(
                current=current,
                duration=duration,
            )

            nmc.apply_current(
                current=current,
                duration=duration,
            )

            # Anschließend wird die Temperatur für das
            # Zeitintervall berechnet:
            #
            # T_neu = T_alt+ ((I²R - (T_alt - T_amb)/R_th) * delta_t) / C_th
            lipo.update_temperature(
                current=current,
                duration=duration,
                ambient_temperature_c=(
                    ambient_temperature
                ),
            )

            nmc.update_temperature(
                current=current,
                duration=duration,
                ambient_temperature_c=(
                    ambient_temperature
                ),
            )

            # Die Spannung wird am Ende des Intervalls mit dem neuen SoC und der neuen Temperatur berechnet.
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

            # Temperaturen am Ende des Intervalls speichern.
            lipo_temperatures.append(
                lipo.temperature_c
            )

            nmc_temperatures.append(
                nmc.temperature_c
            )

            # Temperaturabhängige Widerstände speichern.
            lipo_internal_resistances.append(
                lipo.effective_internal_resistance()
            )

            nmc_internal_resistances.append(
                nmc.effective_internal_resistance()
            )

        lipo_voltages = np.asarray(
            lipo_voltages,
            dtype=float,
        )

        nmc_voltages = np.asarray(
            nmc_voltages,
            dtype=float,
        )

        lipo_temperatures = np.asarray(
            lipo_temperatures,
            dtype=float,
        )

        nmc_temperatures = np.asarray(
            nmc_temperatures,
            dtype=float,
        )

        lipo_internal_resistances = np.asarray(
            lipo_internal_resistances,
            dtype=float,
        )

        nmc_internal_resistances = np.asarray(
            nmc_internal_resistances,
            dtype=float,
        )

        # Elektrische Leistung am Ausgang des Akkus:
        #
        # P_Akku = U_Last * I
        #
        # Da U_Last vom temperaturabhängigen Widerstand
        # abhängt, beeinflusst die Temperatur auch diese Leistung.
        lipo_powers = (
            lipo_voltages
            * battery_currents
        )

        nmc_powers = (
            nmc_voltages
            * battery_currents
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
        
        if not (
            np.all(np.isfinite(lipo_temperatures)) and np.all(np.isfinite(nmc_temperatures))
        ):
            raise ValueError(
                "Die Akkutemperaturen enthalten "
                "ungültige Werte."
            )

        if not (
            np.all(np.isfinite(lipo_internal_resistances)) and np.all(np.isfinite(nmc_internal_resistances))
        ):
            raise ValueError(
                "Die Akku-Innenwiderstände enthalten "
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
            "rolling_resistance_coefficient": float(
                motor.rolling_resistance_coefficient
            ),
            "average_rolling_force_n": float(
                np.mean(rolling_forces)
            ),
            "max_rolling_force_n": float(
                np.max(rolling_forces)
            ),
            "average_temperature_c": float(
                np.mean(interval_temperatures)
            ),
            "min_temperature_c": float(
                np.min(interval_temperatures)
            ),
            "max_temperature_c": float(
                np.max(interval_temperatures)
            ),
            "average_air_density_kg_per_m3": float(
                np.mean(air_densities)
            ),
            "min_air_density_kg_per_m3": float(
                np.min(air_densities)
            ),
            "max_air_density_kg_per_m3": float(
                np.max(air_densities)
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
                        "initial_battery_temperature_c": (
                initial_battery_temperature_c
            ),
            "max_lipo_temperature_c": float(
                np.max(lipo_temperatures)
            ),
            "max_nmc_temperature_c": float(
                np.max(nmc_temperatures)
            ),
            "final_lipo_temperature_c": float(
                lipo_temperatures[-1]
            ),
            "final_nmc_temperature_c": float(
                nmc_temperatures[-1]
            ),
            "max_lipo_battery_power_w": float(
                np.max(lipo_powers)
            ),
            "max_nmc_battery_power_w": float(
                np.max(nmc_powers)
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

            "environment": {
                # Originale Temperaturwerte der GPS-Messpunkte.
                "temperature_c": temperatures,

                # Gemittelte Temperatur jedes Streckenabschnitts.
                "interval_temperature_c": (
                    interval_temperatures
                ),

                # Gemittelte Höhe jedes Streckenabschnitts.
                "interval_elevation_m": (
                    interval_elevations
                ),

                # Berechnete Luftdichte jedes Streckenabschnitts.
                "air_density_kg_per_m3": (
                    air_densities
                ),
            },

            "motor": {
                "force_n": forces,
                "rolling_force_n": rolling_forces,
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
                                "lipo_temperature_c": (
                    lipo_temperatures
                ),
                "nmc_temperature_c": (
                    nmc_temperatures
                ),
                "lipo_internal_resistance_ohm": (
                    lipo_internal_resistances
                ),
                "nmc_internal_resistance_ohm": (
                    nmc_internal_resistances
                ),
                "lipo_power_w": (
                    lipo_powers
                ),
                "nmc_power_w": (
                    nmc_powers
                ),
            },
        }