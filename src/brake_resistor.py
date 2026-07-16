class BrakeResistor:
    """
    Vereinfachtes elektrisches und thermisches
    Modell eines Bremswiderstands.
    """

    def __init__(
        self,
        resistance_ohm: float,
        max_power_w: float,
        initial_temperature_c: float,
        thermal_capacity_j_per_k: float,
        thermal_resistance_k_per_w: float,
    ) -> None:
        if resistance_ohm <= 0:
            raise ValueError(
                "Der Bremswiderstand muss größer "
                "als 0 Ohm sein."
            )

        if max_power_w <= 0:
            raise ValueError(
                "Die maximale Leistung muss "
                "größer als 0 sein."
            )

        if initial_temperature_c <= -273.15:
            raise ValueError(
                "Die Anfangstemperatur ist ungültig."
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

        self.resistance_ohm = resistance_ohm
        self.max_power_w = max_power_w
        self.temperature_c = initial_temperature_c
        self.thermal_capacity_j_per_k = (
            thermal_capacity_j_per_k
        )
        self.thermal_resistance_k_per_w = (
            thermal_resistance_k_per_w
        )

        # Bisher insgesamt in Wärme umgewandelte elektrische Energie.
        self.dissipated_energy_j = 0.0

    def maximum_power(
        self,
        dc_voltage_v: float,
    ) -> float:
        """
        Berechnet die bei der aktuellen Spannung
        maximal mögliche Widerstandsleistung.
        """

        if dc_voltage_v < 0:
            raise ValueError(
                "Die Spannung darf nicht negativ sein."
            )

        # Elektrische Widerstandsleistung:
        # P = U² / R
        electrical_power_limit_w = (
            dc_voltage_v**2
            / self.resistance_ohm
        )

        # Neben der elektrischen Grenze wird auch die Nennleistung des Widerstands beachtet.
        return min(
            electrical_power_limit_w,
            self.max_power_w,
        )

    def update_temperature(
        self,
        power_w: float,
        duration: float,
        ambient_temperature_c: float,
    ) -> None:
        """
        Aktualisiert Temperatur und insgesamt
        dissipierte Energie.
        """

        if power_w < 0:
            raise ValueError(
                "Die Widerstandsleistung darf "
                "nicht negativ sein."
            )

        if power_w > self.max_power_w + 1e-9:
            raise ValueError(
                "Die maximale Widerstandsleistung "
                "wurde überschritten."
            )

        if duration < 0:
            raise ValueError(
                "Die Zeitdauer darf nicht negativ sein."
            )

        if ambient_temperature_c <= -273.15:
            raise ValueError(
                "Die Umgebungstemperatur ist ungültig."
            )

        # Wärmeabgabe an die Umgebung:
        # P_Kühlung = (T_Widerstand - T_Umgebung)         / R_thermisch
        cooling_power_w = (
            self.temperature_c
            - ambient_temperature_c
        ) / self.thermal_resistance_k_per_w

        # Netto-Wärmeleistung:
        # P_netto = P_elektrisch - P_Kühlung
        net_heat_power_w = (
            power_w
            - cooling_power_w
        )

        temperature_change_c = (
            net_heat_power_w
            * duration
            / self.thermal_capacity_j_per_k
        )

        self.temperature_c += temperature_change_c

        # Elektrische Energie:
        # E = P * delta_t
        self.dissipated_energy_j += (
            power_w
            * duration
        )

    @property
    def dissipated_energy_wh(self) -> float:
        """Gibt die dissipierte Energie in Wh zurück."""

        return (
            self.dissipated_energy_j
            / 3600.0
        )