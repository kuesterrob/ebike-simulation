"""
Formatierung und Ausgabe der Simulationsergebnisse
im Terminal.
"""


def format_route_metrics(
    metrics: dict,
) -> list[str]:
    """Formatiert die Kennzahlen der Route."""

    return [
        "--- Routendaten ---",
        (
            "Gesamtstrecke: "
            f"{metrics['total_distance_km']:.2f} km"
        ),
        (
            "Fahrzeit: "
            f"{metrics['duration_minutes']:.1f} min"
        ),
        (
            "Durchschnittsgeschwindigkeit: "
            f"{metrics['average_speed_kmh']:.1f} km/h"
        ),
        (
            "Maximale Geschwindigkeit: "
            f"{metrics['max_speed_kmh']:.1f} km/h"
        ),
        (
            "Aufstieg: "
            f"{metrics['ascent_m']:.0f} m"
        ),
        (
            "Abstieg: "
            f"{metrics['descent_m']:.0f} m"
        ),
    ]


def format_environment_metrics(
    metrics: dict,
) -> list[str]:
    """Formatiert die Umgebungskennzahlen."""

    return [
        "--- Umgebung ---",
        (
            "Durchschnittstemperatur: "
            f"{metrics['average_temperature_c']:.1f} °C"
        ),
        (
            "Temperaturbereich: "
            f"{metrics['min_temperature_c']:.1f} bis "
            f"{metrics['max_temperature_c']:.1f} °C"
        ),
        (
            "Durchschnittliche Luftdichte: "
            f"{metrics['average_air_density_kg_per_m3']:.3f} "
            "kg/m³"
        ),
        (
            "Luftdichtebereich: "
            f"{metrics['min_air_density_kg_per_m3']:.3f} bis "
            f"{metrics['max_air_density_kg_per_m3']:.3f} "
            "kg/m³"
        ),
    ]


def format_motor_metrics(
    metrics: dict,
) -> list[str]:
    """Formatiert die Motorkennzahlen."""

    return [
        "--- Motor ---",
        (
            "Rollwiderstandskoeffizient: "
            f"{metrics['rolling_resistance_coefficient']:.4f}"
        ),
        (
            "Durchschnittlicher Rollwiderstand: "
            f"{metrics['average_rolling_force_n']:.2f} N"
        ),
        (
            "Maximaler Rollwiderstand: "
            f"{metrics['max_rolling_force_n']:.2f} N"
        ),
        (
            "Maximale Leistung: "
            f"{metrics['max_power_w']:.0f} W"
        ),
        (
            "Maximaler Motorstrom: "
            f"{metrics['max_motor_current_a']:.1f} A"
        ),
        (
            "Mechanische Energie: "
            f"{metrics['mechanical_energy_wh']:.1f} Wh"
        ),
    ]


def format_battery_metrics(
    metrics: dict,
) -> list[str]:
    """Formatiert die Akkukennzahlen."""

    return [
        "--- Akkus ---",
        (
            "LiPo-Ladezustand: "
            f"{metrics['lipo_soc_percent']:.1f} %"
        ),
        (
            "NMC-Ladezustand: "
            f"{metrics['nmc_soc_percent']:.1f} %"
        ),
        (
            "Minimale LiPo-Spannung: "
            f"{metrics['min_lipo_voltage_v']:.2f} V"
        ),
        (
            "Minimale NMC-Spannung: "
            f"{metrics['min_nmc_voltage_v']:.2f} V"
        ),
        (
            "Akku-Anfangstemperatur: "
            f"{metrics['initial_battery_temperature_c']:.2f} °C"
        ),
        (
            "LiPo-Maximaltemperatur: "
            f"{metrics['max_lipo_temperature_c']:.2f} °C"
        ),
        (
            "NMC-Maximaltemperatur: "
            f"{metrics['max_nmc_temperature_c']:.2f} °C"
        ),
        (
            "LiPo-Endtemperatur: "
            f"{metrics['final_lipo_temperature_c']:.2f} °C"
        ),
        (
            "NMC-Endtemperatur: "
            f"{metrics['final_nmc_temperature_c']:.2f} °C"
        ),
        (
            "Maximale LiPo-Akkuleistung: "
            f"{metrics['max_lipo_battery_power_w']:.0f} W"
        ),
        (
            "Maximale NMC-Akkuleistung: "
            f"{metrics['max_nmc_battery_power_w']:.0f} W"
        ),
    ]


def format_regeneration_metrics(
    metrics: dict,
) -> list[str]:
    """Formatiert die Rekuperationskennzahlen."""

    return [
        "--- Rekuperation ---",
        (
            "Mechanische Bremsenergie: "
            f"{metrics['mechanical_braking_energy_wh']:.2f} Wh"
        ),
        (
            "Vom LiPo aufgenommene Energie: "
            f"{metrics['lipo_recovered_energy_wh']:.2f} Wh"
        ),
        (
            "Vom NMC aufgenommene Energie: "
            f"{metrics['nmc_recovered_energy_wh']:.2f} Wh"
        ),
        (
            "Im LiPo-Bremswiderstand dissipiert: "
            f"{metrics['lipo_resistor_energy_wh']:.2f} Wh"
        ),
        (
            "Im NMC-Bremswiderstand dissipiert: "
            f"{metrics['nmc_resistor_energy_wh']:.2f} Wh"
        ),
        (
            "Mechanische Bremsenergie bei LiPo: "
            f"{metrics['lipo_friction_brake_energy_wh']:.2f} Wh"
        ),
        (
            "Mechanische Bremsenergie bei NMC: "
            f"{metrics['nmc_friction_brake_energy_wh']:.2f} Wh"
        ),
        (
            "Maximale LiPo-Widerstandsleistung: "
            f"{metrics['max_lipo_resistor_power_w']:.2f} W"
        ),
        (
            "Maximale NMC-Widerstandsleistung: "
            f"{metrics['max_nmc_resistor_power_w']:.2f} W"
        ),
        (
            "Maximale LiPo-Widerstandstemperatur: "
            f"{metrics['max_lipo_resistor_temperature_c']:.2f} "
            "°C"
        ),
        (
            "Maximale NMC-Widerstandstemperatur: "
            f"{metrics['max_nmc_resistor_temperature_c']:.2f} "
            "°C"
        ),
    ]


# Zuordnung der Kommandozeilennamen zu den jeweiligen Formatierungsfunktionen.
METRIC_SECTION_FORMATTERS = {
    "route": format_route_metrics,
    "environment": format_environment_metrics,
    "motor": format_motor_metrics,
    "battery": format_battery_metrics,
    "regeneration": format_regeneration_metrics,
}


def get_metric_section_names() -> list[str]:
    """
    Gibt die Namen aller auswählbaren
    Kennzahlengruppen zurück.
    """

    return list(
        METRIC_SECTION_FORMATTERS.keys()
    )


def format_selected_metrics(
    metrics: dict,
    selected_sections: list[str],
) -> list[str]:
    """
    Formatiert die ausgewählten Kennzahlengruppen.

    Die Funktion gibt Textzeilen zurück, damit dieselbe
    Formatierung später auch für einen PDF-Bericht
    verwendet werden kann.
    """

    lines = []

    for section_name in selected_sections:
        if (
            section_name
            not in METRIC_SECTION_FORMATTERS
        ):
            available_sections = ", ".join(
                get_metric_section_names()
            )

            raise ValueError(
                "Unbekannte Kennzahlengruppe: "
                f"'{section_name}'. "
                "Verfügbare Gruppen: "
                f"{available_sections}"
            )

        formatter = METRIC_SECTION_FORMATTERS[
            section_name
        ]

        # Leerzeile zwischen den einzelnen Bereichen.
        lines.append("")

        lines.extend(
            formatter(metrics)
        )

    return lines


def print_selected_metrics(
    metrics: dict,
    selected_sections: list[str],
) -> None:
    """
    Gibt die ausgewählten Kennzahlengruppen
    im Terminal aus.
    """

    lines = format_selected_metrics(
        metrics=metrics,
        selected_sections=selected_sections,
    )

    for line in lines:
        print(line)

def print_vergleich(df: pd.DataFrame, spalte: str = "lipo_soc_percent") -> None:
    """Kompakte Konsolenausgabe pro Fall."""
    for name, r in df.iterrows():
        print(
            f"{name:<20} {r['kategorie']:<10} "
            f"{r[spalte]:6.2f} %  "
            f"Δ {r[f'{spalte}_delta_pp']:+7.2f} pp  "
            f"({r[f'{spalte}_delta_rel']:+7.1f} %)"
        )