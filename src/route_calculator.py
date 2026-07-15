from math import asin, cos, radians, sin
import numpy as np
import pandas as pd

class RouteCalculator:
    """Berechnung der Geschwindigkeit, Beschleunigun und Steigung aus den GPS-Daten."""

    def calculate_speed(self, timedeltas: np.ndarray, distances: np.ndarray) -> np.ndarray:
        """Berechnet die Geschwindigkeit aus den GPS-Daten."""

        speeds = np.zeros(len(timedeltas), dtype=float)

        for i in range(0, len(timedeltas)):
            delta_time = timedeltas[i]

            if delta_time > 0:
                speeds[i] = distances[i] / delta_time

            else:
                raise ValueError(f"Zeitdifferenz darf nicht null oder kleiner sein. Index: {i}, Zeitdifferenz: {delta_time}")

        return speeds
    
    def calculate_acceleration(self, timedeltas: np.ndarray, speeds: np.ndarray) -> np.ndarray:
        """Berechnet die Beschleunigung aus den GPS-Daten."""

        accelerations = np.zeros(len(timedeltas), dtype=float)

        for i in range(0, len(timedeltas)):
            delta_time = timedeltas[i]

            if delta_time > 0:

                if i == 0:
                    accelerations[i] = speeds[i] / delta_time 

                else:
                    accelerations[i] = (speeds[i] - speeds[i - 1]) / delta_time
            
            else:
                raise ValueError(f"Zeitdifferenz darf nicht null oder kleiner sein. Index: {i}, Zeitdifferenz: {delta_time}")
            

        threshold_factor = 2.0
        half_window = 5         # Anzahl der Nachbarwerte, die für den Vergleich herangezogen werden.

        filtered = accelerations.copy() #Kopie der Werte erstellen, damit gegen die Originalwerte verglichen werden kann.

        for i in range(len(accelerations)):
            neighbors = []
            for k in range(-half_window, half_window + 1):   #Nachbarliste erzeugen, wobei die Grenzen der Liste berücksichtigt werden.
                if k != 0 and 0 <= i + k < len(accelerations):
                    neighbors.append(accelerations[i + k])  
            if not neighbors:                               #Abbrechen wenn keine Nachbarn vorhanden sind.
                continue

            avg = sum(neighbors) / len(neighbors)

            if accelerations[i] > threshold_factor * avg or accelerations[i] < avg / threshold_factor:
                filtered[i] = avg

        return filtered
    
    
    def calculate_slope(self, distances: np.ndarray, elevations: np.ndarray) -> np.ndarray:
        """Berechnet die Steigung aus den GPS-Daten."""

        slopes = np.zeros(len(distances), dtype=float)

        for i in range(0, len(distances)):
            if distances[i] > 0:
                slopes[i] = (elevations[i+1] - elevations[i]) / distances[i]

        return slopes

    

    