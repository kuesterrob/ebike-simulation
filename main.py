from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.gps_reader import GPSReader
from src.route_calculator import RouteCalculator
from src.motor import Motor
from src.lipo_battery import LiPoBatteryPack
from src.nmc_battery import NMCBatteryPack


PROJECT_DIRECTORY = Path(__file__).resolve().parent

GPS_FILE = (
    PROJECT_DIRECTORY
    / "data"
    / "final_project_input_data.csv"
)


def main() -> None:
    # GPS-Datei einlesen
    reader = GPSReader()
    df = reader.load_file(GPS_FILE)

    # Distanzen zwischen den GPS-Punkten berechnen
    distances = reader.calculate_distances()

    # Zeitpunkte und Zeitabstände auslesen
    zeit = df["time"].to_numpy(dtype="datetime64[ms]")

    zeitdeltas = (
        df["time"]
        .diff()
        .dt.total_seconds()
        .to_numpy()
    )

    # Gesamtdistanz zu jedem Zeitpunkt berechnen
    total_dist = np.concatenate(
        ([0.0], np.cumsum(distances))
    )

    # --------------------------------------------------
    # Routendaten berechnen und filtern
    # --------------------------------------------------

    route_calculator = RouteCalculator()

    # Ungefilterte Geschwindigkeit berechnen
    raw_speeds = route_calculator.calculate_speed(
        zeitdeltas,
        distances,
    )

    # Einzelne Ausreißer der Geschwindigkeit entfernen
    speeds = route_calculator.median_filter(
        raw_speeds,
        window_size=5,
    )

    # Beschleunigung aus der gefilterten Geschwindigkeit berechnen
    raw_accelerations = route_calculator.calculate_acceleration(
        zeitdeltas,
        speeds,
    )

    # Beschleunigung mit gleitendem Mittelwert glätten
    accelerations = route_calculator.moving_average(
        raw_accelerations,
        window_size=5,
    )

    # Höhenwerte aus den GPS-Daten auslesen
    elevations = df["ele"].to_numpy(dtype=float)

    # Einzelne Ausreißer der Höhenwerte entfernen
    filtered_elevations = route_calculator.median_filter(
        elevations,
        window_size=5,
    )

    # Steigung aus den gefilterten Höhenwerten berechnen
    slopes = route_calculator.calculate_slope(
        distances,
        filtered_elevations,
    )

    # Steigung zusätzlich leicht glätten
    slopes = route_calculator.moving_average(
        slopes,
        window_size=5,
    )

    # Erstes Element entfernen, damit alle Arrays gleich lang sind
    zeitdeltas = zeitdeltas[1:]
    raw_speeds = raw_speeds[1:]
    speeds = speeds[1:]
    raw_accelerations = raw_accelerations[1:]
    accelerations = accelerations[1:]

    # Die Motorergebnisse gehören zu den Zeitpunkten ab Index 1
    plot_time = zeit[1:]

    # Da slopes = Δh/Δs ist, entspricht slopes dem Sinus des Winkels
    slope_in_degrees = np.degrees(
        np.arcsin(
            np.clip(slopes, -1.0, 1.0)
        )
    )

    # --------------------------------------------------
    # Motorberechnung
    # --------------------------------------------------

    motor = Motor()

    motor_results = motor.calculate(
        speeds=speeds,
        accelerations=accelerations,
        slopes=slopes,
    )

    forces = motor_results["force_n"]
    powers = motor_results["power_w"]
    torques = motor_results["torque_nm"]
    motor_currents = motor_results["current_a"]

    # --------------------------------------------------
    # Ergebnisse kontrollieren
    # --------------------------------------------------

    print("Anzahl Zeitpunkte:", len(plot_time))
    print("Anzahl Geschwindigkeiten:", len(speeds))
    print("Anzahl Beschleunigungen:", len(accelerations))
    print("Anzahl Steigungen:", len(slopes))
    print("Anzahl Motorströme:", len(motor_currents))

    print(
        "Größte ungefilterte Beschleunigung:",
        np.max(np.abs(raw_accelerations)),
        "m/s²",
    )

    print(
        "Größte gefilterte Beschleunigung:",
        np.max(np.abs(accelerations)),
        "m/s²",
    )

    print("Maximale Kraft:", np.max(forces), "N")
    print("Maximale Leistung:", np.max(powers), "W")
    print("Maximales Drehmoment:", np.max(torques), "Nm")
    print("Maximaler Motorstrom:", np.max(motor_currents), "A")

    # --------------------------------------------------
    # Akkusimulation
    # --------------------------------------------------

    lipo = LiPoBatteryPack(
        capacity_nom_Ah=50.0,
        internal_resistance_mOhm=80.0,
        initial_soc=1.0,
        Vmin=32.0,
        Vmax=42.0,
    )

    nmc = NMCBatteryPack(
        capacity_nom_Ah=50.0,
        internal_resistance_mOhm=70.0,
        initial_soc=1.0,
        Vmin=32.0,
        Vmax=42.0,
    )

    v_lipo = []
    v_nmc = []

    # Motorstrom für jedes Zeitintervall auf beide Akkus anwenden
    for current, duration in zip(
        motor_currents,
        zeitdeltas,
    ):
        lipo.apply_current(
            current=current,
            duration=duration,
        )

        v_lipo.append(
            lipo.voltage(current=current)
        )

        nmc.apply_current(
            current=current,
            duration=duration,
        )

        v_nmc.append(
            nmc.voltage(current=current)
        )

    # --------------------------------------------------
    # Routendaten plotten
    # --------------------------------------------------

    plotte(
        plot_time,
        raw_accelerations,
        titel="Ungefilterte Beschleunigung",
        x_label="Zeit",
        y_label="Beschleunigung [m/s²]",
    )

    plotte(
        plot_time,
        accelerations,
        titel="Gefilterte Beschleunigung",
        x_label="Zeit",
        y_label="Beschleunigung [m/s²]",
    )

    plotte(
        plot_time,
        speeds,
        titel="Gefilterte Geschwindigkeit",
        x_label="Zeit",
        y_label="Geschwindigkeit [m/s]",
    )

    plotte(
        plot_time,
        slope_in_degrees,
        titel="Gefilterte Steigung",
        x_label="Zeit",
        y_label="Steigung [°]",
    )

    plotte(
        zeit,
        total_dist,
        titel="Zurückgelegte Strecke",
        x_label="Zeit",
        y_label="Strecke [m]",
    )

    # --------------------------------------------------
    # Motordaten plotten
    # --------------------------------------------------

    plotte(
        plot_time,
        forces,
        titel="Benötigte Antriebskraft",
        x_label="Zeit",
        y_label="Kraft [N]",
    )

    plotte(
        plot_time,
        powers,
        titel="Mechanische Motorleistung",
        x_label="Zeit",
        y_label="Leistung [W]",
    )

    plotte(
        plot_time,
        torques,
        titel="Motordrehmoment",
        x_label="Zeit",
        y_label="Drehmoment [Nm]",
    )

    plotte(
        plot_time,
        motor_currents,
        titel="Motorstrom",
        x_label="Zeit",
        y_label="Strom [A]",
    )

    # --------------------------------------------------
    # Batteriespannungen plotten
    # --------------------------------------------------

    plotte(
        plot_time,
        v_lipo,
        titel="LiPo-Batteriespannung",
        x_label="Zeit",
        y_label="Spannung [V]",
    )

    plotte(
        plot_time,
        v_nmc,
        titel="NMC-Batteriespannung",
        x_label="Zeit",
        y_label="Spannung [V]",
    )


def plotte(
    x,
    y,
    titel="Plot",
    x_label="x",
    y_label="y",
):
    """Erstellt einen einfachen Plot."""

    if len(x) != len(y):
        raise ValueError(
            "Beide Arrays müssen gleich lang sein."
        )

    plt.plot(
        x,
        y,
        linestyle="-",
    )

    plt.title(titel)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()