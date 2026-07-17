from math import radians, sin, cos, asin, sqrt, atan2, degrees
import numpy as np
import pandas as pd
 
class MovementDirection:
    def __init__(self, df: pd.DataFrame, lat: str = "lat", lon: str = "lon"):
        self.df = df.reset_index(drop=True)
        self.lat, self.lon = lat, lon
 
    def _bearing(self, lat1, lon1, lat2, lon2):
        "Kurswinkel in Grad (0-360)."
        phi1, phi2 = radians(lat1), radians(lat2)
        dlam = radians(lon2 - lon1)
        x = sin(dlam) * cos(phi2)
        y = cos(phi1) * sin(phi2) - sin(phi1) * cos(phi2) * cos(dlam)
        return (degrees(atan2(x, y)) + 360) % 360
 
    def calculate(self) -> pd.DataFrame:
        lat = self.df[self.lat].to_numpy()
        lon = self.df[self.lon].to_numpy()
        pairs = range(len(lat) - 1)
        brng = [self._bearing(lat[i], lon[i], lat[i + 1], lon[i + 1]) for i in pairs] + [np.nan]
        return self.df.assign(bearing=brng)
