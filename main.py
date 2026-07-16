import logging
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


logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Konfiguriert das Logging in der Konsole."""

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
        ],
    )


def print_metrics(
    metrics: dict,
) -> None:
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

    print("\n--- Umgebung ---")

    print(
        f"Durchschnittstemperatur: "
        f"{metrics['average_temperature_c']:.1f} °C"
    )

    print(
        f"Temperaturbereich: "
        f"{metrics['min_temperature_c']:.1f} bis "
        f"{metrics['max_temperature_c']:.1f} °C"
    )

    print(
        f"Durchschnittliche Luftdichte: "
        f"{metrics['average_air_density_kg_per_m3']:.3f} kg/m³"
    )

    print(
        f"Luftdichtebereich: "
        f"{metrics['min_air_density_kg_per_m3']:.3f} bis "
        f"{metrics['max_air_density_kg_per_m3']:.3f} kg/m³"
    )

    print("\n--- Motor ---")

    print(
        f"Rollwiderstandskoeffizient: "
        f"{metrics['rolling_resistance_coefficient']:.4f}"
    )

    print(
        f"Durchschnittlicher Rollwiderstand: "
        f"{metrics['average_rolling_force_n']:.2f} N"
    )

    print(
        f"Maximaler Rollwiderstand: "
        f"{metrics['max_rolling_force_n']:.2f} N"
    )

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
    # Anfangstemperatur des Akkus aus dem erstenTemperaturwert der CSV-Datei.
    print(
        f"Akku-Anfangstemperatur: "
        f"{metrics['initial_battery_temperature_c']:.2f} °C"
    )

    # Höchste berechnete Akkutemperaturen während der Fahrt.
    print(
        f"LiPo-Maximaltemperatur: "
        f"{metrics['max_lipo_temperature_c']:.2f} °C"
    )

    print(
        f"NMC-Maximaltemperatur: "
        f"{metrics['max_nmc_temperature_c']:.2f} °C"
    )

    # Akkutemperaturen am Ende der Fahrt.
    print(
        f"LiPo-Endtemperatur: "
        f"{metrics['final_lipo_temperature_c']:.2f} °C"
    )

    print(
        f"NMC-Endtemperatur: "
        f"{metrics['final_nmc_temperature_c']:.2f} °C"
    )


def show_results(
    results: dict,
) -> None:
    """Zeigt alle vorhandenen Diagramme nacheinander an."""

    plot_names = get_plot_names(
        results
    )

    logger.info(
        "Bereite %d Ergebnisdiagramme vor",
        len(plot_names),
    )

    for plot_name in plot_names:
        figure = None
        
        try:
            logger.info(
                "Zeige Diagramm: %s",
                plot_name,
            )

            figure = create_result_figure(
                results=results,
                plot_name=plot_name,
            )
            

            plt.show()

        except Exception as error:
            raise RuntimeError(
                f"Das Diagramm '{plot_name}' "
                f"konnte nicht erstellt oder "
                f"angezeigt werden."
            ) from error

        finally:
            if figure is not None:
                plt.close(figure)


def main() -> int:
    """
    Startet die E-Bike-Simulation.
    """

    configure_logging()

    logger.info(
        "E-Bike-Simulation gestartet"
    )

    logger.info(
        "Verwendete GPS-Datei: %s",
        GPS_FILE,
    )

    try:
        simulator = BikeSimulator(
            gps_file=GPS_FILE,
            battery_capacity_ah=50.0,
            initial_soc=1.0,
            filter_window=5,
        )

        logger.info(
            "BikeSimulator wurde initialisiert"
        )

        results = simulator.run()

        logger.info(
            "Simulation erfolgreich abgeschlossen"
        )

        print_metrics(
            results["metrics"]
        )

        show_results(results)

    except FileNotFoundError as error:
        logger.error(
            "Benötigte Datei wurde nicht gefunden: %s",
            error,
        )

        return 1

    except ValueError as error:
        logger.error(
            "Ungültige Simulationsdaten: %s",
            error,
        )

        return 1

    except KeyboardInterrupt:
        logger.warning(
            "Simulation wurde durch den Benutzer abgebrochen"
        )

        return 130

    except Exception:
        # logger.exception gibt zusätzlich den vollständigen Traceback des unbekannten Fehlers aus.
        logger.exception(
            "Unerwarteter Programmfehler"
        )

        return 1

    logger.info(
        "Anwendung erfolgreich beendet"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )