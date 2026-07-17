import unittest

import numpy as np

from src.air_density import calculate_air_density


class TestAirDensity(unittest.TestCase):
    """
    Testet die Berechnung der Luftdichte
    aus Temperatur und Höhe.
    """

    def test_air_density_at_standard_conditions(self):
        """
        Prüft die Luftdichte bei den Bedingungen
        der Standardatmosphäre.

        Bei 15 °C und auf Meereshöhe beträgt die
        Luftdichte ungefähr 1,225 kg/m³.
        """

    
        temperatures_c = np.array([15.0])
        altitudes_m = np.array([0.0])

        expected_air_density = 1.225

   
        calculated_air_densities = (
            calculate_air_density(
                temperatures_c=temperatures_c,
                altitudes_m=altitudes_m,
            )
        )

     
        calculated_air_density = (
            calculated_air_densities[0]
        )

        # Abweichung von höchstens 0,001 kg/m³ erlaubt.
        self.assertAlmostEqual(
            calculated_air_density,
            expected_air_density,
            delta=0.001,
        )

    def test_air_density_decreases_with_altitude_and_temperature(
        self,
    ):
        """
        Prüft grundlegende Eigenschaften:
        - Mit zunehmender Höhe sinkt die Luftdichte.
        - Mit zunehmender Temperatur sinkt die Luftdichte.
        """

        with self.subTest(
            case="air density decreases with altitude"
        ):

            air_densities = calculate_air_density(
                temperatures_c=np.array(
                    [15.0, 15.0]
                ),
                altitudes_m=np.array(
                    [0.0, 1000.0]
                ),
            )

            # Die Luftdichte auf Meereshöhe muss größer als in 1000 Metern Höhe sein.
            self.assertGreater(
                air_densities[0],
                air_densities[1],
            )

        with self.subTest(
            case="air density decreases with temperature"
        ):
      
            air_densities = calculate_air_density(
                temperatures_c=np.array(
                    [0.0, 30.0]
                ),
                altitudes_m=np.array(
                    [0.0, 0.0]
                ),
            )

            # Kalte Luft muss dichter als warme Luft sein.
            self.assertGreater(
                air_densities[0],
                air_densities[1],
            )

    def test_air_density_rejects_invalid_input(self):
        """
        Prüft die Fehlerbehandlung bei ungültigen
        Temperaturen und Höhendaten.
        """

        test_cases = [
            (
                "different number of values",

              
                np.array([15.0, 20.0]),
                np.array([0.0]),

                "gleich viele Werte",
            ),
            (
                "temperature at absolute zero",

                # Eine Temperatur von -273,15 °C ist physikalisch nicht zulässig.
                np.array([-273.15]),
                np.array([0.0]),
                "über -273,15",
            ),
            (
                "temperature contains NaN",

                np.array([np.nan]),
                np.array([0.0]),
                "gültige Zahlen",
            ),
        ]

        for (
            description,
            temperatures_c,
            altitudes_m,
            expected_message,
        ) in test_cases:

            with self.subTest(case=description):

     
                with self.assertRaisesRegex(
                    ValueError,
                    expected_message,
                ):
                    calculate_air_density(
                        temperatures_c=temperatures_c,
                        altitudes_m=altitudes_m,
                    )