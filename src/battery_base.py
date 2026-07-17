from abc import ABC, abstractmethod


class BatteryBase(ABC):
    """
    Gemeinsame Schnittstelle für die verschiedenen
    Akkumodelle.
    """

    @abstractmethod
    def apply_current(
        self,
        current: float,
        duration: float,
    ) -> None:
        """
        Aktualisiert den Ladezustand anhand von
        Strom und Zeitdauer.
        """
        pass

    @abstractmethod
    def voltage(
        self,
        current: float = 0.0,
    ) -> float:
        """
        Gibt die Akkuspannung für den angegebenen
        Strom zurück.
        """
        pass