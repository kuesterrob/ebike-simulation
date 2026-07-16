import logging

from src.battery_base import BatteryBase


class BatteryPack(BatteryBase):
    """Gemeinsames elektrisches und thermisches Akkumodell."""

    def __init__(
        self,
        capacity_nom_Ah: float,
        internal_resistance_mOhm: float = 80.0,
        initial_soc: float = 1.0,
        Vmin: float = 3.0,
        Vmax: float = 4.2,
        parallel_cells: int = 1,
        initial_temperature_c: float = 25.0,
        thermal_capacity_j_per_k: float = 10_000.0,
        thermal_resistance_k_per_w: float = 2.0,
        resistance_temperature_coefficient_per_k: float = 0.01,
        reference_temperature_c: float = 25.0,
    ) -> None:
        if capacity_nom_Ah <= 0:
            raise ValueError(
                "Die Akkukapazität muss größer als 0 sein."
            )

        if not 0 < initial_soc <= 1:
            raise ValueError(
                "Der Ladezustand muss zwischen 0 und 1 liegen."
            )

        if internal_resistance_mOhm <= 0:
            raise ValueError(
                "Der Innenwiderstand muss größer als 0 sein."
            )

        if Vmin >= Vmax:
            raise ValueError(
                "Die Minimalspannung muss kleiner als "
                "die Maximalspannung sein."
            )

        if parallel_cells < 1:
            raise ValueError(
                "Die Anzahl paralleler Zellen muss "
                "mindestens 1 sein."
            )

        if initial_temperature_c <= -273.15:
            raise ValueError(
                "Die Anfangstemperatur muss über "
                "-273,15 °C liegen."
            )

        if thermal_capacity_j_per_k <= 0:
            raise ValueError(
                "Die thermische Kapazität muss "
                "größer als 0 sein."
            )

        if thermal_resistance_k_per_w <= 0:
            raise ValueError(
                "Der thermische Widerstand muss "
                "größer als 0 sein."
            )

        if resistance_temperature_coefficient_per_k < 0:
            raise ValueError(
                "Der Temperaturkoeffizient darf "
                "nicht negativ sein."
            )

        # Umrechnung der Kapazität:
        # 1 Ah = 3600 As
        self.C_nom = capacity_nom_Ah * 3600.0

        self.soc = initial_soc
        self.Vmin = Vmin
        self.Vmax = Vmax
        self.parallel_cells = parallel_cells

        # Formel für parallele Zellstränge:
        #
        # R_Pack = R_Serienstrang / Anzahl_Parallelstränge
        #
        # Der Widerstand wird zusätzlich von Milliohm in Ohm umgerechnet.
        self.R_int_reference = (
            internal_resistance_mOhm
            * 1e-3
            / parallel_cells
        )

        # Das vereinfachte Modell nimmt eine einheitliche mittlere Temperatur für den gesamten Akkupack an.
        self.temperature_c = initial_temperature_c

        # Der angegebene Innenwiderstand gilt bei dieser Referenztemperatur.
        self.reference_temperature_c = (
            reference_temperature_c
        )

        # C_thermisch gibt an, wie viel Energie benötigt wird, um den Akku um 1 K beziehungsweise 1 °C zu erwärmen.
        self.thermal_capacity_j_per_k = (
            thermal_capacity_j_per_k
        )

        # R_thermisch beschreibt den Wärmeübergang vom Akku an die Umgebung.
        self.thermal_resistance_k_per_w = (
            thermal_resistance_k_per_w
        )

        # Modellannahme mangels gemessener Kennlinie:
        # Änderung des Innenwiderstands um 1 % pro Kelvin.
        self.resistance_temperature_coefficient_per_k = (
            resistance_temperature_coefficient_per_k
        )

    def effective_internal_resistance(self) -> float:
        """
        Berechnet den Innenwiderstand bei der
        aktuellen Akkutemperatur.
        """

        # Temperaturdifferenz: delta_T = T_referenz - T_akku
        # Ist der Akku kälter als die Referenz, ist die Differenz positiv.
        temperature_difference = (
            self.reference_temperature_c
            - self.temperature_c
        )

        # Vereinfachte Widerstandskennlinie:
        # R(T) = R_ref * (1 + alpha * (T_ref - T))
        # Bei niedriger Temperatur steigt dadurch der Innenwiderstand.
        resistance_factor = (
            1.0
            + (
                self.resistance_temperature_coefficient_per_k
                * temperature_difference
            )
        )

        # Die Begrenzung verhindert negative oder extrem große Widerstände außerhalb des Modellbereichs.
        resistance_factor = max(
            0.5,
            min(resistance_factor, 3.0),
        )

        return (
            self.R_int_reference
            * resistance_factor
        )

    def update_temperature(
        self,
        current: float,
        duration: float,
        ambient_temperature_c: float,
    ) -> None:
        """
        Aktualisiert die mittlere Akkutemperatur für
        einen Simulationsabschnitt.
        """

        if duration < 0:
            raise ValueError(
                "Die Zeitdauer darf nicht negativ sein."
            )

        if ambient_temperature_c <= -273.15:
            raise ValueError(
                "Die Umgebungstemperatur muss über "
                "-273,15 °C liegen."
            )

        internal_resistance = (
            self.effective_internal_resistance()
        )

        # Vereinfachte Wärmebilanz
        #
        # Elektrische Wärmeleistung:
        # P_Wärme = I² * R(T)
        # Die Verlustleistung am Innenwiderstand wird innerhalb des Akkus in Wärme umgewandelt.
        generated_heat_w = (
            current**2
            * internal_resistance
        )

        # Wärmeabgabe an die Umgebung:
        # P_Abgabe = (T_Akku - T_Umgebung) / R_thermisch
        # Positiver Wert:
        # Der Akku gibt Wärme ab.
        # Negativer Wert:
        # Der Akku nimmt Wärme aus der Umgebung auf.
        dissipated_heat_w = (
            self.temperature_c
            - ambient_temperature_c
        ) / self.thermal_resistance_k_per_w

        # Netto-Wärmeleistung:
        # P_netto = P_Wärme - P_Abgabe
        net_heat_w = (
            generated_heat_w
            - dissipated_heat_w
        )

        # Wärmemenge im Zeitintervall:
        # Q = P_netto * delta_t
        heat_energy_j = (
            net_heat_w
            * duration
        )

        # Temperaturänderung:
        # delta_T = Q / C_thermisch
        temperature_change_c = (
            heat_energy_j
            / self.thermal_capacity_j_per_k
        )

        # Temperatur für den nächsten Simulationsschritt:
        # T_neu = T_alt + delta_T
        self.temperature_c += temperature_change_c

    def apply_current(
        self,
        current: float,
        duration: float,
    ) -> None:
        """Aktualisiert den Ladezustand des Akkus."""

        if current > 0:
            internal_resistance = (
                self.effective_internal_resistance()
            )

            if current > (
                self.voltage(current=current)
                / internal_resistance
            ):
                raise ValueError(
                    "Der Strom ist größer als der maximal "
                    "lieferbare Akkustrom."
                )

            # Änderung des Ladezustands:
            # delta_SoC = -(I * delta_t) / C_nominal
            dsoc = (
                -(current * duration)
                / self.C_nom
            )

            self.soc = max(
                0.0,
                min(self.soc + dsoc, 1.0),
            )

            if self.soc <= 0.0:
                logging.warning(
                    "Der Akku ist leer."
                )

        elif current < 0:
            raise ValueError(
                f"Der Strom darf nicht negativ sein: "
                f"{current:.2f} A"
            )

    def voltage(
        self,
        current: float = 0.0,
    ) -> float:
        """Berechnet die Akkuspannung unter Last."""

        open_circuit_voltage = (
            self.Vmin
            + self.soc
            * (self.Vmax - self.Vmin)
        )

        internal_resistance = (
            self.effective_internal_resistance()
        )

        # Spannung unter Last:
        # U_Last = U_OCV - I * R(T)
        return (
            open_circuit_voltage
            - internal_resistance * current
        )

    def is_empty(self) -> bool:
        return self.soc <= 0.0 + 1e-9

    def is_full(self) -> bool:
        return self.soc >= 1.0 - 1e-9

    def __str__(self) -> str:
        return (
            f"BatteryPack("
            f"SoC={self.soc * 100:.1f} %, "
            f"V={self.voltage():.2f} V, "
            f"T={self.temperature_c:.1f} °C)"
        )