from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


from src.gps_reader import GPSReader
from src.route_calculator import RouteCalculator
from src.motor import Motor


PROJECT_DIRECTORY = Path(__file__).resolve().parent
GPS_FILE = (
    PROJECT_DIRECTORY
    / "data"
    / "final_project_input_data.csv"
)


def main() -> None:
    reader = GPSReader()

    df = reader.load_file(GPS_FILE)
    
    distances = reader.calculate_distances()

    zeit = df["time"].to_numpy(dtype="datetime64[ms]")
    zeitdeltas = df["time"].diff().dt.total_seconds().to_numpy()

    print(len(distances))
    print(len(zeit))

    total_dist = np.array([0])

    for x in distances:
        total_dist = np.append(total_dist, total_dist[-1] + x)

    zeitdeltas = df["time"].diff().dt.total_seconds().to_numpy()

    print(zeitdeltas)
    
    # Geschwindigkeit, Beschleunigung und Steigung berechnen
    route_calculator = RouteCalculator()
    speeds = route_calculator.calculate_speed(zeitdeltas, distances)
    accelerations = route_calculator.calculate_acceleration(zeitdeltas, speeds)
    slopes = route_calculator.calculate_slope(distances, df["ele"].to_numpy())

    print(speeds)
    print(accelerations)
    print(len(slopes))

    # Erstes Element entfernen, damit alle Arrays gleich lang sind
    zeitdeltas = zeitdeltas[1:]
    speeds = speeds[1:]
    accelerations = accelerations[1:]

    # Steigung nur für die Darstellung in Grad umrechnen
    slope_in_deegrees = np.degrees(np.arctan(slopes))

    # Motorberechnung durchführen
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

    # Ergebnisse zur Kontrolle ausgeben
    print("Anzahl Geschwindigkeiten:", len(speeds))
    print("Anzahl Steigungen:", len(slopes))
    print("Anzahl Motorergebnisse:", len(forces))

    print("Maximale Kraft:", np.max(forces), "N")
    print("Maximale Leistung:", np.max(powers), "W")
    print("Maximales Drehmoment:", np.max(torques), "Nm")
    print("Maximaler Motorstrom:", np.max(motor_currents), "A")

    
    #Plotten der Ergebnisse 
    plotte(zeitdeltas, speeds, titel="Geschwindigkeit", x_label="Zeit", y_label="Geschwindigkeit [m/s]")
    plotte(zeitdeltas, accelerations, titel="Beschleunigung", x_label="Zeit", y_label="Beschleunigung [m/s²]")
    plotte(zeitdeltas, slope_in_deegrees, titel="Steigung", x_label="Zeit", y_label="Steigung [°]")

    plotte(zeit, total_dist)

    plotte(
        zeit[1:],
        forces,
        titel="Benötigte Antriebskraft",
        x_label="Zeit",
        y_label="Kraft [N]",
    )

    plotte(
        zeit[1:],
        powers,
        titel="Mechanische Motorleistung",
        x_label="Zeit",
        y_label="Leistung [W]",
    )

    plotte(
        zeit[1:],
        torques,
        titel="Motordrehmoment",
        x_label="Zeit",
        y_label="Drehmoment [Nm]",
    )

    plotte(
        zeit[1:],
        motor_currents,
        titel="Motorstrom",
        x_label="Zeit",
        y_label="Strom [A]",
    )

    plotte(
        zeit,
        total_dist,
        titel="Zurückgelegte Strecke",
        x_label="Zeit",
        y_label="Strecke [m]",
    )





    

def plotte(x, y, titel="Plot", x_label="x", y_label="y"):
    if len(x) != len(y):
        raise ValueError("Beide Arrays müssen gleich lang sein.")

    plt.plot(x, y, marker="o", linestyle="-")
    plt.title(titel)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(True)
    plt.show()





if __name__ == "__main__":
    main()