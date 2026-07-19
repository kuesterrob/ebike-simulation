import json, os, time
from pathlib import Path
import pandas as pd, requests
import logging

logger = logging.getLogger(__name__)
 
CACHE = Path(__file__).parent / "../data/geocode_cache.json"
PRECISION = 3  # Dezimalstellen für grid bestimmung: 3 = ~110 m
 
class Reverse_Geocoder():

    #Vor dem ausführen api key festlegen im terminal mit export GEOAPIFY_API_KEY="key"
    #Wir nutzen die Geoapify API im klar Text weil wir einen kostenlosen Account nutzen. Für die Nutzung in einem Produktivsystem sollte der Key verschlüsselt werden.
    def __init__(self,df: pd.df, api_key = "58a1b553653b4401b914c1ed967d6642"):
        self.df = df
        self.api_key = api_key

    def geoapify_bulk(self,coords) -> json:
        try:
            """POST coords to Geoapify batch, poll until done, return one dict per coord."""
            resp = requests.post(
                "https://api.geoapify.com/v1/batch/geocode/reverse", 
                params={"apiKey": self.api_key},
                json=[{"lat": lat, "lon": lon} for lat, lon in coords],
                timeout=30,
            )
            resp.raise_for_status()
            job_url = resp.json()["url"]
            while (r := requests.get(job_url, timeout=30)).status_code == 202:
                time.sleep(5)  # 202 = daten werden noch verarbeitet
                logger.info("Warten auf reverse geocoding api")
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            logger.error(f"Fehler bei der Geoapify API-Anfrage: {e}")
            #Programm abbrechen, da ohne Geocoding keine weiteren Schritte möglich sind
            raise SystemExit(1) from e
 
    def get_results(self) -> pd.df:
        #Chache laden
        cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
        
        #Ähnliche Werte entfernen um unnötige request zu eliminieren (api limit 1000 werte)
        df = self.df
        df["_lat"] = df["lat"].round(PRECISION)
        df["_lon"] = df["lon"].round(PRECISION)
        cells = df[["_lat", "_lon"]].drop_duplicates().itertuples(index=False)
        
        #mit cache vergleichen und nur fehlende werte an api übergeben 
        missing = [(la, lo) for la, lo in cells if f"{la},{lo}" not in cache]
        logger.info(f"{len(df)} punkte, {len(missing)} neue Orte zu fetchen")
        
        #fehlende Werte von api pullen um in Cache schreiben, dann chache speichern
        
        if missing:
            for (la, lo), res in zip(missing, self.geoapify_bulk(missing)):
                cache[f"{la},{lo}"] = {
                    "place": res.get("city") or res.get("town") or res.get("village") or res.get("municipality") or res.get("county"),
                    "street": res.get("street"),
                    "postcode": res.get("postcode"),
                    "country": res.get("country"),
                    "formatted": res.get("formatted"),
                }
            
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        
        #Daten aus cache ins dataframe einbinden
        places = pd.DataFrame(
            [cache[f"{la},{lo}"] for la, lo in zip(df["_lat"], df["_lon"])], index=df.index
        )
        return(places)


