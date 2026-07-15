from pathlib import Path

import matplotlib.pyplot as plt

from src.bikesimulator import BikeSimulator
from src.plotter import (
    create_result_figure,
    get_plot_names,
)


PROJECT_DIRECTORY = Path(__file__).resolve().parent

GPS_FILE = (
    PROJECT_DIRECTORY
    / "data"
    / "final_project_input_data.csv"
)


def print_metrics(metrics: dict) -> None:
    """Gibt die wichtigsten Ergebnisse aus."""

    print("\n--- Routendaten ---")

    print(
        f"Gesamtstrecke: "
        f"{metrics['total_distance_km']:.2f} km"
    )

    print(
        f"Fahrzeit: "
        f"{metrics['duration_minutes']:.1f} min"
    )

    print(
        f"Durchschnittsgeschwindigkeit: "
        f"{metrics['average_speed_kmh']:.1f} km/h"
    )

    print(
        f"Maximale Geschwindigkeit: "
        f"{metrics['max_speed_kmh']:.1f} km/h"
    )

    print(
        f"Aufstieg: "
        f"{metrics['ascent_m']:.0f} m"
    )

    print(
        f"Abstieg: "
        f"{metrics['descent_m']:.0f} m"
    )

    print("\n--- Motor ---")

    print(
        f"Maximale Leistung: "
        f"{metrics['max_power_w']:.0f} W"
    )

    print(
        f"Maximaler Motorstrom: "
        f"{metrics['max_motor_current_a']:.1f} A"
    )

    print(
        f"Mechanische Energie: "
        f"{metrics['mechanical_energy_wh']:.1f} Wh"
    )

    print("\n--- Akkus ---")

    print(
        f"LiPo-Ladezustand: "
        f"{metrics['lipo_soc_percent']:.1f} %"
    )

    print(
        f"NMC-Ladezustand: "
        f"{metrics['nmc_soc_percent']:.1f} %"
    )

    print(
        f"Minimale LiPo-Spannung: "
        f"{metrics['min_lipo_voltage_v']:.2f} V"
    )

    print(
        f"Minimale NMC-Spannung: "
        f"{metrics['min_nmc_voltage_v']:.2f} V"
    )


def show_results(results: dict) -> None:
    """
    Zeigt alle vorhandenen Diagramme nacheinander an.
    """

    plot_names = get_plot_names(results)

    for plot_name in plot_names:
        figure = create_result_figure(
            results=results,
            plot_name=plot_name,
        )

        # Das Programm wartet, bis das aktuelle
        # Plot-Fenster geschlossen wurde.
        plt.show()

        # Figur anschließend aus dem Speicher entfernen.
        plt.close(figure)


def main() -> None:
    """Startet die E-Bike-Simulation."""

    print("E-Bike-Simulation wird gestartet ...")

    try:
        simulator = BikeSimulator(
            gps_file=GPS_FILE,
            battery_capacity_ah=50.0,
            initial_soc=1.0,
            filter_window=5,
        )

        results = simulator.run()

    except (FileNotFoundError, ValueError) as error:
        print(
            f"Simulation fehlgeschlagen: {error}"
        )
        return

    print("Simulation erfolgreich abgeschlossen.")

    print_metrics(results["metrics"])
    show_results(results)


if __name__ == "__main__":
    main()