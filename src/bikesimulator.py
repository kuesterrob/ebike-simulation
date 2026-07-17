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
from src.brake_resistor import BrakeResistor
from src.regenerative_braking import RegenerativeBrakingController



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
    
    def _prepare_route_data(self) -> dict:
        """
        Liest die GPS-Datei ein und berechnet alle
        benötigten Routen- und Umgebungsdaten.
        """

        # GPS-Datei einlesen.
        reader = GPSReader()

        dataframe = reader.load_file(
            self.gps_file
        )

        # 3D-Distanzen zwischen den GPS-Punkten berechnen.
        distances = reader.calculate_distances()

        # Zeitstempel vereinheitlichen und in die Zeitzone Europe/Vienna umwandeln.
        dataframe["time"] = pd.to_datetime(
            dataframe["time"],
            utc=True,
        )

        dataframe["time"] = (
            dataframe["time"]
            .dt.tz_convert("Europe/Vienna")
        )

        # Zeitzoneninformation entfernen und die Zeitwerte als NumPy-Array speichern.
        time = (
            dataframe["time"]
            .dt.tz_localize(None)
            .to_numpy()
        )

        # Zeitdifferenz zwischen zwei aufeinanderfolgenden GPS-Punkten in Sekunden berechnen.
        time_deltas = (
            dataframe["time"]
            .diff()
            .dt.total_seconds()
            .to_numpy()
        )

        # Der erste Wert ist NaN, weil es für den ersten GPS-Punkt noch keinen vorherigen Punkt gibt.
        time_deltas = time_deltas[1:]

        # Gesamtstrecke berechnen.
        # Der erste GPS-Punkt liegt bei 0 Metern.
        total_distance = np.concatenate(
            (
                [0.0],
                np.cumsum(distances),
            )
        )

        route_calculator = RouteCalculator()

        # Geschwindigkeit jedes Streckenabschnitts aus Distanz und Zeit berechnen.
        speeds = (
            route_calculator.calculate_speed(
                time_deltas,
                distances,
            )
        )

        # Beschleunigung aus den Geschwindigkeiten und Zeitdifferenzen berechnen.
        accelerations = (
            route_calculator.calculate_acceleration(
                time_deltas,
                speeds,
            )
        )

        # Auffällige Beschleunigungswerte zählen und im Log ausgeben.
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

        # Höhenwerte der GPS-Punkte auslesen.
        elevations = (
            dataframe["ele"]
            .to_numpy(dtype=float)
        )

        # Temperaturwerte der GPS-Punkte auslesen.
        temperatures = (
            dataframe["temperature"]
            .to_numpy(dtype=float)
        )

        # Geschwindigkeit, Beschleunigung und Steigung beziehen sich auf einen Streckenabschnitt.
        # Deshalb wird aus der Höhe am Anfang und Ende des Abschnitts die mittlere Höhe gebildet.
        interval_elevations = (
            elevations[:-1]
            + elevations[1:]
        ) / 2.0

        # Auch für die Temperatur wird der Mittelwert jedes Streckenabschnitts verwendet.
        interval_temperatures = (
            temperatures[:-1]
            + temperatures[1:]
        ) / 2.0

        # Luftdichte für jeden Streckenabschnitt aus Temperatur und Höhe berechnen.
        air_densities = calculate_air_density(
            temperatures_c=interval_temperatures,
            altitudes_m=interval_elevations,
        )

        # Steigung für jeden Streckenabschnitt berechnen.
        slopes = (
            route_calculator.calculate_slope(
                distances,
                elevations,
            )
        )

       
        interval_time = time[1:]

        # Steigung in Grad umrechnen.
        slope_degrees = np.degrees(
            np.arcsin(
                np.clip(
                    slopes,
                    -1.0,
                    1.0,
                )
            )
        )

        # NaN- und unendliche Werte durch 0 ersetzen.
        valid_time_deltas = np.nan_to_num(
            time_deltas,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        # Negative Zeitdifferenzen auf 0 begrenzen.
        valid_time_deltas = np.clip(
            valid_time_deltas,
            0.0,
            None,
        )

        # Alle später benötigten Routenwerte werden gemeinsam in einem Dictionary zurückgegeben.
        return {
            "reader": reader,
            "time": time,
            "interval_time": interval_time,
            "time_deltas": valid_time_deltas,
            "distances": distances,
            "total_distance": total_distance,
            "elevations": elevations,
            "temperatures": temperatures,
            "interval_elevations": (
                interval_elevations
            ),
            "interval_temperatures": (
                interval_temperatures
            ),
            "air_densities": air_densities,
            "speeds": speeds,
            "accelerations": accelerations,
            "slopes": slopes,
            "slope_degrees": slope_degrees,
        }

    def _calculate_motor_data(
        self,
        route_data: dict,
    ) -> dict:
        """
        Berechnet alle Motorwerte aus den zuvor
        vorbereiteten Routendaten.
        """

        # Für die Motorberechnung werden Geschwindigkeit, Beschleunigung, Steigung und Luftdichte benötigt.
        speeds = route_data["speeds"]

        accelerations = route_data[
            "accelerations"
        ]

        slopes = route_data["slopes"]

        air_densities = route_data[
            "air_densities"
        ]

        # Motormodell erzeugen.
        motor = Motor()

        # Kräfte, Leistungen, Drehmomente und Ströme für alle Streckenabschnitte berechnen.
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

        # Vorzeichenbehaftete Motorleistung:
        # positiver Wert = Antrieb
        # negativer Wert = Bremsen
        signed_powers = motor_results[
            "signed_power_w"
        ]

        # Der Bremsleistungsbedarf wird als positiver Betrag gespeichert.
        braking_powers = motor_results[
            "braking_power_w"
        ]

        torques = motor_results[
            "torque_nm"
        ]

        motor_currents = motor_results[
            "current_a"
        ]

        # Prüfen, ob unerwartet negative Motorströme vorhanden sind.
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

        # Für den normalen Antriebsfall werden nur positive Motorströme an den Akku übergeben.
        # Die Rekuperation wird separat über die Bremsleistung berechnet.
        battery_currents = np.clip(
            motor_currents,
            0.0,
            None,
        )

        # Ungültige Stromwerte werden auf 0 A gesetzt.
        battery_currents = np.nan_to_num(
            battery_currents,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        # Alle später benötigten Motorwerte werden gemeinsam zurückgegeben.
        return {
            "motor": motor,
            "forces": forces,
            "rolling_forces": rolling_forces,
            "powers": powers,
            "signed_powers": signed_powers,
            "braking_powers": braking_powers,
            "torques": torques,
            "motor_currents": motor_currents,
            "battery_currents": battery_currents,
        }

    def _create_simulation_components(
        self,
        initial_temperature_c: float,
    ) -> dict:
        """
        Erzeugt die Akkus, den Rekuperationscontroller
        und die Bremswiderstände für die Simulation.
        """

        # Die Anzahl paralleler Zellstränge ist nichtbekannt. 
        # Deshalb wird zunächst ein paralleler Strang angenommen.
        battery_parallel_cells = 1

        # Thermische Modellannahmen für beide Akkupacks.
        battery_thermal_capacity_j_per_k = (
            10_000.0
        )

        battery_thermal_resistance_k_per_w = (
            2.0
        )

        # Der Innenwiderstand verändert sich im Modell um ein Prozent pro Kelvin.
        battery_resistance_temperature_coefficient = (
            0.01
        )

        # Die angegebenen Innenwiderstände gelten bei einer Referenztemperatur von 25 °C.
        battery_reference_temperature_c = 25.0

        # Der Akku darf mit maximal 0,5 C geladen werden.
        battery_max_charge_c_rate = 0.5

        battery_max_charge_current_a = (
            self.battery_capacity_ah
            * battery_max_charge_c_rate
        )

        # LiPo-Akkupack erzeugen.
        lipo = LiPoBatteryPack(
            capacity_nom_Ah=(
                self.battery_capacity_ah
            ),
            max_charge_current_a=(
                battery_max_charge_current_a
            ),
            internal_resistance_mOhm=80.0,
            initial_soc=self.initial_soc,
            Vmin=32.0,
            Vmax=42.0,
            parallel_cells=(
                battery_parallel_cells
            ),
            initial_temperature_c=(
                initial_temperature_c
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

        # NMC-Akkupack erzeugen.
        nmc = NMCBatteryPack(
            capacity_nom_Ah=(
                self.battery_capacity_ah
            ),
            max_charge_current_a=(
                battery_max_charge_current_a
            ),
            internal_resistance_mOhm=70.0,
            initial_soc=self.initial_soc,
            Vmin=32.0,
            Vmax=42.0,
            parallel_cells=(
                battery_parallel_cells
            ),
            initial_temperature_c=(
                initial_temperature_c
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

        # Modellannahmen für die Rekuperation:
        # 75 Prozent der mechanischen Bremsleistung können elektrisch genutzt werden.
        # Der Generator kann höchstens 500 W elektrische Leistung bereitstellen.
        regenerative_controller = (
            RegenerativeBrakingController(
                efficiency=0.75,
                max_electrical_power_w=500.0,
            )
        )

        # Gemeinsame Parameter der Bremswiderstände.
        brake_resistor_parameters = {
            "resistance_ohm": 4.0,
            "max_power_w": 500.0,
            "initial_temperature_c": (
                initial_temperature_c
            ),
            "thermal_capacity_j_per_k": (
                5_000.0
            ),
            "thermal_resistance_k_per_w": 1.0,
        }

        # LiPo und NMC sind zwei unabhängige Simulationsvarianten. 
        # Deshalb benötigt jede Variante einen eigenen Bremswiderstand mit eigenem Temperaturzustand.
        lipo_brake_resistor = BrakeResistor(
            **brake_resistor_parameters
        )

        nmc_brake_resistor = BrakeResistor(
            **brake_resistor_parameters
        )

        # Alle erzeugten Komponenten gemeinsam zurückgeben
        return {
            "lipo": lipo,
            "nmc": nmc,
            "regenerative_controller": (
                regenerative_controller
            ),
            "lipo_brake_resistor": (
                lipo_brake_resistor
            ),
            "nmc_brake_resistor": (
                nmc_brake_resistor
            ),
        }

    def run(self) -> dict:
        """Führt die Simulation aus."""

        logger.info(
            "E-Bike-Simulation wird ausgeführt"
        )

        # GPS-, Routen- und Umgebungsdaten vorbereiten.
        route_data = self._prepare_route_data()

        reader = route_data["reader"]

        time = route_data["time"]

        interval_time = route_data[
            "interval_time"
        ]

        valid_time_deltas = route_data[
            "time_deltas"
        ]

        distances = route_data["distances"]

        total_distance = route_data[
            "total_distance"
        ]

        elevations = route_data["elevations"]

        temperatures = route_data[
            "temperatures"
        ]

        interval_elevations = route_data[
            "interval_elevations"
        ]

        interval_temperatures = route_data[
            "interval_temperatures"
        ]

        air_densities = route_data[
            "air_densities"
        ]

        speeds = route_data["speeds"]

        accelerations = route_data[
            "accelerations"
        ]

        slopes = route_data["slopes"]

        slope_degrees = route_data[
            "slope_degrees"
        ]

        # Motorwerte aus den Routendaten berechnen.
        motor_data = self._calculate_motor_data(
            route_data
        )

  
        motor = motor_data["motor"]

        forces = motor_data["forces"]

        rolling_forces = motor_data[
            "rolling_forces"
        ]

        powers = motor_data["powers"]

        signed_powers = motor_data[
            "signed_powers"
        ]

        braking_powers = motor_data[
            "braking_powers"
        ]

        torques = motor_data["torques"]

        motor_currents = motor_data[
            "motor_currents"
        ]

        battery_currents = motor_data[
            "battery_currents"
        ]

        # Akkus und Rekuperationskomponenten

        # Der Akku stand vor der Fahrt lange genug in derselben Umgebung.
        #  Deshalb entspricht seine Anfangstemperatur dem ersten Temperaturwert der GPS-Datei.
        initial_battery_temperature_c = float(
            temperatures[0]
        )

        # Akkus, Rekuperationscontroller und Bremswiderstände erzeugen.
        components = (
            self._create_simulation_components(
                initial_temperature_c=(
                    initial_battery_temperature_c
                )
            )
        )


        lipo = components["lipo"]

        nmc = components["nmc"]

        regenerative_controller = components[
            "regenerative_controller"
        ]

        lipo_brake_resistor = components[
            "lipo_brake_resistor"
        ]

        nmc_brake_resistor = components[
            "nmc_brake_resistor"
        ]
        

        lipo_voltages = []
        nmc_voltages = []

        lipo_temperatures = []
        nmc_temperatures = []

        lipo_internal_resistances = []
        nmc_internal_resistances = []

        lipo_currents = []
        nmc_currents = []

        lipo_charge_powers = []
        nmc_charge_powers = []

        lipo_resistor_powers = []
        nmc_resistor_powers = []

        lipo_resistor_temperatures = []
        nmc_resistor_temperatures = []

        lipo_friction_brake_powers = []
        nmc_friction_brake_powers = []

        lipo_conversion_loss_powers = []
        nmc_conversion_loss_powers = []

        for (
            drive_current,
            braking_power,
            duration,
            ambient_temperature,
        ) in zip(
            battery_currents,
            braking_powers,
            valid_time_deltas,
            interval_temperatures,
        ):
            drive_current = float(drive_current)
            braking_power = float(braking_power)
            duration = float(duration)
            ambient_temperature = float(
                ambient_temperature
            )

            # Die Energieverteilung wird für beide Akkuvarianten getrennt berechnet, weil ihr SoC und ihre Spannung unterschiedlich sein können.
            lipo_braking_result = (
                regenerative_controller.distribute(
                    braking_power_w=braking_power,
                    duration=duration,
                    battery=lipo,
                    brake_resistor=(
                        lipo_brake_resistor
                    ),
                )
            )

            nmc_braking_result = (
                regenerative_controller.distribute(
                    braking_power_w=braking_power,
                    duration=duration,
                    battery=nmc,
                    brake_resistor=(
                        nmc_brake_resistor
                    ),
                )
            )

            if braking_power > 0:
                # Negative Ströme laden den Akku.
                lipo_current = lipo_braking_result[
                    "battery_current_a"
                ]

                nmc_current = nmc_braking_result[
                    "battery_current_a"
                ]

            else:
                # Im normalen Antriebsfall wird der positive Motorstrom verwendet.
                lipo_current = drive_current
                nmc_current = drive_current

            # Ladezustand aktualisieren.
            lipo.apply_current(
                current=lipo_current,
                duration=duration,
            )

            nmc.apply_current(
                current=nmc_current,
                duration=duration,
            )

            # Akkutemperatur aktualisieren.
            lipo.update_temperature(
                current=lipo_current,
                duration=duration,
                ambient_temperature_c=(
                    ambient_temperature
                ),
            )

            nmc.update_temperature(
                current=nmc_current,
                duration=duration,
                ambient_temperature_c=(
                    ambient_temperature
                ),
            )

            # Bremswiderstand erwärmen beziehungsweise  während inaktiver Abschnitte abkühlen.
            lipo_brake_resistor.update_temperature(
                power_w=lipo_braking_result[
                    "resistor_power_w"
                ],
                duration=duration,
                ambient_temperature_c=(
                    ambient_temperature
                ),
            )

            nmc_brake_resistor.update_temperature(
                power_w=nmc_braking_result[
                    "resistor_power_w"
                ],
                duration=duration,
                ambient_temperature_c=(
                    ambient_temperature
                ),
            )

            # Spannung am Ende des Zeitintervalls speichern.
            lipo_voltages.append(
                lipo.voltage(
                    current=lipo_current
                )
            )

            nmc_voltages.append(
                nmc.voltage(
                    current=nmc_current
                )
            )

            lipo_temperatures.append(
                lipo.temperature_c
            )

            nmc_temperatures.append(
                nmc.temperature_c
            )

            lipo_internal_resistances.append(
                lipo.effective_internal_resistance()
            )

            nmc_internal_resistances.append(
                nmc.effective_internal_resistance()
            )

            # Tatsächliche Akkuströme speichern.
            lipo_currents.append(
                lipo_current
            )

            nmc_currents.append(
                nmc_current
            )

            # Aufteilung der Bremsleistung speichern.
            lipo_charge_powers.append(
                lipo_braking_result[
                    "battery_charge_power_w"
                ]
            )

            nmc_charge_powers.append(
                nmc_braking_result[
                    "battery_charge_power_w"
                ]
            )

            lipo_resistor_powers.append(
                lipo_braking_result[
                    "resistor_power_w"
                ]
            )

            nmc_resistor_powers.append(
                nmc_braking_result[
                    "resistor_power_w"
                ]
            )

            lipo_resistor_temperatures.append(
                lipo_brake_resistor.temperature_c
            )

            nmc_resistor_temperatures.append(
                nmc_brake_resistor.temperature_c
            )

            lipo_friction_brake_powers.append(
                lipo_braking_result[
                    "friction_brake_power_w"
                ]
            )

            nmc_friction_brake_powers.append(
                nmc_braking_result[
                    "friction_brake_power_w"
                ]
            )

            lipo_conversion_loss_powers.append(
                lipo_braking_result[
                    "conversion_loss_power_w"
                ]
            )

            nmc_conversion_loss_powers.append(
                nmc_braking_result[
                    "conversion_loss_power_w"
                ]
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

        lipo_currents = np.asarray(
            lipo_currents,
            dtype=float,
        )

        nmc_currents = np.asarray(
            nmc_currents,
            dtype=float,
        )

        lipo_charge_powers = np.asarray(
            lipo_charge_powers,
            dtype=float,
        )

        nmc_charge_powers = np.asarray(
            nmc_charge_powers,
            dtype=float,
        )

        lipo_resistor_powers = np.asarray(
            lipo_resistor_powers,
            dtype=float,
        )

        nmc_resistor_powers = np.asarray(
            nmc_resistor_powers,
            dtype=float,
        )

        lipo_resistor_temperatures = np.asarray(
            lipo_resistor_temperatures,
            dtype=float,
        )

        nmc_resistor_temperatures = np.asarray(
            nmc_resistor_temperatures,
            dtype=float,
        )

        lipo_friction_brake_powers = np.asarray(
            lipo_friction_brake_powers,
            dtype=float,
        )

        nmc_friction_brake_powers = np.asarray(
            nmc_friction_brake_powers,
            dtype=float,
        )

        lipo_conversion_loss_powers = np.asarray(
            lipo_conversion_loss_powers,
            dtype=float,
        )

        nmc_conversion_loss_powers = np.asarray(
            nmc_conversion_loss_powers,
            dtype=float,
        )

        # Positive Akkuleistung:
        # Der Akku gibt Energie ab.
        # Negative Akkuleistung:
        # Der Akku wird durch Rekuperation geladen.
        lipo_powers = (
            lipo_voltages
            * lipo_currents
        )

        nmc_powers = (
            nmc_voltages
            * nmc_currents
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
        # Gesamte mechanische Bremsenergie, die durch das gemessene Fahrprofil angefordert wird.
        mechanical_braking_energy_wh = float(
            np.sum(
                braking_powers
                * valid_time_deltas
            )
            / 3600.0
        )

        # Elektrische Energie, die in den Akku geladen wird.
        lipo_recovered_energy_wh = float(
            np.sum(
                lipo_charge_powers
                * valid_time_deltas
            )
            / 3600.0
        )

        nmc_recovered_energy_wh = float(
            np.sum(
                nmc_charge_powers
                * valid_time_deltas
            )
            / 3600.0
        )

        # Energie, die im Bremswiderstand in Wärme umgewandelt wird.
        lipo_resistor_energy_wh = float(
            np.sum(
                lipo_resistor_powers
                * valid_time_deltas
            )
            / 3600.0
        )

        nmc_resistor_energy_wh = float(
            np.sum(
                nmc_resistor_powers
                * valid_time_deltas
            )
            / 3600.0
        )

        # Energie, die von der mechanischen Bremse aufgenommen werden muss.
        lipo_friction_brake_energy_wh = float(
            np.sum(
                lipo_friction_brake_powers
                * valid_time_deltas
            )
            / 3600.0
        )

        nmc_friction_brake_energy_wh = float(
            np.sum(
                nmc_friction_brake_powers
                * valid_time_deltas
            )
            / 3600.0
        )

        # Verluste bei der Umwandlung von mechanischer in elektrische Energie.
        lipo_conversion_loss_energy_wh = float(
            np.sum(
                lipo_conversion_loss_powers
                * valid_time_deltas
            )
            / 3600.0
        )

        nmc_conversion_loss_energy_wh = float(
            np.sum(
                nmc_conversion_loss_powers
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
            "mechanical_braking_energy_wh": (
                mechanical_braking_energy_wh
            ),
            "lipo_recovered_energy_wh": (
                lipo_recovered_energy_wh
            ),
            "nmc_recovered_energy_wh": (
                nmc_recovered_energy_wh
            ),
            "lipo_resistor_energy_wh": (
                lipo_resistor_energy_wh
            ),
            "nmc_resistor_energy_wh": (
                nmc_resistor_energy_wh
            ),
            "lipo_friction_brake_energy_wh": (
                lipo_friction_brake_energy_wh
            ),
            "nmc_friction_brake_energy_wh": (
                nmc_friction_brake_energy_wh
            ),
            "lipo_conversion_loss_energy_wh": (
                lipo_conversion_loss_energy_wh
            ),
            "nmc_conversion_loss_energy_wh": (
                nmc_conversion_loss_energy_wh
            ),
            "max_lipo_resistor_power_w": float(
                np.max(lipo_resistor_powers)
            ),
            "max_nmc_resistor_power_w": float(
                np.max(nmc_resistor_powers)
            ),
            "max_lipo_resistor_temperature_c": float(
                np.max(lipo_resistor_temperatures)
            ),
            "max_nmc_resistor_temperature_c": float(
                np.max(nmc_resistor_temperatures)
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
                "signed_power_w": signed_powers,
                "braking_power_w": braking_powers,
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
                "lipo_current_a": (
                    lipo_currents
                ),
                "nmc_current_a": (
                    nmc_currents
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
            "braking": {
                "lipo_charge_power_w": (
                    lipo_charge_powers
                ),
                "nmc_charge_power_w": (
                    nmc_charge_powers
                ),
                "lipo_resistor_power_w": (
                    lipo_resistor_powers
                ),
                "nmc_resistor_power_w": (
                    nmc_resistor_powers
                ),
                "lipo_resistor_temperature_c": (
                    lipo_resistor_temperatures
                ),
                "nmc_resistor_temperature_c": (
                    nmc_resistor_temperatures
                ),
                "lipo_friction_brake_power_w": (
                    lipo_friction_brake_powers
                ),
                "nmc_friction_brake_power_w": (
                    nmc_friction_brake_powers
                ),
                "lipo_conversion_loss_power_w": (
                    lipo_conversion_loss_powers
                ),
                "nmc_conversion_loss_power_w": (
                    nmc_conversion_loss_powers
                ),
            },
        }