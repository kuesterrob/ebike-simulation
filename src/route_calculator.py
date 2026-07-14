from math import asin, cos, radians, sin
import numpy as np
import pandas as pd

class RouteCalculator:
    """Berechnung der Geschwindigkeit, Beschleunigun und Steigung aus den GPS-Daten."""

    def calculate_speed(self, timedeltas: np.ndarray, distances: np.ndarray) -> np.ndarray:
        """Berechnet die Geschwindigkeit aus den GPS-Daten."""

        speeds = np.zeros(len(timedeltas), dtype=float)

        for i in range(1, len(timedeltas)):
            delta_time = timedeltas[i]

            if delta_time > 0:
                speeds[i] = distances[i - 1] / delta_time

        return speeds
    
    def calculate_acceleration(self, timedeltas: np.ndarray, speeds: np.ndarray) -> np.ndarray:
        """Berechnet die Beschleunigung aus den GPS-Daten."""

        accelerations = np.zeros(len(timedeltas), dtype=float)

        for i in range(1, len(timedeltas)):
            delta_time = timedeltas[i]

            if delta_time > 0:
                accelerations[i] = (speeds[i] - speeds[i - 1]) / delta_time

        return accelerations
    
    def calculate_slope(self, distances: np.ndarray, elevations: np.ndarray) -> np.ndarray:
        """Berechnet die Steigung aus den GPS-Daten."""

        slopes = np.zeros(len(distances), dtype=float)

        for i in range(1, len(distances)):
            distance = distances[i - 1]

            if distance > 0:
                slopes[i] = (elevations[i] - elevations[i - 1]) / distance

        return slopes
        