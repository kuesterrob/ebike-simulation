import numpy as np
import pandas as pd
from pathlib import Path
from math import radians, sin, cos, asin, sqrt

class GPSReader:

    def __init__(self):
        self.df = pd.DataFrame()
        self.total_3d = 0.0
        self.total_h = 0.0
        self.climb = 0.0
        self.descent = 0.0
        self.distances = np.array([])

    def load_file(self, file_path: Path) -> pd.DataFrame:
        "Liest GPS-Daten aus CSV aus und gibt sie als Pandas DataFrame zurück."

        try:
            df = pd.read_csv(
                file_path,
                sep=";",              
                decimal=".",
                parse_dates=["time"],          
                date_format="ISO8601",)
            self.df = df
            return(df)
        except FileNotFoundError:
            raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")
        
    def calculate_distances(self)-> np.array:
        "Berechnet die 3D-Distanz zwischen aufeinanderfolgenden GPS-Punkten."
        lat = self.df["lat"].to_numpy(dtype=float)
        lon = self.df["lon"].to_numpy(dtype=float)
        ele = self.df["ele"].to_numpy(dtype=float)

        n = len(lat)
        if not (n == len(lon) == len(ele)):
            raise ValueError("Alle drei Listen müssen gleich lang sein.")
        if n < 2:
            raise ValueError("Mindestens 2 Punkte nötig.")
        
        
        prev = 0  #Variable für vorheriges Element initialisieren

        for i in range(1, n):
            d_h = self._haversine(lat[prev], lon[prev], lat[i], lon[i])
    
            dh = ele[i] - ele[prev]

            self.distances = np.append(self.distances, sqrt(d_h ** 2 + dh ** 2))
            self.total_h += d_h
            self.total_3d += sqrt(d_h ** 2 + dh ** 2)
    
            if dh > 0:
                self.climb += dh
            else:
                self.descent += abs(dh)

            prev = i

        return(self.distances)
    
    def get_stats(self) -> dict:
        "Gibt ein Dictionary mit Gesamtdistanz, horizontaler Distanz, Aufstieg und Abstieg zurück."
        
        return {
            "Distanz_3d_m": round(self.total_3d, 1),
            "Distanz_vertikal_m": round(self.total_h, 1),
            "Aufstieg_m": round(self.climb, 1),
            "Abstieg_m": round(self.descent, 1),
            "Punkte_gesamt": len(self.df),
            "Horizontale_Distanz": sum(self.distances),
        }
    
    def _haversine(self,lat1, lon1, lat2, lon2):
        "Horizontale Distanz in Metern (Haversine-Formel)."
        R = 6371000
        phi1, phi2 = radians(lat1), radians(lat2)
        dphi = radians(lat2 - lat1)
        dlam = radians(lon2 - lon1)
        a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlam / 2) ** 2
        return 2 * R * asin(sqrt(a))
    

    
    
    

            
        