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
            
            #Filterung von GPS Rauschen mittels Durchschnitt der umliegenden Werte  
        threshholdfactor = 1.5  
        for acceleration in range(0, len(accelerations)):
            if accelerations[acceleration] > 3:
                print(f"Warnung: Beschleunigung an Index {acceleration} ist größer als 3 m/s². Wert: {accelerations[acceleration]} m/s²")
            if acceleration == 0:
                avg = sum([accelerations[acceleration + 1], accelerations[acceleration + 2]]) / 2 # Berechnung des Mittelwerts der umliegenden Werte
                if (accelerations[acceleration] > threshholdfactor * avg) or (accelerations[acceleration] < avg / threshholdfactor):  #Überschreitung des Mittelwerts mal dem Faktor oder Unterschreitung des Mittelwerts durch den Faktor
                    accelerations[acceleration] = avg
                else:
                    continue

            if acceleration == 1:
                avg = sum([accelerations[acceleration + 1], accelerations[acceleration + 2], accelerations[acceleration - 1]]) / 3 # Berechnung des Mittelwerts der umliegenden Werte
                if (accelerations[acceleration] > threshholdfactor * avg) or (accelerations[acceleration] < avg / threshholdfactor):  #Überschreitung des Mittelwerts mal dem Faktor oder Unterschreitung des Mittelwerts durch den Faktor
                    accelerations[acceleration] = avg
                else:
                    continue

            if acceleration >= 2 and acceleration <= len(accelerations) - 3:
                avg = sum([accelerations[acceleration + 1], accelerations[acceleration + 2], accelerations[acceleration - 1], accelerations[acceleration - 2]]) / 4 # Berechnung des Mittelwerts der umliegenden Werte
                if (accelerations[acceleration] > threshholdfactor * avg) or (accelerations[acceleration] < avg / threshholdfactor):  #Überschreitung des Mittelwerts mal dem Faktor oder Unterschreitung des Mittelwerts durch den Faktor
                    accelerations[acceleration] = avg
                else:
                    continue

            if acceleration == len(accelerations) - 2:
                avg = sum([accelerations[acceleration - 1], accelerations[acceleration - 2], accelerations[acceleration + 1]]) / 3 # Berechnung des Mittelwerts der umliegenden Werte
                if (accelerations[acceleration] > threshholdfactor * avg) or (accelerations[acceleration] < avg / threshholdfactor):  #Überschreitung des Mittelwerts mal dem Faktor oder Unterschreitung des Mittelwerts durch den Faktor
                    accelerations[acceleration] = avg
                else:
                    continue

            if acceleration == len(accelerations) - 1:
                avg = sum([accelerations[acceleration - 1], accelerations[acceleration - 2]]) / 2 # Berechnung des Mittelwerts der umliegenden Werte
                if (accelerations[acceleration] > threshholdfactor * avg) or (accelerations[acceleration] < avg / threshholdfactor):  #Überschreitung des Mittelwerts mal dem Faktor oder Unterschreitung des Mittelwerts durch den Faktor
                    accelerations[acceleration] = avg
                else:
                    continue

        return accelerations
    
    
    def calculate_slope(self, distances: np.ndarray, elevations: np.ndarray) -> np.ndarray:
        """Berechnet die Steigung aus den GPS-Daten."""

        slopes = np.zeros(len(distances), dtype=float)

        for i in range(0, len(distances)):
            if distances[i] > 0:
                slopes[i] = (elevations[i+1] - elevations[i]) / distances[i]

        return slopes

    

    