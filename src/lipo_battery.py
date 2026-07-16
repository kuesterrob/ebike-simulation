from src.battery_pack import BatteryPack


class LiPoBatteryPack(BatteryPack):
    """LiPo-Akkupack mit eigener OCV-Kennlinie."""

    def __init__(
        self,
        capacity_nom_Ah: float,
        internal_resistance_mOhm: float = 80.0,
        initial_soc: float = 1.0,
        Vmin: float = 32.0,
        Vmax: float = 42.0,
        parallel_cells: int = 1,
        initial_temperature_c: float = 25.0,
        thermal_capacity_j_per_k: float = 10_000.0,
        thermal_resistance_k_per_w: float = 2.0,
        resistance_temperature_coefficient_per_k: float = 0.01,
        reference_temperature_c: float = 25.0,
    ) -> None:
        super().__init__(
            capacity_nom_Ah=capacity_nom_Ah,
            internal_resistance_mOhm=(
                internal_resistance_mOhm
            ),
            initial_soc=initial_soc,
            Vmin=Vmin,
            Vmax=Vmax,
            parallel_cells=parallel_cells,
            initial_temperature_c=(
                initial_temperature_c
            ),
            thermal_capacity_j_per_k=(
                thermal_capacity_j_per_k
            ),
            thermal_resistance_k_per_w=(
                thermal_resistance_k_per_w
            ),
            resistance_temperature_coefficient_per_k=(
                resistance_temperature_coefficient_per_k
            ),
            reference_temperature_c=(
                reference_temperature_c
            ),
        )

    def voltage(
        self,
        current: float = 0.0,
    ) -> float:
        """Berechnet die LiPo-Spannung unter Last."""

        # LiPo-Open-Circuit-Spannung:
        # U_OCV = U_min + SoC^0,3 * (U_max - U_min)
        open_circuit_voltage = (
            self.Vmin
            + (self.soc**0.3)
            * (self.Vmax - self.Vmin)
        )

        internal_resistance = (
            self.effective_internal_resistance()
        )

        # Spannung unter Last:
        # U_Last = U_OCV - I * R(T)
        return (
            open_circuit_voltage
            - internal_resistance * current
        )