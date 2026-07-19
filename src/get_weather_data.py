import json
import logging
import pathlib
import requests
import pandas as pd
 
logger = logging.getLogger(__name__)
 
CACHE = pathlib.Path("data/weather_cache.json")
PRECISION = 2          # Nachkommastellen der Koordinaten-Rundung (~1 km)
FREQ = "15min"         # Zeit-Bucket (Datenauflösung)
 
 
class TripWeather:
    VARS = ["temperature_2m", "surface_pressure", "wind_speed_10m",
            "wind_direction_10m", "wind_gusts_10m", "precipitation"]  # xm ist Messhöhe über Boden
 
    def __init__(self, df:pd.df, lat="lat", lon="lon", time="time"):
        d = df.rename(columns={lat: "lat", lon: "lon"}).copy()
        d["time"] = (pd.to_datetime(d[time], utc=True)      # ...Z -> UTC
                       .dt.tz_convert("Europe/Vienna")      # -> Lokalzeit
                       .dt.tz_localize(None))
        self.df = d             
 
    @staticmethod
    def _key(la:float, lo:float, t:float)-> str:
        return f"{la},{lo},{t.isoformat()}"
 
    # ---- EIN Request fuer alle fehlenden Zellen, 15-min-Werte ----
    def _fetch(self, cells:list):
        try:
            lats = [c[0] for c in cells]
            lons = [c[1] for c in cells]
            times = pd.DatetimeIndex([c[2] for c in cells])
            past = times.max() < pd.Timestamp.now()
            url = ("https://historical-forecast-api.open-meteo.com/v1/forecast" if past
                else "https://api.open-meteo.com/v1/forecast")
            r = requests.get(url, timeout=60, params={
                "latitude":  ",".join(map(str, lats)),
                "longitude": ",".join(map(str, lons)),
                "minutely_15": ",".join(self.VARS),
                "wind_speed_unit": "ms", "timezone": "Europe/Vienna",
                "start_date": times.min().date().isoformat(),
                "end_date":   times.max().date().isoformat(),
            })
            r.raise_for_status()
            data = r.json()
            data = data if isinstance(data, list) else [data]   # 1 Ort -> Liste
            out = []
            for i, loc in enumerate(data):
                m = pd.DataFrame(loc["minutely_15"])
                m["time"] = pd.to_datetime(m["time"])
                idx = (m["time"] - times[i]).abs().argmin()
                out.append({v: float(m[v].iloc[idx]) for v in self.VARS})
            return out
        except requests.RequestException as e:
            logger.error(f"Fehler bei der Open-Meteo API-Anfrage: {e}")
            # Programm abbrechen, da ohne Wetterdaten keine weiteren Schritte möglich sind
            raise SystemExit(1) from e
 
    # ---- Cache laden, nur Fehlendes fetchen, pro Trackpunkt rekonstruieren ----
    def get_weather(self) -> pd.DataFrame:
        # Cache laden
        cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
 
        # Aehnliche Werte zu Zellen zusammenfassen (Koordinaten + Zeit-Bucket)
        df = self.df
        df["_lat"] = df["lat"].round(PRECISION)
        df["_lon"] = df["lon"].round(PRECISION)
        df["_t"]   = df["time"].dt.floor(FREQ)
        cells = [(la, lo, t) for la, lo, t
                 in df[["_lat", "_lon", "_t"]].drop_duplicates().itertuples(index=False)]
 
        # mit Cache vergleichen, nur fehlende Zellen an die API
        missing = [c for c in cells if self._key(*c) not in cache]
        logger.info(f"{len(df)} punkte, {len(missing)} neue Zellen zu fetchen")
 
        # fehlende Werte pullen, in Cache schreiben, Cache speichern
        if missing:
            for c, res in zip(missing, self._fetch(missing)):
                cache[self._key(*c)] = res
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
 
        # Daten aus Cache ins DataFrame einbinden (eine Zeile pro Trackpunkt)
        weather = pd.DataFrame(
            [cache[self._key(la, lo, t)]
             for la, lo, t in zip(df["_lat"], df["_lon"], df["_t"])],
            index=df.index,
        )
        return weather

