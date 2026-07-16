import math

from src.battery_pack import BatteryPack
from src.brake_resistor import BrakeResistor

class RegenerativeBrakingController:
    """
    Verteilt später die Bremsleistung auf Akku,
    Bremswiderstand und mechanische Bremse.
    """

    def __init__(
        self,
        efficiency: float,
        max_electrical_power_w: float,
    ) -> None:
        if not 0 < efficiency <= 1:
            raise ValueError(
                "Der Rekuperationswirkungsgrad muss "
                "zwischen 0 und 1 liegen."
            )

        if max_electrical_power_w <= 0:
            raise ValueError(
                "Die maximale Rekuperationsleistung "
                "muss größer als 0 sein."
            )

        self.efficiency = efficiency
        self.max_electrical_power_w = (
            max_electrical_power_w
        )

    @staticmethod
    def calculate_charge_current(
        battery: BatteryPack,
        requested_power_w: float,
    ) -> float:
        """
        Berechnet aus der gewünschten Ladeleistung
        den dazugehörigen Ladestrom als positiven Betrag.
        """

        if requested_power_w <= 0:
            return 0.0

        open_circuit_voltage = battery.voltage(
            current=0.0
        )

        internal_resistance = (
            battery.effective_internal_resistance()
        )

        discriminant = (
            open_circuit_voltage**2
            + 4.0
            * internal_resistance
            * requested_power_w
        )

        charge_current_a = (
            -open_circuit_voltage
            + math.sqrt(discriminant)
        ) / (
            2.0 * internal_resistance
        )

        return charge_current_a
    
    def distribute(
        self,
        braking_power_w: float,
        duration: float,
        battery: BatteryPack,
        brake_resistor: BrakeResistor,
    ) -> dict[str, float]:
        """
        Verteilt die Bremsleistung auf Akku,
        Bremswiderstand und mechanische Bremse.
        """

        if braking_power_w < 0:
            raise ValueError(
                "Der Bremsleistungsbetrag darf "
                "nicht negativ sein."
            )

        if duration < 0:
            raise ValueError(
                "Die Zeitdauer darf nicht negativ sein."
            )

        if braking_power_w == 0 or duration == 0:
            return {
                "electrical_potential_w": 0.0,
                "battery_current_a": 0.0,
                "battery_charge_power_w": 0.0,
                "resistor_power_w": 0.0,
                "conversion_loss_power_w": 0.0,
                "friction_brake_power_w": 0.0,
            }

        # Der Wirkungsgrad und die maximale Generatorleistung begrenzen die elektrisch verfügbare Rekuperationsleistung.
        electrical_potential_w = min(
            braking_power_w * self.efficiency,
            self.max_electrical_power_w,
        )

        # Zunächst wird versucht, die gesamte verfügbare elektrische Leistung in den Akku zu laden.
        requested_charge_current_a = (
            self.calculate_charge_current(
                battery=battery,
                requested_power_w=(
                    electrical_potential_w
                ),
            )
        )

        # Der Akku begrenzt den Strom anhand von Ladestrom, Spannung, SoC und Zeitschrittdauer.
        allowed_charge_current_a = (
            battery.maximum_charge_current(
                duration=duration
            )
        )

        charge_current_a = min(
            requested_charge_current_a,
            allowed_charge_current_a,
        )

        # Der Akku verwendet negative Ströme zum Laden.
        battery_terminal_voltage_v = (
            battery.voltage(
                current=-charge_current_a
            )
        )

        # Die Ladeleistung wird als positiver Betrag gespeichert.
        battery_charge_power_w = (
            battery_terminal_voltage_v
            * charge_current_a
        )

        # Leistung, die der Akku nicht aufnehmen konnte.
        remaining_electrical_power_w = max(
            electrical_potential_w
            - battery_charge_power_w,
            0.0,
        )

        # Der verbleibende Anteil wird dem
        # Bremswiderstand angeboten.
        resistor_power_limit_w = (
            brake_resistor.maximum_power(
                dc_voltage_v=(
                    battery_terminal_voltage_v
                )
            )
        )

        resistor_power_w = min(
            remaining_electrical_power_w,
            resistor_power_limit_w,
        )

        accepted_electrical_power_w = (
            battery_charge_power_w
            + resistor_power_w
        )

        # Rückrechnung auf die mechanische Motorseite.
        regenerative_mechanical_power_w = (
            accepted_electrical_power_w
            / self.efficiency
        )

        conversion_loss_power_w = max(
            regenerative_mechanical_power_w
            - accepted_electrical_power_w,
            0.0,
        )

        # Alles, was elektrisch nicht verarbeitet werden kann, übernimmt die mechanische Bremse.
        friction_brake_power_w = max(
            braking_power_w
            - regenerative_mechanical_power_w,
            0.0,
        )

        return {
            "electrical_potential_w": (
                electrical_potential_w
            ),

            # Negatives Vorzeichen, weil der Akku geladen wird.
            "battery_current_a": (
                -charge_current_a
            ),

            "battery_charge_power_w": (
                battery_charge_power_w
            ),
            "resistor_power_w": resistor_power_w,
            "conversion_loss_power_w": (
                conversion_loss_power_w
            ),
            "friction_brake_power_w": (
                friction_brake_power_w
            ),
        }