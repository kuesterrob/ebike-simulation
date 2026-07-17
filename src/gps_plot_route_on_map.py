import folium
import logging
from pathlib import Path
from src.gps_reader import GPSReader

 
logger = logging.getLogger(__name__)

class GPSMap:

    def __init__(self, lats: list[str], lons: list[str], line_color="blue",tiles="CartoDB positron"):
        self.points = []
        self.line_color = line_color
        self.tiles = tiles

        for p in range(len(lons)):     
            self.add_points(lats[p], lons[p])

    # -- Punkte verwalten ---------------------------------------------------

    def add_points(self, lat: str, lon: str) -> None:
        """Fuegt einen einzelnen Punkt hinzu."""
        self.points.append((lat, lon))
        return None

    def clear(self) -> None:
        """Entfernt alle Punkte."""
        self.points = []
        return None

    # -- Karte bauen --------------------------------------------------------

    def _construct_map(self, with_line=True) -> folium.map:
        if not self.points:
            raise ValueError("Es wurden keine Koordinaten hinzugefuegt.")

        latlon = [(lat, lon) for lat, lon in self.points]

        # Karte auf den Durchschnitt aller Punkte zentrieren
        avg_lat = sum(lat for lat, _ in latlon) / len(latlon)
        avg_lon = sum(lon for _, lon in latlon) / len(latlon)
        map = folium.Map(location=[avg_lat, avg_lon], zoom_start=7,tiles = self.tiles)

        #Start/Ziel hinzufügen
        reader = GPSReader()
        if reader.haversine(lat1 = latlon[0][0], lon1=latlon[0][1], lat2=latlon[-1][0], lon2=latlon[-1][1]) < 10:
            folium.Marker(latlon[0], tooltip="Start/Ziel",
                icon=folium.Icon(color="green")).add_to(map)
        else:
            folium.Marker(latlon[0], tooltip="Start",
                icon=folium.Icon(color="green")).add_to(map)
            folium.Marker(latlon[-1], tooltip="Ziel",
                icon=folium.Icon(color="red")).add_to(map)


        # Optional: Punkte als Route verbinden
        if with_line:
            folium.PolyLine(latlon, color=self.line_color, weight=7, opacity=1).add_to(map)

        # Kartenausschnitt an alle Punkte anpassen
        map.fit_bounds(latlon)
        return map

    def save(self,with_line=True, filename="karte.html", folder="outputs") -> None:
        map = self._construct_map(with_line=with_line)

        # Ordner relativ zum Script-Speicherort aufloesen und anlegen
        basis = Path(__file__).parent.parent
        save_loc = basis / folder / filename
        save_loc.parent.mkdir(parents=True, exist_ok=True)

        map.save(str(save_loc))
        logger.info(f"Karte gespeichert: {save_loc}")
        return None