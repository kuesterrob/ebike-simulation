import logging
from pathlib import Path

from src.bikesimulator import BikeSimulator
from src.plotter import (
    get_plot_options,
    show_result_figures,
)
from src.reporting.console import (
    get_metric_section_names,
    print_selected_metrics,
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
    GPS_FILE.parent
    / "ebike_simulation_report.pdf"
)



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


def main() -> int:
    """Startet die E-Bike-Simulation."""

    configure_logging()

    try:
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