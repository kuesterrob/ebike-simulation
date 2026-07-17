import unittest

from src.battery_pack import BatteryPack


class TestBatteryPack(unittest.TestCase):
    """
    Testet den Ladezustand und die Ladegrenzen
    des Akkumodells.
    """

    def create_battery(
        self,
        initial_soc=0.5,
    ):
        """
        Erzeugt einen Akku mit einfachen Testwerten.

        Die Hilfsmethode ermöglicht es, für einzelne
        Tests Akkus mit unterschiedlichen Ladezuständen
        zu erzeugen.
        """
        return BatteryPack(
            # Nennkapazität des Akkus:
            # 10 Ah entsprechen 36 000 As.
            capacity_nom_Ah=10.0,

            # Der Akku darf mit höchstens 5 A
            # geladen werden.
            max_charge_current_a=5.0,

            # 100 Milliohm entsprechen 0,1 Ohm.
            internal_resistance_mOhm=100.0,

            initial_soc=initial_soc,
            Vmin=30.0,
            Vmax=40.0,
            parallel_cells=1,

            # Der Temperaturkoeffizient wird für diese Tests deaktiviert. Dadurch bleibt der Innenwiderstand konstant und die Ergebnisselassen sich leichter berechnen.
            resistance_temperature_coefficient_per_k=0.0,
        )

    def setUp(self):
        """
        Wird vor jeder Testmethode ausgeführt.
        Jeder Test erhält dadurch einen neuen Akku
        mit einem Ladezustand von 50 Prozent.
        """
        self.battery = self.create_battery(
            initial_soc=0.5,
        )

    def test_discharge_reduces_state_of_charge(self):
        """
        Prüft, ob ein positiver Strom den Akku entlädt
        und der SoC nicht unter null sinken kann.
        """

        self.battery.apply_current(
            current=10.0,
            duration=360.0,
        )

        # Der Ladezustand muss 40 Prozent betragen.
        self.assertAlmostEqual(
            self.battery.soc,
            0.4,
        )

        # Der Akku ist noch nicht leer.
        self.assertFalse(
            self.battery.is_empty()
        )

        #  Das Akkumodell muss den Wert aber auf null begrenzen.
        self.battery.apply_current(
            current=10.0,
            duration=3600.0,
        )

        self.assertAlmostEqual(
            self.battery.soc,
            0.0,
        )

        self.assertTrue(
            self.battery.is_empty()
        )

    def test_charging_increases_state_of_charge(self):
        """
        Prüft, ob ein negativer Strom den Akku lädt.
        """

        self.battery.apply_current(
            current=-5.0,
            duration=360.0,
        )

        self.assertAlmostEqual(
            self.battery.soc,
            0.55,
        )

        self.assertFalse(
            self.battery.is_full()
        )

    def test_maximum_charge_current_respects_limits(self):
        """
        Prüft die verschiedenen Begrenzungen
        des maximalen Ladestroms.
        """

        maximum_current = (
            self.battery.maximum_charge_current(
                duration=360.0,
            )
        )

        self.assertAlmostEqual(
            maximum_current,
            5.0,
        )

        # Ein vollständig geladener Akku darf keinen weiteren Ladestrom aufnehmen.
        full_battery = self.create_battery(
            initial_soc=1.0,
        )

        maximum_current_full = (
            full_battery.maximum_charge_current(
                duration=360.0,
            )
        )

        self.assertAlmostEqual(
            maximum_current_full,
            0.0,
        )

        # Akku bereits 99 Prozent geladen darf noch 0,1 A aufnehmen, damit der SoC nicht über 100 Prozent steigt.
        almost_full_battery = self.create_battery(
            initial_soc=0.99,
        )

        maximum_current_almost_full = (
            almost_full_battery.maximum_charge_current(
                duration=3600.0,
            )
        )

        self.assertAlmostEqual(
            maximum_current_almost_full,
            0.1,
        )

    def test_battery_rejects_invalid_charging(self):
        """
        Prüft die Fehlerbehandlung bei unzulässigem
        Ladestrom und negativer Zeitdauer.
        """

        # Ladestrom von 6 A muss abgelehnt werden 
       
        with self.subTest(
            case="charge current exceeds limit"
        ):
            with self.assertRaisesRegex(
                ValueError,
                "aktuell erlaubte",
            ):
                self.battery.apply_current(
                    current=-6.0,
                    duration=360.0,
                )

        # negative Zeitdauer ist physikalisch nicht sinnvoll -> ValueError
        with self.subTest(
            case="negative duration"
        ):
            with self.assertRaisesRegex(
                ValueError,
                "nicht negativ",
            ):
                self.battery.apply_current(
                    current=1.0,
                    duration=-1.0,
                )