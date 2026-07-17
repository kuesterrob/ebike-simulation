import unittest
import numpy as np

from src.route_calculator import RouteCalculator


class TestRouteCalculator(unittest.TestCase):
    """
    Testet die Berechnung von Geschwindigkeit,
    Beschleunigung und Steigung.
    """

    def setUp(self):
        """
        Methode wird vor jeder Testmethode ausgeführt.
        Dadurch erhält jeder Test einen neuen, unabhängigen
        RouteCalculator.
        """
        self.calculator = RouteCalculator()

    # Tests mit gültigen Eingabewerten
    def test_calculate_speed_with_known_values(self):
        """
        Prüft die Geschwindigkeitsberechnung mit bekannten Werten.
        """

        # Eingaben und erwartetes Ergebnis festlegen.
        time_deltas = np.array(
            [2.0, 2.0, 2.0]
        )

        distances = np.array(
            [4.0, 8.0, 12.0]
        )

        expected_speeds = np.array(
            [2.0, 4.0, 6.0]
        )

        # testende Methode aufrufen
        calculated_speeds = (
            self.calculator.calculate_speed(
                time_deltas,
                distances,
            )
        )

        # Berechnetes und erwartetes Ergebnis vergleichen.
        # Durch assert_allclose berücksichtigung kleine Rundungsfehler
        np.testing.assert_allclose(
            calculated_speeds,
            expected_speeds,
        )

    def test_calculate_acceleration_with_known_values(self):
        """
        Prüft die Beschleunigungsberechnung mit bekannten Werten.
        """

        time_deltas = np.array(
            [2.0, 2.0, 2.0]
        )

        speeds = np.array(
            [2.0, 4.0, 6.0]
        )

        expected_accelerations = np.array(
            [1.0, 1.0, 1.0]
        )

        calculated_accelerations = (
            self.calculator.calculate_acceleration(
                time_deltas,
                speeds,
            )
        )

        np.testing.assert_allclose(
            calculated_accelerations,
            expected_accelerations,
        )

    def test_calculate_slope_with_known_values(self):
        """
        Prüft positive und negative Steigungen.
        """

        distances = np.array(
            [4.0, 8.0, 12.0]
        )

        elevations = np.array(
            [100.0, 100.4, 101.2, 100.0]
        )

        expected_slopes = np.array(
            [0.1, 0.1, -0.1]
        )

        calculated_slopes = (
            self.calculator.calculate_slope(
                distances,
                elevations,
            )
        )

        np.testing.assert_allclose(
            calculated_slopes,
            expected_slopes,
        )

    # Tests der Fehlerbehandlung
    def test_calculate_speed_rejects_invalid_input(self):
        """
        Prüft, ob calculate_speed bei ungültigen Eingaben
        einen ValueError mit einer passenden Meldung auslöst.
        """
        test_cases = [
            (
                "unterschiedliche Anzahl von Werten",
                np.array([1.0, 2.0]),
                np.array([5.0]),
                "gleich viele Werte",
            ),
            (
                "Zeitdifferenz ist null",
                np.array([1.0, 0.0]),
                np.array([5.0, 5.0]),
                "nicht null oder kleiner",
            ),
            (
                "negative Distanz",
                np.array([1.0]),
                np.array([-5.0]),
                "nicht negativ",
            ),
        ]

        #Schleife führt alle oben definierten Fälle aus.
        for (
            description,
            time_deltas,
            distances,
            expected_message,
        ) in test_cases:

            # subTest zeigt bei einem Fehler an, welcher einzelne Fall fehlgeschlagen ist.
            with self.subTest(case=description):

                #  Test ist nur erfolgreich, wenn innerhalb dieses Blocks ein ValueError ausgelöst wird.
                # Zusätzlich wird geprüft, ob die Fehlermeldung den angegebenen Text enthält.
                with self.assertRaisesRegex(
                    ValueError,
                    expected_message,
                ):
                    self.calculator.calculate_speed(
                        time_deltas,
                        distances,
                    )

    def test_calculate_acceleration_rejects_invalid_input(self):
        """
        Prüft die Fehlerbehandlung der Beschleunigungsberechnung.
        """

        test_cases = [
            (
                "unterschiedliche Anzahl von Werten",
                np.array([1.0, 2.0]),
                np.array([2.0]),
                "gleich viele Werte",
            ),
            (
                "Zeitdifferenz ist null",
                np.array([1.0, 0.0]),
                np.array([2.0, 4.0]),
                "nicht null oder kleiner",
            ),
            (
                "Geschwindigkeit ist NaN",
                np.array([1.0, 1.0]),
                np.array([2.0, np.nan]),
                "gültige Zahlen",
            ),
        ]

        for (
            description,
            time_deltas,
            speeds,
            expected_message,
        ) in test_cases:

            with self.subTest(case=description):
                with self.assertRaisesRegex(
                    ValueError,
                    expected_message,
                ):
                    self.calculator.calculate_acceleration(
                        time_deltas,
                        speeds,
                    )

    def test_calculate_slope_rejects_invalid_input(self):
        """
        Prüft die Fehlerbehandlung der Steigungsberechnung.
        """

        test_cases = [
            (
                "zu wenige Höhenwerte",
                np.array([10.0, 20.0]),
                np.array([100.0, 101.0]),
                "genau einen Wert",
            ),
            (
                "negative Distanz",
                np.array([-10.0]),
                np.array([100.0, 101.0]),
                "nicht negativ",
            ),
            (
                "Höhenwert ist NaN",
                np.array([10.0]),
                np.array([100.0, np.nan]),
                "gültige Zahlen",
            ),
        ]

        for (
            description,
            distances,
            elevations,
            expected_message,
        ) in test_cases:

            with self.subTest(case=description):
                with self.assertRaisesRegex(
                    ValueError,
                    expected_message,
                ):
                    self.calculator.calculate_slope(
                        distances,
                        elevations,
                    )