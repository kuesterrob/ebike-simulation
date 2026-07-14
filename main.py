from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


from src.gps_reader import GPSReader
from src.route_calculator import RouteCalculator


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

    route_calculator = RouteCalculator()
    speeds = route_calculator.calculate_speed(zeitdeltas, distances)
    accelerations = route_calculator.calculate_acceleration(zeitdeltas, speeds)
    slopes = route_calculator.calculate_slope(distances, df["ele"].to_numpy())

    plotte(zeitdeltas, speeds, titel="Geschwindigkeit", x_label="Zeit", y_label="Geschwindigkeit [m/s]")
    plotte(zeitdeltas, accelerations, titel="Beschleunigung", x_label="Zeit", y_label="Beschleunigung [m/s²]")
    plotte(zeitdeltas, slopes, titel="Steigung", x_label="Zeit", y_label="Steigung [m/m]")

    plotte(zeit, total_dist)
    

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