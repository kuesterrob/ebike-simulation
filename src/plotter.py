import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import logging

logger = logging.getLogger(__name__)

# Kurze Bezeichnungen für die Auswahl über die Kommandozeile.
PLOT_OPTIONS = {
    "speed": "Geschwindigkeit",
    "acceleration": "Beschleunigung",
    "slope": "Steigung",
    "air_density": "Luftdichte",
    "distance": "Zurückgelegte Strecke",
    "drive_force": "Antriebskraft",
    "motor_power": "Motorleistung",
    "torque": "Drehmoment",
    "motor_current": "Motorstrom",
    "battery_current": "Akkustrom",
    "battery_voltage": "Batteriespannung",
    "battery_temperature": "Akkutemperatur",
    "battery_power": "Akkuleistung",
    "battery_resistance": "Akku-Innenwiderstand",
    "braking_demand": "Bremsleistungsbedarf",
    "regeneration_power": "Rekuperationsleistung",
    "resistor_power": "Bremswiderstandsleistung",
    "resistor_temperature": (
        "Bremswiderstandstemperatur"
    ),
    "friction_brake_power": (
        "Mechanische Bremsleistung"
    ),
}

def get_plot_definitions(
    results: dict,
) -> dict:
    """
    Erstellt die Definitionen aller verfügbaren Plots.

    Hier wird festgelegt:

    - Welche x-Werte verwendet werden
    - Welche Datenreihen angezeigt werden
    - Welche Achsenbeschriftungen verwendet werden
    """

    time = results["time"]
    route = results["route"]
    motor = results["motor"]
    battery = results["battery"]
    environment = results["environment"]
    braking = results["braking"]

    return {
        "Geschwindigkeit": {
            "x": time["intervals"],
            "series": {
                "Geschwindigkeit": (
                    route["speed_mps"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Geschwindigkeit [m/s]",
        },

        "Beschleunigung": {
            "x": time["intervals"],
            "series": {
                "Ungefiltert": (
                    route["raw_acceleration_mps2"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Beschleunigung [m/s²]",
        },

        "Steigung": {
            "x": time["intervals"],
            "series": {
                "Steigung": (
                    route["slope_degrees"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Steigung [°]",
        },

                "Luftdichte": {
            # Die Luftdichte wurde für jeden Streckenabschnitt berechnet. Deshalb werden die Intervallzeiten verwendet.
            "x": time["intervals"],

            "series": {
                "Luftdichte": (
                    environment[
                        "air_density_kg_per_m3"
                    ]
                ),
            },

            "x_label": "Zeit",
            "y_label": "Luftdichte [kg/m³]",
        },

        "Zurückgelegte Strecke": {
            "x": time["all"],
            "series": {
                "Strecke": (
                    route["total_distance_m"] * (10 ** -3)
                ),
            },
            "x_label": "Zeit",
            "y_label": "Strecke [km]",
        },

        "Antriebskraft": {
            "x": time["intervals"],
            "series": {
                "Antriebskraft": (
                    motor["force_n"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Kraft [N]",
        },

        "Motorleistung": {
            "x": time["intervals"],
            "series": {
                "Motorleistung": (
                    motor["power_w"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Leistung [W]",
        },

        "Drehmoment": {
            "x": time["intervals"],
            "series": {
                "Drehmoment": (
                    motor["torque_nm"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Drehmoment [Nm]",
        },

        "Motorstrom": {
            "x": time["intervals"],
            "series": {
                "Motorstrom": (
                    motor["current_a"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Strom [A]",
        },

        "Akkustrom": {
            "x": time["intervals"],
            "series": {
                "LiPo": (
                    battery["lipo_current_a"]
                ),
                "NMC": (
                    battery["nmc_current_a"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Strom [A]",
        },

        "Batteriespannung": {
            "x": time["intervals"],
            "series": {
                "LiPo": (
                    battery["lipo_voltage_v"]
                ),
                "NMC": (
                    battery["nmc_voltage_v"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Spannung [V]",
        },
                "Akkutemperatur": {
            "x": time["intervals"],
            "series": {
                "LiPo": (
                    battery[
                        "lipo_temperature_c"
                    ]
                ),
                "NMC": (
                    battery[
                        "nmc_temperature_c"
                    ]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Temperatur [°C]",
        },
                "Akkuleistung": {
            "x": time["intervals"],
            "series": {
                "LiPo": (
                    battery["lipo_power_w"]
                ),
                "NMC": (
                    battery["nmc_power_w"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Leistung [W]",
        },
                "Akku-Innenwiderstand": {
            "x": time["intervals"],
            "series": {
                "LiPo": (
                    battery[
                        "lipo_internal_resistance_ohm"
                    ]
                    * 1000.0
                ),
                "NMC": (
                    battery[
                        "nmc_internal_resistance_ohm"
                    ]
                    * 1000.0
                ),
            },
            "x_label": "Zeit",
            "y_label": "Innenwiderstand [mΩ]",
        },

        "Bremsleistungsbedarf": {
            "x": time["intervals"],
            "series": {
                "Mechanischer Bremsbedarf": (
                    motor["braking_power_w"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Leistung [W]",
        },

        "Rekuperationsleistung": {
            "x": time["intervals"],
            "series": {
                "LiPo-Akku": (
                    braking["lipo_charge_power_w"]
                ),
                "NMC-Akku": (
                    braking["nmc_charge_power_w"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Ladeleistung [W]",
        },

        "Bremswiderstandsleistung": {
            "x": time["intervals"],
            "series": {
                "LiPo-Simulation": (
                    braking["lipo_resistor_power_w"]
                ),
                "NMC-Simulation": (
                    braking["nmc_resistor_power_w"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Leistung [W]",
        },

        "Bremswiderstandstemperatur": {
            "x": time["intervals"],
            "series": {
                "LiPo-Simulation": (
                    braking[
                        "lipo_resistor_temperature_c"
                    ]
                ),
                "NMC-Simulation": (
                    braking[
                        "nmc_resistor_temperature_c"
                    ]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Temperatur [°C]",
        },

        "Mechanische Bremsleistung": {
            "x": time["intervals"],
            "series": {
                "LiPo-Simulation": (
                    braking[
                        "lipo_friction_brake_power_w"
                    ]
                ),
                "NMC-Simulation": (
                    braking[
                        "nmc_friction_brake_power_w"
                    ]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Leistung [W]",
        },

    }


def get_plot_names(
    results: dict,
) -> list[str]:
    """Gibt die Namen aller verfügbaren Plots zurück."""

    plot_definitions = get_plot_definitions(
        results
    )

    return list(plot_definitions.keys())


def create_figure(
    x,
    series: dict,
    title: str,
    x_label: str,
    y_label: str,
):
    """
    Erstellt eine Matplotlib-Figur.
    """

    figure, axis = plt.subplots(
        figsize=(10, 5),
    )

    for series_name, values in series.items():
        if len(x) != len(values):
            raise ValueError(
                f"Die Datenreihe '{series_name}' "
                f"hat die Länge {len(values)}, "
                f"erwartet wurde {len(x)}."
            )

        axis.plot(
            x,
            values,
            linestyle="-",
            label=series_name,
        )

    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)
    axis.grid(True)
    axis.xaxis.set_major_locator(mdates.MinuteLocator(byminute=[0, 30]))
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    axis.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=[10, 20, 40, 50]))

    if len(series) > 1:
        axis.legend()

    figure.autofmt_xdate()
    figure.tight_layout()

    return figure


def create_result_figure(
    results: dict,
    plot_name: str,
):
    """
    Erzeugt eine bestimmte Ergebnisfigur anhand
    ihres Namens.
    """

    plot_definitions = get_plot_definitions(
        results
    )

    if plot_name not in plot_definitions:
        available_plots = ", ".join(
            plot_definitions.keys()
        )

        raise ValueError(
            f"Unbekannter Plot: '{plot_name}'. "
            f"Verfügbare Plots: {available_plots}"
        )

    plot_data = plot_definitions[plot_name]

    return create_figure(
        x=plot_data["x"],
        series=plot_data["series"],
        title=plot_name,
        x_label=plot_data["x_label"],
        y_label=plot_data["y_label"],
    )

def get_plot_options() -> dict[str, str]:
    """
    Gibt die verfügbaren Kurzbezeichnungen und
    die zugehörigen Plotnamen zurück.
    """

    return PLOT_OPTIONS.copy()


def show_result_figures(
    results: dict,
    selected_plot_ids: list[str],
) -> None:
    """
    Zeigt die ausgewählten Diagramme nacheinander an.
    """

    available_plot_names = set(
        get_plot_names(results)
    )

    logger.info(
        "Bereite %d Ergebnisdiagramme vor",
        len(selected_plot_ids),
    )

    for plot_id in selected_plot_ids:
        if plot_id not in PLOT_OPTIONS:
            available_ids = ", ".join(
                PLOT_OPTIONS.keys()
            )

            raise ValueError(
                f"Unbekannter Plot: '{plot_id}'. "
                f"Verfügbare Plots: {available_ids}"
            )

        plot_name = PLOT_OPTIONS[
            plot_id
        ]

        # Zusätzliche Prüfung, damit die Zuordnung  tatsächlich zu einer Plotdefinition gehört.
        if plot_name not in available_plot_names:
            raise ValueError(
                "Für den Plot "
                f"'{plot_id}' fehlt die Definition "
                f"'{plot_name}'."
            )

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
                "konnte nicht erstellt oder "
                "angezeigt werden."
            ) from error

        finally:
            if figure is not None:
                plt.close(figure)