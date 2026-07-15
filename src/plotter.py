import matplotlib.pyplot as plt


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
                "Gefiltert": (
                    route["acceleration_mps2"]
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

        "Zurückgelegte Strecke": {
            "x": time["all"],
            "series": {
                "Strecke": (
                    route["total_distance_m"]
                ),
            },
            "x_label": "Zeit",
            "y_label": "Strecke [m]",
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
                "Akkustrom": (
                    motor["battery_current_a"]
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