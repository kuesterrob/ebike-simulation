import unittest

from src.battery_pack import BatteryPack
from src.brake_resistor import BrakeResistor
from src.regenerative_braking import (
    RegenerativeBrakingController,
)


class TestRegenerativeBrakingController(
    unittest.TestCase
):
    """
    Testet die Verteilung der Bremsleistung auf
    Akku, Bremswiderstand und mechanische Bremse.
    """

    def create_battery(
        self,
        initial_soc=0.5,
    ):
        """
        Erstellt einen Akku für die Tests.
        """
        return BatteryPack(
            capacity_nom_Ah=10.0,
            max_charge_current_a=100.0,
            internal_resistance_mOhm=100.0,
            initial_soc=initial_soc,
            Vmin=30.0,
            Vmax=40.0,
            parallel_cells=1,

            # Der Innenwiderstand soll während der Tests konstant bleiben.
            resistance_temperature_coefficient_per_k=0.0,
        )

    def create_brake_resistor(self):
        """
        Erstellt einen Bremswiderstand.

        Der Widerstand darf maximal 200 W aufnehmen.
        Damit kann im Test überprüft werden, ob die
        übrige Leistung an die mechanische Bremse geht.
        """
        return BrakeResistor(
            resistance_ohm=4.0,
            max_power_w=200.0,
            initial_temperature_c=25.0,
            thermal_capacity_j_per_k=5000.0,
            thermal_resistance_k_per_w=1.0,
        )

    def setUp(self):

        self.controller = (
            RegenerativeBrakingController(
                efficiency=0.75,
                max_electrical_power_w=500.0,
            )
        )

        self.battery = self.create_battery(
            initial_soc=0.5,
        )

        self.brake_resistor = (
            self.create_brake_resistor()
        )

    def assert_power_balance(
        self,
        braking_power_w,
        result,
    ):
        """
        Hilfsmethode zur Prüfung der Leistungsbilanz.

        Die ursprüngliche mechanische Bremsleistung
        muss vollständig aufgeteilt werden auf:

        - Akkuladeleistung
        - Bremswiderstandsleistung
        - Umwandlungsverluste
        - mechanische Bremsleistung
        """

        distributed_power_w = (
            result["battery_charge_power_w"]
            + result["resistor_power_w"]
            + result["conversion_loss_power_w"]
            + result["friction_brake_power_w"]
        )

        self.assertAlmostEqual(
            distributed_power_w,
            braking_power_w,
            places=6,
        )

    def test_battery_accepts_available_regenerative_power(
        self,
    ):
        """
        Prüft die Rekuperation, wenn der Akku die
        gesamte elektrische Leistung aufnehmen kann.
        """

        braking_power_w = 400.0

        #  Bremsleistung verteilen.
        result = self.controller.distribute(
            braking_power_w=braking_power_w,
            duration=10.0,
            battery=self.battery,
            brake_resistor=self.brake_resistor,
        )

        # Der Generator stellt 300 W elektrische Leistung bereit.
        self.assertAlmostEqual(
            result["electrical_potential_w"],
            300.0,
            places=6,
        )

        # Der Akku kann die vollständigen 300 W aufnehmen.
        self.assertAlmostEqual(
            result["battery_charge_power_w"],
            300.0,
            places=6,
        )

        # Ein negativer Akkustrom bedeutet, dass der Akku geladen wird.
        self.assertLess(
            result["battery_current_a"],
            0.0,
        )

        # Es bleibt keine Leistung für den Bremswiderstand übrig.
        self.assertAlmostEqual(
            result["resistor_power_w"],
            0.0,
            places=6,
        )

        #  gesamte Bremsleistung rekuperiert -> mechanische Bremse muss keine Leistung aufnehmen.
        self.assertAlmostEqual(
            result["friction_brake_power_w"],
            0.0,
            places=6,
        )

      
        self.assertAlmostEqual(
            result["conversion_loss_power_w"],
            100.0,
            places=6,
        )

        # Prüft, ob keine Leistung verloren gegangen ist.
        self.assert_power_balance(
            braking_power_w,
            result,
        )

    def test_full_battery_uses_resistor_and_friction_brake(
        self,
    ):
        """
        Prüft die Leistungsverteilung bei einem
        vollständig geladenen Akku.
        """

        # Ein voller Akku darf keine weitere Energie aufnehmen.
        full_battery = self.create_battery(
            initial_soc=1.0,
        )

      
        braking_power_w = 1000.0

        result = self.controller.distribute(
            braking_power_w=braking_power_w,
            duration=10.0,
            battery=full_battery,
            brake_resistor=self.brake_resistor,
        )


        self.assertAlmostEqual(
            result["electrical_potential_w"],
            500.0,
            places=6,
        )

        # Der volle Akku darf keinen Ladestrom und keine Ladeleistung erhalten.
        self.assertAlmostEqual(
            result["battery_current_a"],
            0.0,
            places=6,
        )

        self.assertAlmostEqual(
            result["battery_charge_power_w"],
            0.0,
            places=6,
        )

        # Der Bremswiderstand ist auf 200 W begrenzt.
        self.assertAlmostEqual(
            result["resistor_power_w"],
            200.0,
            places=6,
        )

        # Da weder Akku noch Widerstand die gesamte
        # Bremsleistung aufnehmen können, muss die
        # mechanische Bremse ebenfalls eingesetzt werden.
        self.assertGreater(
            result["friction_brake_power_w"],
            0.0,
        )

        # 
        # Leistungsbilanz muss stimmen.
        self.assert_power_balance(
            braking_power_w,
            result,
        )

    def test_zero_power_or_duration_returns_zero(
        self,
    ):
        """
        Prüft die Grenzfälle ohne Bremsleistung
        """

        test_cases = [
            (
                "no braking power",
                0.0,
                10.0,
            ),
            (
                "no time progress",
                400.0,
                0.0,
            ),
        ]

        for (
            description,
            braking_power_w,
            duration,
        ) in test_cases:

            with self.subTest(case=description):
                result = self.controller.distribute(
                    braking_power_w=braking_power_w,
                    duration=duration,
                    battery=self.battery,
                    brake_resistor=(
                        self.brake_resistor
                    ),
                )

                # Bei 0 W Bremsleistung oder 0 Sekunden
                # müssen sämtliche Ausgabewerte null sein.
                self.assertTrue(
                    all(
                        value == 0.0
                        for value in result.values()
                    )
                )

    def test_rejects_invalid_input(self):
        """
        Prüft die Fehlerbehandlung für negative
        Bremsleistung und negative Zeitdauer.
        """

        with self.subTest(
            case="negative braking power"
        ):
            with self.assertRaisesRegex(
                ValueError,
                "nicht negativ",
            ):
                self.controller.distribute(
                    braking_power_w=-100.0,
                    duration=10.0,
                    battery=self.battery,
                    brake_resistor=(
                        self.brake_resistor
                    ),
                )

        with self.subTest(
            case="negative duration"
        ):
            with self.assertRaisesRegex(
                ValueError,
                "nicht negativ",
            ):
                self.controller.distribute(
                    braking_power_w=100.0,
                    duration=-1.0,
                    battery=self.battery,
                    brake_resistor=(
                        self.brake_resistor
                    ),
                )