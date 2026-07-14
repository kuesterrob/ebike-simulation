from src.battery_pack import BatteryPack


class LiPoBatteryPack(BatteryPack):

    def __init__(
        self,
        capacity_nom_Ah: float,
        internal_resistance_mOhm: float = 80.0,
        initial_soc: float = 1.0,
        Vmin: float = 32.0,
        Vmax: float = 42.0,
    ):
        super().__init__(capacity_nom_Ah, internal_resistance_mOhm, initial_soc, Vmin, Vmax)


    def voltage(self, current=0.0)-> float:
        if current > 0:
            open_circuit_voltage = self.Vmin + (self.soc**0.3) * (self.Vmax - self.Vmin)
            return open_circuit_voltage - self.R_int * current
