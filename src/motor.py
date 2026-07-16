import logging
import numpy as np


logger = logging.getLogger(__name__)


class Motor:
    """Berechnet Kraft, Leistung, Drehmoment und Strom des E-Bike-Motors."""

    def __init__(
        self,
        total_mass_kg: float = 80.0,
        drag_area_m2: float = 0.5625,
        wheel_diameter_inch: float = 27.0,
        motor_constant_nm_per_a: float = 1.5,
    ) -> None:
        
        if total_mass_kg <= 0:
            raise ValueError(
                "Die Gesamtmasse muss größer als 0 sein."
            )

        if drag_area_m2 < 0:
            raise ValueError(
                "Die Luftwiderstandsfläche darf nicht "
                "negativ sein."
            )

        if wheel_diameter_inch <= 0:
            raise ValueError(
                "Der Raddurchmesser muss größer als 0 sein."
            )

        if motor_constant_nm_per_a <= 0:
            raise ValueError(
                "Die Motorkonstante muss größer als 0 sein."
            )

    
        self.total_mass_kg = total_mass_kg
        self.drag_area_m2 = drag_area_m2
        self.motor_constant_nm_per_a = motor_constant_nm_per_a

        # Erdbeschleunigung in m/s².
        self.gravity_m_per_s2 = 9.81

        # Umrechnung des Raddurchmessers von Zoll in Meter.
        # Anschließend wird der Durchmesser durch zwei geteilt,
        # um den Radradius zu erhalten.
        self.wheel_radius_m = (
            wheel_diameter_inch * 0.0254 / 2
        )

    def calculate(
        self,
        speeds: np.ndarray,
        accelerations: np.ndarray,
        slopes: np.ndarray,
        air_density_kg_per_m3: np.ndarray,
    ) -> dict[str, np.ndarray]:
        """
        Berechnet die Motorgrößen aus den zuvor vom
        RouteCalculator bestimmten Fahrdaten.
        """

        if not (
            len(speeds)
            == len(accelerations)
            == len(slopes)
            == len(air_density_kg_per_m3)
        ):
            raise ValueError(
                "Geschwindigkeit, Beschleunigung, "
                "Steigung und Luftdichte müssen gleich viele Werte enthalten."
            )

        if len(speeds) == 0:
            raise ValueError(
                "Die Motordaten dürfen nicht leer sein."
            )

        if not (
            np.all(np.isfinite(speeds))
            and np.all(np.isfinite(accelerations))
            and np.all(np.isfinite(slopes))
            and np.all(np.isfinite(air_density_kg_per_m3))
        ):
            raise ValueError(
                "Die Motordaten enthalten ungültige Werte."
            )
        
        # Eine Luftdichte von null oder kleiner ist  physikalisch nicht möglich.
        if np.any(air_density_kg_per_m3 <= 0):
            raise ValueError(
                "Die Luftdichte muss größer als 0 sein."
            )

        # Kraft, die zur Beschleunigung von Fahrer und Fahrrad benötigt wird.
        acceleration_force = (
            self.total_mass_kg * accelerations
        )

        # Steigungskraft: positiv bergauf, negativ bergab.
        # Da slopes = Δh/Δs ist, gilt: F = m * g * slopes.
        slope_force = (
            self.total_mass_kg
            * self.gravity_m_per_s2
            * slopes
        )

        # Die Luftwiderstandskraft wird für jeden Streckenabschnitt mit der dort berechneten Luftdichte bestimmt.
        # F_Luft = 0,5 * Luftdichte * Widerstandsfläche * Geschwindigkeit²
        # Bei geringerer Luftdichte fällt auch der Luftwiderstand und damit die benötigte Motorleistung kleiner aus.
        air_force = (
            0.5
            * air_density_kg_per_m3
            * self.drag_area_m2
            * speeds**2
        )

        # Die gesamte benötigte Antriebskraft ergibt sich aus der Summe der Beschleunigungs-, Steigungs- und Luftwiderstandskraft.
        total_force = (
            acceleration_force
            + slope_force
            + air_force
        )

        # Mechanische Motorleistung.
        power = total_force * speeds
        for i in range(len(power)):
            if power[i] < 0:
                power[i] = 0.0
                

        # Drehmoment am angetriebenen Rad.
        torque = total_force * self.wheel_radius_m
        for i in range(len(torque)):
            if torque[i] < 0:
                torque[i] = 0.0
                

        # Benötigter Motorstrom über die Motorkonstante.
        motor_current = (
            torque / self.motor_constant_nm_per_a
        )

        return {
            "acceleration_force_n": acceleration_force,
            "slope_force_n": slope_force,
            "air_force_n": air_force,
            "force_n": total_force,
            "power_w": power,
            "torque_nm": torque,
            "current_a": motor_current,
        }