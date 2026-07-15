from src.battery_base import BatteryBase
import logging


class BatteryPack(BatteryBase):
    def __init__(
        self,
        capacity_nom_Ah: float,
        internal_resistance_mOhm: float = 80.0,
        initial_soc: float = 1.0,
        Vmin: float = 3.0,
        Vmax: float = 4.2,
        parallel_cells: int = 1,
        
    ):
        error = False
        try:
            if capacity_nom_Ah <= 0:
                logging.error(f"capacity can not be <= 0, is {capacity_nom_Ah}")
                error = True
        except TypeError:
            logging.error(f"capacity should be float, is {type(capacity_nom_Ah)}")
            error = True
        try:
            if initial_soc <= 0:
                logging.error(f"inital soc can not be <= 0, is {initial_soc}")
                error = True
        except TypeError:
            logging.error(f"initial soc should be float, is {type(initial_soc)}")
            error = True
        if error:
            raise ValueError(f"Parameters were initilized with wrong values or types, check log for details")
        self.C_nom = capacity_nom_Ah * (3600.0)  # Kapazität in As
        
        self.soc = max(0.0, min(initial_soc, 1.0))
        self.R_int = internal_resistance_mOhm * 1e-3 * (1/parallel_cells)  

        self.Vmin = Vmin
        self.Vmax = Vmax

    def apply_current(self, current: float, duration: float) -> None:
        if current > 0:
            if current > (self.voltage(current=current)/self.R_int):
                raise ValueError(f"Current is higher than the maximum that can be provided by the battery")
            dsoc = -(current * duration) / self.C_nom  
            self.soc = max(0.0, min(self.soc + dsoc, 1.0))
            error = False
            if self.soc <= 0.0:
                logging.warning("SoC is below 0.0, battery is empty.")
                error = True
            if self.soc > 1.0:
                logging.warning("SoC is above 1.0, battery is overcharged.")
                error = True
            if error:
                raise ValueError("SoC is out of bounds.")
        elif current < 0:
            raise ValueError(f"Current is negative:{current:.2f}")

    def voltage(self, current: float = 0.0) -> float:
        open_circuit_voltage = self.Vmin + self.soc * (self.Vmax - self.Vmin)
        return open_circuit_voltage - self.R_int * current

    def is_empty(self) -> bool:
        return self.soc <= 0.0 + 1e-9

    def is_full(self) -> bool:
        return self.soc >= 1.0 - 1e-9

    def __str__(self):
        return f"BatteryPack(SoC={self.soc * 100:.1f}%, V={self.voltage():.2f} V)"
