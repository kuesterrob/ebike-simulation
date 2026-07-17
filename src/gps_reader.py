import logging 
import numpy as np
import pandas as pd
from pathlib import Path
from math import radians, sin, cos, asin, sqrt

logger = logging.getLogger(__name__)

class GPSReader:

    """Liest GPS-Daten aus CSV-Dateien und berechnet Distanzen, Aufstieg und Abstieg."""

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
                date_format="ISO8601",
            )

        except FileNotFoundError as error:
            raise FileNotFoundError(
                f"Datei nicht gefunden: {file_path}"
            ) from error

        except pd.errors.EmptyDataError as error:
            raise ValueError(
                "Die GPS-Datei ist leer."
            ) from error

        except pd.errors.ParserError as error:
            raise ValueError(
                "Die GPS-Datei konnte nicht gelesen werden."
            ) from error

        required_columns = {
            "lat",
            "lon",
            "ele",
            "time",
            "temperature",
        }

        missing_columns = (
            required_columns - set(df.columns)
        )

        if missing_columns:
            raise ValueError(
                "In der GPS-Datei fehlen folgende Spalten: "
                f"{', '.join(sorted(missing_columns))}"
            )

        if (
            df[list(required_columns)]
            .isnull()
            .any()
            .any()
        ):
            raise ValueError(
                "Die GPS-Datei enthält fehlende Werte."
            )

        self.df = df

        logger.info(
            "GPS-Datei geladen: %d Datenpunkte",
            len(df),
        )

        return df
        
    def calculate_distances(self)-> np.array:
        "Berechnet die 3D-Distanz zwischen aufeinanderfolgenden GPS-Punkten."
        if self.df.empty:
            raise ValueError(
                "Es wurden noch keine GPS-Daten geladen."
            )

        lat = self.df["lat"].to_numpy(
            dtype=float
        )
        lon = self.df["lon"].to_numpy(
            dtype=float
        )
        ele = self.df["ele"].to_numpy(
            dtype=float
        )

        if not (
            np.all(np.isfinite(lat))
            and np.all(np.isfinite(lon))
            and np.all(np.isfinite(ele))
        ):
            raise ValueError(
                "Koordinaten und Höhendaten müssen "
                "gültige Zahlen enthalten."
            )

        n = len(lat)

        if not (
            n == len(lon) == len(ele)
        ):
            raise ValueError(
                "Koordinaten und Höhendaten müssen "
                "gleich viele Werte enthalten."
            )

        if n < 2:
            raise ValueError(
                "Mindestens 2 GPS-Punkte sind erforderlich."
            )
        
        prev = 0  #Variable für vorheriges Element initialisieren

        for i in range(1, n):
            d_h = self.haversine(lat[prev], lon[prev], lat[i], lon[i])
    
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
    
    def haversine(self,lat1, lon1, lat2, lon2):
        "Horizontale Distanz in Metern (Haversine-Formel)."
        R = 6371000
        phi1, phi2 = radians(lat1), radians(lat2)
        dphi = radians(lat2 - lat1)
        dlam = radians(lon2 - lon1)
        a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlam / 2) ** 2
        return 2 * R * asin(sqrt(a))
    
    def get_dataframe(self) -> pd.dataframe:
        return(self.df)

    
    
    

            
        