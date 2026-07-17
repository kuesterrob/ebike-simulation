import unittest

import numpy as np

from src.motor import Motor


class TestMotor(unittest.TestCase):
    """
    Testet, ob der Motor korrekt zwischen
    Antrieb und Bremsen unterscheidet.
    """

    def setUp(self):
        """
        Wird vor jeder Testmethode ausgeführt.

        Für den Test werden Luft- und Rollwiderstand
        deaktiviert. Dadurch hängt das Ergebnis nur von
        der Beschleunigung ab und kann einfach berechnet
        und überprüft werden.
        """
        self.motor = Motor(
            total_mass_kg=100.0,
            drag_area_m2=0.0,
            wheel_diameter_inch=20.0,
            motor_constant_nm_per_a=2.0,
            rolling_resistance_coefficient=0.0,
        )

    def test_motor_calculates_drive_power(self):
        """
        Prüft den normalen Antriebsfall.
        """

      
        speeds = np.array([5.0])
        accelerations = np.array([1.0])
        slopes = np.array([0.0])
        air_densities = np.array([1.2])

    
        results = self.motor.calculate(
            speeds=speeds,
            accelerations=accelerations,
            slopes=slopes,
            air_density_kg_per_m3=air_densities,
        )

    
        self.assertAlmostEqual(
            results["force_n"][0],
            100.0,
        )

       
        self.assertAlmostEqual(
            results["signed_power_w"][0],
            500.0,
        )

        # Im Antriebsfall muss die Antriebsleistung positiv sein.
        self.assertAlmostEqual(
            results["power_w"][0],
            500.0,
        )

        # Gleichzeitig darf keine Bremsleistung vorliegen.
        self.assertAlmostEqual(
            results["braking_power_w"][0],
            0.0,
        )

        # Im Antriebsfall müssen Drehmoment und Strom ebenfalls positiv sein.
        self.assertGreater(
            results["torque_nm"][0],
            0.0,
        )

        self.assertGreater(
            results["current_a"][0],
            0.0,
        )

        # Es darf kein Bremsdrehmoment vorhanden sein.
        self.assertAlmostEqual(
            results["braking_torque_nm"][0],
            0.0,
        )

    def test_motor_calculates_braking_power(self):
        """
        Prüft den Bremsfall.
        """

        speeds = np.array([5.0])
        accelerations = np.array([-1.0])
        slopes = np.array([0.0])
        air_densities = np.array([1.2])

        results = self.motor.calculate(
            speeds=speeds,
            accelerations=accelerations,
            slopes=slopes,
            air_density_kg_per_m3=air_densities,
        )

    
        self.assertAlmostEqual(
            results["force_n"][0],
            -100.0,
        )

    
        self.assertAlmostEqual(
            results["signed_power_w"][0],
            -500.0,
        )

        # Im Bremsfall darf keine positive Antriebsleistung vorliegen.
        self.assertAlmostEqual(
            results["power_w"][0],
            0.0,
        )

        # Die Bremsleistung wird als positiver Betrag gespeichert.
        self.assertAlmostEqual(
            results["braking_power_w"][0],
            500.0,
        )

        # Das vorzeichenbehaftete Drehmoment muss im Bremsfall negativ sein.
        self.assertLess(
            results["signed_torque_nm"][0],
            0.0,
        )

        # Das normale Antriebsdrehmoment ist null.
        self.assertAlmostEqual(
            results["torque_nm"][0],
            0.0,
        )

        # Das Bremsdrehmoment wird als positiver Betrag zurückgegeben.
        self.assertGreater(
            results["braking_torque_nm"][0],
            0.0,
        )

        # Der Motorstrom beschreibt nur den Antriebsfall deshalb muss er während des Bremsens null sein.
        self.assertAlmostEqual(
            results["current_a"][0],
            0.0,
        )

    def test_motor_rejects_invalid_input(self):
        """
        Prüft, ob ungültige Eingangsdaten einen
        ValueError mit passender Fehlermeldung auslösen.
        """

        test_cases = [
            (
                "unterschiedliche Anzahl von Werten",
                np.array([5.0, 6.0]),
                np.array([1.0]),
                np.array([0.0]),
                np.array([1.2]),
                "gleich viele Werte",
            ),
            (
                "leere Eingangsdaten",
                np.array([]),
                np.array([]),
                np.array([]),
                np.array([]),
                "nicht leer",
            ),
            (
                "ungültige Luftdichte",
                np.array([5.0]),
                np.array([1.0]),
                np.array([0.0]),
                np.array([0.0]),
                "größer als 0",
            ),
        ]

        for (
            description,
            speeds,
            accelerations,
            slopes,
            air_densities,
            expected_message,
        ) in test_cases:

            
            with self.subTest(case=description):

                with self.assertRaisesRegex(
                    ValueError,
                    expected_message,
                ):
                    self.motor.calculate(
                        speeds=speeds,
                        accelerations=accelerations,
                        slopes=slopes,
                        air_density_kg_per_m3=air_densities,
                    )