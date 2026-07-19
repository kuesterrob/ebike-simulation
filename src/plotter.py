import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
import logging
from itertools import groupby
import numpy as np


logger = logging.getLogger(__name__)

# Kurze Bezeichnungen für die Auswahl über die Kommandozeile.
PLOT_OPTIONS = {
    "speed": "Geschwindigkeit",
    "acceleration": "Beschleunigung",
    "slope": "Steigung",
    "air_density": "Luftdichte",
    "distance": "Zurückgelegte Strecke",
    "wind_force": "Windkraft",
    "drive_force": "Antriebskraft",
    "motor_power": "Motorleistung",
    "torque": "Drehmoment",
    "motor_current": "Motorstrom",
    "battery_current": "Akkustrom",
    "battery_soc": "Batterie SoC",
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
#20 Farben für Geocoding plots für Leserlichkeit
STRONG_COLORS = [
    "#0067c2",  # blau
    "#3a521f",  # grün
    "#a33181",  # magenta
    "#856100",  # oliv
    "#60408f",  # violett
    "#008561",  # petrol
    "#7a3754",  # weinrot
    "#b83700",  # orange
    "#12524b",  # petrol
    "#c21d5f",  # weinrot
    "#1c4b7a",  # blau
    "#99001f",  # rot
    "#7a1dc2",  # violett
    "#667a12",  # grün
    "#b800ab",  # magenta
    "#2e8099",  # petrol
    "#b85c45",  # rot
    "#1c40b8",  # blau
    "#1b8500",  # laubgrün
    "#66412e",  # orange
]

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
        "Windkraft": {
            "x": time["intervals"],
            "series": {
                "Windkraft": (
                    motor["wind_force_n"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Kraft [N]",
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

        "Batterie SoC": {
            "x": time["intervals"],
            "series": {
                "LiPo": (
                    battery["lipo_soc_list"]
                ),
                "NMC": (
                    battery["nmc_soc_list"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "SoC [%]",
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

def _cut(data, start, stop=None):
    """Positionsbasierter Zugriff, auch für pandas-Objekte mit eigenem Index."""
    data = getattr(data, "iloc", data)
    return data[start] if stop is None else data[start:stop]


def _segments(places):
    """Zusammenhängende Blöcke gleichen Ortsnamens als (name, i0, i1)."""
    i = 0
    for name, group in groupby(places):
        n = len(list(group))
        yield name, i, i + n
        i += n


def create_figure_route(
    x,
    series: dict,
    title: str,
    x_label: str,
    y_label: str,
    places=np.array,
    label_min: int = 8,
    rotation: int = 60,
):
    """
    Erstellt eine Matplotlib-Figur.

    places: optionale Ortsnamen (gleiche Länge wie x). Färbt die Kurve je
            Ort ein und beschriftet Segmente ab label_min Punkten schräg.
    """

    figure, axis = plt.subplots(
        figsize=(10, 5),
    )

    if places is not None and len(places) != len(x):
        raise ValueError(
            f"'places' hat die Länge {len(places)}, "
            f"erwartet wurde {len(x)}."
        )

    colors = (
        {
            name: STRONG_COLORS[i % len(STRONG_COLORS)]
            for i, name in enumerate(dict.fromkeys(places))
        }
        if places is not None
        else {}
    )

    for series_name, values in series.items():
        if len(x) != len(values):
            raise ValueError(
                f"Die Datenreihe '{series_name}' "
                f"hat die Länge {len(values)}, "
                f"erwartet wurde {len(x)}."
            )

        if places is not None:
            axis.legend(
                handles=[Line2D([], [], color=c, lw=3, label=n)
                     for n, c in colors.items()],
                loc="upper left",
                fontsize=7,
                ncol=2,
                frameon=False,
        )
        elif len(series) > 1:
            axis.legend()

        gesetzt = 0
        for name, i0, i1 in _segments(places):
            end = min(i1 + 1, len(x))  # Überlappung, sonst Lücken
            axis.plot(
                _cut(x, i0, end),
                _cut(values, i0, end),
                linestyle="-",
                color=colors[name],
            )

            if i1 - i0 >= label_min:
                mid = (i0 + i1 - 1) // 2 
                oben = gesetzt % 2 == 0      # abwechselnd über/unter der Kurve
                gesetzt += 1
                axis.annotate(
                    name,
                    (_cut(x, mid), _cut(values, mid)),
                    textcoords="offset points",
                    xytext=(4, 4),
                    rotation=rotation,
                    rotation_mode="anchor",
                    ha="left" if oben else "right",
                    va="bottom" if oben else "top",
                    fontsize=8,
                    fontweight="bold",
                    color=colors[name],
                )

    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)
    axis.grid(True)
    axis.xaxis.set_major_locator(mdates.MinuteLocator(byminute=[0, 30]))
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    axis.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=[10, 20, 40, 50]))
    

    if len(series) > 1 and places is None:
        axis.legend()

    figure.autofmt_xdate()
    figure.tight_layout()

    return figure
    

def create_result_figure(
    results: dict,
    plot_name: str,
    places: np.ndarray
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

    if plot_name == "Zurückgelegte Strecke":    #Extra Plot für gesamtstreck um Geocoding Daten zu inkludieren
        return create_figure_route( 
        x=plot_data["x"],
        series=plot_data["series"],
        title=plot_name,
        x_label=plot_data["x_label"],
        y_label=plot_data["y_label"],
        places = places,
    )
    else:
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
    places = results["places"]

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
                places = places
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