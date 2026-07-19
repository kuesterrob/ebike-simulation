import logging
from pathlib import Path
from itertools import product
import pandas as pd

from src.bikesimulator import BikeSimulator
from src.plotter import (
    get_plot_options,
    show_result_figures,
)
from src.reporting.console import (
    get_metric_section_names,
    print_selected_metrics,
    print_vergleich,
)
from src.reporting.pdf_report import (
    create_pdf_report,
)


PROJECT_DIRECTORY = Path(__file__).resolve().parent

GPS_FILE = (
    PROJECT_DIRECTORY
    / "data"
    / "final_project_input_data.csv"
)

PDF_REPORT_FILE = (
    GPS_FILE.parent.parent
    / "outputs/ebike_simulation_report.pdf"
)

PARAMETERS = (
    ("rider_mass_kg", "Fahrergewicht", 70.0, "kg"),
    ("bike_mass_kg", "Fahrradgewicht", 10.0, "kg"),
    ("drag_area_m2", "Effektive Stirnfläche (cw·A)", 0.5625, "m²"),
    ("wheel_diameter_inch", "Raddurchmesser", 27.0, "Zoll"),
    ("motor_constant_nm_per_a", "Motorkonstante", 1.5, "Nm/A"),
    ("rolling_resistance_coefficient", "Rollwiderstandsbeiwert", 0.0077, ""),
)

DEFAULTS = {name: default for name, _, default, _ in PARAMETERS}

CASES = {
    "basis":              ("Referenz",   {}),
    "pendler":            ("Archetyp",   dict(rider_mass_kg=80, bike_mass_kg=22, drag_area_m2=0.60, wheel_diameter_inch=28, motor_constant_nm_per_a=1.5, rolling_resistance_coefficient=0.0070)),
    "lastenrad":          ("Archetyp",   dict(rider_mass_kg=80, bike_mass_kg=45, drag_area_m2=0.75, wheel_diameter_inch=20, motor_constant_nm_per_a=2.2, rolling_resistance_coefficient=0.0090)),
    "sportlich":          ("Archetyp",   dict(rider_mass_kg=70, bike_mass_kg=14, drag_area_m2=0.38, wheel_diameter_inch=28, motor_constant_nm_per_a=1.2, rolling_resistance_coefficient=0.0040)),
    "mtb_gelände":       ("Archetyp",   dict(rider_mass_kg=85, bike_mass_kg=24, drag_area_m2=0.65, wheel_diameter_inch=27.5, motor_constant_nm_per_a=1.8, rolling_resistance_coefficient=0.0140)),
    "masse_leicht":       ("Masse",      dict(rider_mass_kg=55)),
    "masse_schwer":       ("Masse",      dict(rider_mass_kg=100)),
    "masse_zuladung":     ("Masse",      dict(bike_mass_kg=25)),
    "cda_tief":           ("CdA",        dict(drag_area_m2=0.35)),
    "cda_aufrecht":       ("CdA",        dict(drag_area_m2=0.70)),
    "cda_beladen":        ("CdA",        dict(drag_area_m2=0.85)),
    "crr_rennreifen":     ("Crr",        dict(rolling_resistance_coefficient=0.0030)),
    "crr_tourenreifen":   ("Crr",        dict(rolling_resistance_coefficient=0.0090)),
    "crr_stollen":        ("Crr",        dict(rolling_resistance_coefficient=0.0150)),
    "antrieb_schnell":    ("Antrieb",    dict(motor_constant_nm_per_a=1.0, wheel_diameter_inch=29)),
    "antrieb_ausgewogen": ("Antrieb",    dict(motor_constant_nm_per_a=1.5, wheel_diameter_inch=26)),
    "antrieb_drehmoment": ("Antrieb",    dict(motor_constant_nm_per_a=2.5, wheel_diameter_inch=20)),
    "best_case":          ("Grenzfall",  dict(rider_mass_kg=55, bike_mass_kg=12, drag_area_m2=0.35, wheel_diameter_inch=28, motor_constant_nm_per_a=1.2, rolling_resistance_coefficient=0.0030)),
    "worst_case":         ("Grenzfall",  dict(rider_mass_kg=110, bike_mass_kg=30, drag_area_m2=0.85, wheel_diameter_inch=26, motor_constant_nm_per_a=1.5, rolling_resistance_coefficient=0.0150)),
    "auslegungsgrenze":   ("Grenzfall",  dict(rider_mass_kg=110, bike_mass_kg=45, drag_area_m2=0.75, wheel_diameter_inch=20, motor_constant_nm_per_a=2.5, rolling_resistance_coefficient=0.0140)),
}

logger = logging.getLogger(__name__)

class UserCancelledError(Exception):
    """Wird ausgelöst, wenn der Benutzer das Menü abbricht."""


# Bezeichnungen für die Auswahl der Terminalausgaben.
METRIC_LABELS = {
    "route": "Route und Fahrdaten",
    "environment": "Umgebungsdaten",
    "motor": "Motor und Antrieb",
    "battery": "Akkudaten",
    "regeneration": "Rekuperation und Bremsen",
}


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


def get_metric_options() -> dict[str, str]:
    """
    Erstellt die auswählbaren Kennzahlengruppen.
    """

    return {
        metric_name: METRIC_LABELS.get(
            metric_name,
            metric_name,
        )
        for metric_name in get_metric_section_names()
    }


def select_items(
    title: str,
    options: dict[str, str],
) -> list[str]:
    """
    Zeigt ein interaktives Auswahlmenü im Terminal.
    """

    option_ids = list(options.keys())

    while True:
        print()
        print(title)
        print("-" * len(title))

        # Alle verfügbaren Einträge nummeriert anzeigen.
        for number, option_id in enumerate(
            option_ids,
            start=1,
        ):
            print(
                f"{number}: {options[option_id]}"
            )

        print("a: Alle auswählen")
        print("0: Keine auswählen")
        print("q: Programm abbrechen")

        user_input = input(
            "Auswahl eingeben "
            "(zum Beispiel 1,3, a, 0 oder q): "
        ).strip().lower()

        # Alle Einträge auswählen.
        if user_input in {"a", "alle"}:
            return option_ids.copy()
        
        # Das vollständige Programm aus jedem Menü heraus abbrechen.
        if user_input in {"q", "quit", "abbrechen"}:
            raise UserCancelledError

        # Keine Einträge auswählen.
        if user_input in {"0", "keine"}:
            return []

        # Kommas durch Leerzeichen ersetzen. Dadurch funktionieren sowohl 1,3 als auch 1 3
        entered_values = (
            user_input
            .replace(",", " ")
            .split()
        )

        if not entered_values:
            print(
                "Keine gültige Auswahl eingegeben. "
                "Bitte erneut versuchen."
            )
            continue

        # Prüfen, ob wirklich nur Zahlen eingegeben wurden.
        if not all(
            value.isdigit()
            for value in entered_values
        ):
            print(
                "Ungültige Eingabe. Bitte Zahlen, "
                "'a' oder '0' verwenden."
            )
            continue

        selected_numbers = [
            int(value)
            for value in entered_values
        ]

        # Prüfen, ob alle Zahlen zu einem vorhandenen Menüpunkt gehören.
        if any(
            number < 1
            or number > len(option_ids)
            for number in selected_numbers
        ):
            print(
                "Mindestens eine Zahl liegt "
                "außerhalb des gültigen Bereichs."
            )
            continue

        selected_ids = []

        for number in selected_numbers:
            option_id = option_ids[number - 1]

            # Doppelte Auswahlen vermeiden.
            if option_id not in selected_ids:
                selected_ids.append(option_id)

        return selected_ids
    
def ask_yes_no(
    question: str,
) -> bool:
    """
    Fragt im Terminal eine Ja-Nein-Entscheidung ab.
    """

    while True:
        user_input = input(
            f"{question} (j/n/q): "
        ).strip().lower()

        if user_input in {"j", "ja"}:
            return True

        if user_input in {"n", "nein"}:
            return False

        if user_input in {
            "q",
            "quit",
            "abbrechen",
        }:
            raise UserCancelledError

        print(
            "Ungültige Eingabe. Bitte j, n oder q "
            "eingeben."
        )

def ask_float(label: str, default: float, unit: str = "") -> float:
    """Fragt einen Zahlenwert ab. Leere Eingabe übernimmt den Standardwert."""
    suffix = f" {unit}" if unit else ""
    eingabe = input(f"{label} [{default}{suffix}]: ").strip()

    if not eingabe:
        return default

    try:
        wert = float(eingabe.replace(",", "."))
    except ValueError:
        raise ValueError(f"Ungültige Zahl für {label!r}: {eingabe!r}") from None

    if wert <= 0:
        raise ValueError(f"{label} muss positiv sein, war: {wert}")

    return wert

def ask_parameters() -> dict[str, float]:
    """Fragt alle Simulationsparameter ab, optional komplett mit Standardwerten."""
    antwort = input(
        "Standardwerte für alle Parameter verwenden? [J/n]: "
    ).strip().lower()

    if antwort in ("", "j", "ja", "y", "yes"):
        return {name: default for name, _, default, _ in PARAMETERS}

    print("\nEnter drücken übernimmt den jeweiligen Standardwert.\n")
    return {
        name: ask_float(label, default, unit)
        for name, label, default, unit in PARAMETERS
    }

def run_study(cases=CASES) -> pd.DataFrame:
    rows = []
    for name, (kategorie, abweichungen) in cases.items():
        if set(abweichungen) - set(DEFAULTS):
            raise ValueError(f"Unbekannte Parameter in {name!r}")
        p = {**DEFAULTS, **abweichungen}
        simulator = BikeSimulator(
                gps_file=GPS_FILE,
                battery_capacity_ah=50.0,
                initial_soc=1.0,
                filter_window=5,
                rider_mass_kg=p["rider_mass_kg"],
                bike_mass_kg=p["bike_mass_kg"],
                drag_area_m2=p["drag_area_m2"],
                wheel_diameter_inch=p["wheel_diameter_inch"],
                motor_constant_nm_per_a=p["motor_constant_nm_per_a"],
                rolling_resistance_coefficient=p["rolling_resistance_coefficient"],
        )
        logger.info(
                "BikeSimulator wurde initialisiert"
            )

        results = simulator.run()
        
        rows.append({
            "name": name,
            "kategorie": kategorie,
            "lipo_soc_percent": results["battery"]["lipo_soc_percent"],
            "nmc_soc_percent": results["battery"]["nmc_soc_percent"],
        })
        logger.info(
            "Simulation erfolgreich abgeschlossen"
        )
    return pd.DataFrame(rows).set_index("name")

def add_basis_vergleich(df: pd.DataFrame, basis: str = "basis") -> pd.DataFrame:
    b = df.loc[basis]
    out = df.copy()
    for spalte in ["lipo_soc_percent", "nmc_soc_percent"]:
        out[f"{spalte}_delta_pp"] = out[spalte] - b[spalte]
        out[f"{spalte}_delta_rel"] = (out[spalte] - b[spalte]) / b[spalte] * 100
    return out


def main() -> int:
    """Startet die E-Bike-Simulation."""

    configure_logging()

    parameter_or_concrete = input(
        "Möchtest du eine Parameterstudie durchführen "
        "oder mit bestimmten Werten simulieren?\n"
        "  [1] Parameterstudie\n"
        "  [2] Konkrete Werte\n"
        "Auswahl (1-2): "
        ).strip()
    
    if parameter_or_concrete not in ("1", "2"):
        raise ValueError(f"Ungültige Auswahl: {parameter_or_concrete!r}")
    
    if parameter_or_concrete == "1":
        try:
            #Simuliert werden 20 phsikalisch sinnvolle Parametersätze

            logger.info(
                "E-Bike-Simulation gestartet"
            )

            df = run_study()
            df = add_basis_vergleich(df)
            print_vergleich(df)

        except UserCancelledError:
            print()
            print("Programm wurde abgebrochen.")
            return 0

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
            print()

            logger.warning(
                "Simulation wurde durch den Benutzer "
                "abgebrochen"
            )
            return 130

        except Exception:
            logger.exception(
                "Unerwarteter Programmfehler"
            )
            return 1

        logger.info(
            "Anwendung erfolgreich beendet"
        )

        return 0
    
    if parameter_or_concrete == "2":
        try:
            params = ask_parameters()

            # Zuerst auswählen, welche Ergebnisse später im Terminal ausgegeben werden sollen.
            metric_sections = select_items(
                title=(
                    "Welche Ergebnisse möchtest du "
                    "im Terminal ausgeben?"
                ),
                options=get_metric_options(),
            )

            # Anschließend auswählen, welche Diagrammenach der Simulation angezeigt werden sollen.
            plot_ids = select_items(
                title=(
                    "Welche Diagramme möchtest du "
                    "anzeigen?"
                ),
                options=get_plot_options(),
            )

            create_report = ask_yes_no(
                "Möchtest du aus dieser Auswahl "
                "einen PDF-Bericht erstellen?"
            )

            logger.info(
                "E-Bike-Simulation gestartet"
            )

            logger.info(
                "Verwendete GPS-Datei: %s",
                GPS_FILE,
            )

            simulator = BikeSimulator(
                gps_file=GPS_FILE,
                battery_capacity_ah=50.0,
                initial_soc=1.0,
                filter_window=5,
                rider_mass_kg=params["rider_mass_kg"],
                bike_mass_kg=params["bike_mass_kg"],
                drag_area_m2=params["drag_area_m2"],
                wheel_diameter_inch=params["wheel_diameter_inch"],
                motor_constant_nm_per_a=params["motor_constant_nm_per_a"],
                rolling_resistance_coefficient=params["rolling_resistance_coefficient"],
            )

            logger.info(
                "BikeSimulator wurde initialisiert"
            )

            results = simulator.run()

            logger.info(
                "Simulation erfolgreich abgeschlossen"
            )

            # Nur die ausgewählten Ergebnisgruppen im Terminal ausgeben.
            if metric_sections:
                print_selected_metrics(
                    metrics=results["metrics"],
                    selected_sections=metric_sections,
                )

            # PDF vor der Anzeige der Diagrammfenster erstellen.
        
            if create_report:
                created_report = create_pdf_report(
                    results=results,
                    selected_sections=metric_sections,
                    selected_plot_ids=plot_ids,
                    output_file=PDF_REPORT_FILE,
                )

                print()
                print(
                    "PDF-Bericht wurde erstellt:"
                )
                print(
                    created_report.resolve()
                )

            # Erst danach die ausgewählten Diagramme anzeigen.
            if plot_ids:
                show_result_figures(
                    results=results,
                    selected_plot_ids=plot_ids,
                )
    
        except UserCancelledError:
            print()
            print("Programm wurde abgebrochen.")
            return 0

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
            print()

            logger.warning(
                "Simulation wurde durch den Benutzer "
                "abgebrochen"
            )
            return 130

        except Exception:
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