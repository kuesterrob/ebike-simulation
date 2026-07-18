import logging
import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)


class Motor:
    """Berechnet Kraft, Leistung, Drehmoment und Strom des E-Bike-Motors."""

    def __init__(
        self,
        rider_mass_kg: float = 70.0,
        bike_mass_kg: float = 10.0,
        drag_area_m2: float = 0.5625,
        wheel_diameter_inch: float = 27.0,
        motor_constant_nm_per_a: float = 1.5,
        rolling_resistance_coefficient: float = 0.0077, # Quelle: Tengattini & Bigazzi (2018), DOI: 10.1080/02640414.2018.1458587
    ) -> None:
        
        if rider_mass_kg <= 0:
            raise ValueError(
                "Die Fahrermasse muss größer als 0 sein."
            )
        
        if bike_mass_kg <= 0:
            raise ValueError(
                "Die Bikemasse muss größer als 0 sein."
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
        
        
        if rolling_resistance_coefficient < 0:
            raise ValueError(
                "Der Rollwiderstandskoeffizient darf nicht "
                "negativ sein."
            )

        total_mass_kg = rider_mass_kg + bike_mass_kg
        self.total_mass_kg = total_mass_kg
        self.drag_area_m2 = drag_area_m2
        self.motor_constant_nm_per_a = motor_constant_nm_per_a
        self.rolling_resistance_coefficient = rolling_resistance_coefficient

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
        wind_speeds: np.ndarray,
        wind_directions: np.ndarray,
        move_directions: np.ndarray,
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
        # slopes entspricht dem Verhältnis aus Höhenänderung und tatsächlicher Streckenlänge. Damit entspricht slopes dem Sinus des Steigungswinkels.
        # Für den Rollwiderstand wird der Cosinus benötigt, weil nur die senkrecht auf die Straße wirkende Normalkraft berücksichtigt wird.
        cos_slope = np.sqrt(
            1.0
            - np.clip(
                slopes,
                -1.0,
                1.0,
            ) ** 2
        )

        # Der Rollwiderstand ergibt sich aus dem Rollwiderstandskoeffizienten und der Normalkraft:
        # F_Roll = c_rr * m * g * cos(alpha).
        rolling_force = (
            self.rolling_resistance_coefficient
            * self.total_mass_kg
            * self.gravity_m_per_s2
            * cos_slope
        )

       
        rolling_force = np.where(
            speeds > 0,  # Rollwiderstand entsteht nur, wenn das Fahrrad rollt.
            rolling_force,
            0.0,
        )

        # Die Luftwiderstandskraft wird für jeden Streckenabschnitt mit der dort berechneten Luftdichte und dem Windeinfluss bestimmt.
        # F_Luft = 0,5 * Luftdichte * Widerstandsfläche * Geschwindigkeit²
        # Bei geringerer Luftdichte oder Rückenwind fällt auch der Luftwiderstand und damit die benötigte Motorleistung kleiner aus.

        #Richtungs und Geschwindigkeitsdaten vorbereiten
        wind_speed_factor = 0.45                #Faktor für die Windgeschwindigkeit, da diese in 10m Höhe angegeben wird



        
        # Fahrtrichtung als Einheitsvektor 
        head = np.radians(move_directions[:-1])
        
        hx, hy = np.sin(head), np.cos(head)

        # Wind: Richtung, aus der er kommt -> Richtung, in die er weht (meteologisch)
        wind_directions = np.radians((wind_directions[:-1] + 180) % 360)
        

        wx = wind_speeds[:-1] * np.sin(wind_directions)
        wy = wind_speeds[:-1] * np.cos(wind_directions)
        

        ax = wx - speeds * hx
        ay = wy - speeds * hy
        

        v_apparent = np.hypot(ax, ay)          # Betrag des scheinbaren Windes
        v_long = -(ax * hx + ay * hy)

        air_force = (
            0.5
            * air_density_kg_per_m3
            * self.drag_area_m2
            * v_apparent
            * v_long
        )
        air_force_still = (
            0.5
            * air_density_kg_per_m3
            * self.drag_area_m2
            * speeds **2
            
        )
        wind_force = air_force - air_force_still

        # Die gesamte benötigte Antriebskraft ergibt sich aus der Summe der Beschleunigungs-, Steigungs- und Luftwiderstandskraft.
        total_force = (
            acceleration_force
            + slope_force
            + air_force
            + rolling_force
        )
        # Vorzeichenbehaftete mechanische Motorleistung:
        # Positiver Wert:
        # Der Motor muss das Fahrrad antreiben.
        # Negativer Wert:
        # Zum Einhalten des gemessenen Fahrprofils mussgebremst werden. Diese Leistung kann späterteilweise zur Rekuperation verwendet werden.
        signed_power = (
            total_force
            * speeds
        )

        # Antriebsfall nur positive Leistungswerte verwendet.
        drive_power = np.clip(
            signed_power,
            0.0,
            None,
        )

        # Die Bremsleistung wird als positiver Betrag gespeichert.
        braking_power = np.clip(
            -signed_power,
            0.0,
            None,
        )

        # Vorzeichenbehaftetes Drehmoment:
        # Positiv bedeutet Antrieb, negativ bedeutet Bremsen.
        signed_torque = (
            total_force
            * self.wheel_radius_m
        )

        # Positives Drehmoment für den Antrieb.
        drive_torque = np.clip(
            signed_torque,
            0.0,
            None,
        )

        # Bremsmoment als positiver Betrag.
        braking_torque = np.clip(
            -signed_torque,
            0.0,
            None,
        )

        #  Strom beschreibt nur den Antriebsfall. 
        motor_current = (
            drive_torque
            / self.motor_constant_nm_per_a
        )

        return {
            "acceleration_force_n": acceleration_force,
            "slope_force_n": slope_force,
            "rolling_force_n": rolling_force,
            "air_force_n": air_force,
            "wind_force_n" :wind_force,
            "force_n": total_force,
            "power_w": drive_power,
            # Zusätzliche Werte für die spätere Rekuperation.
            "signed_power_w": signed_power,
            "braking_power_w": braking_power,
            # Positives Antriebsdrehmoment.
            "torque_nm": drive_torque,
            # Zusätzliche Drehmomentwerte für Bremsphasen.
            "signed_torque_nm": signed_torque,
            "braking_torque_nm": braking_torque,
            "current_a": motor_current,
        }