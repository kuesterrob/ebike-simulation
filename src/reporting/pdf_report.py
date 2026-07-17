"""
Erstellung eines PDF-Berichts aus den
Simulationsergebnissen.
"""

from datetime import datetime
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from src.plotter import (
    create_result_figure,
    get_plot_options,
)
from src.reporting.console import (
    format_selected_metrics,
)


def add_page_number(
    canvas,
    document,
) -> None:
    """Fügt unten rechts eine Seitennummer ein."""

    canvas.saveState()

    canvas.setFont(
        "Helvetica",
        9,
    )

    canvas.setFillColor(
        colors.grey,
    )

    canvas.drawRightString(
        A4[0] - 1.5 * cm,
        1.0 * cm,
        f"Seite {document.page}",
    )

    canvas.restoreState()


def create_plot_image(
    results: dict,
    plot_id: str,
) -> tuple[Image, BytesIO]:
    """
    Erstellt aus einem vorhandenen Plot ein Bild,
    das in den PDF-Bericht eingefügt werden kann.
    """

    plot_options = get_plot_options()

    if plot_id not in plot_options:
        raise ValueError(
            f"Unbekannter Plot für PDF: '{plot_id}'"
        )

    plot_name = plot_options[plot_id]

    figure = create_result_figure(
        results=results,
        plot_name=plot_name,
    )

    image_buffer = BytesIO()

    try:
        # Der Plot wird nicht als Datei gespeichert,
        figure.savefig(
            image_buffer,
            format="png",
            dpi=160,
            bbox_inches="tight",
        )
    finally:
        plt.close(figure)

    image_buffer.seek(0)

    plot_image = Image(
        image_buffer,
    )

    # Das Seitenverhältnis des Diagramms bleibt erhalten.
    maximum_width = 17.5 * cm
    maximum_height = 12.0 * cm

    scale_factor = min(
        maximum_width / plot_image.imageWidth,
        maximum_height / plot_image.imageHeight,
    )

    plot_image.drawWidth = (
        plot_image.imageWidth * scale_factor
    )

    plot_image.drawHeight = (
        plot_image.imageHeight * scale_factor
    )

    return plot_image, image_buffer


def create_pdf_report(
    results: dict,
    selected_sections: list[str],
    selected_plot_ids: list[str],
    output_file: Path,
) -> Path:
    """
    Erstellt einen PDF-Bericht.

    Der Bericht enthält die ausgewählten
    Kennzahlengruppen und Diagramme.
    """

    # Der Ausgabeordner wird automatisch angelegt,
    # wenn er noch nicht vorhanden ist.
    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    document = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.8 * cm,
        title="E-Bike-Simulationsbericht",
        author="E-Bike-Simulation",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#244A64"),
        spaceAfter=14,
    )

    section_style = ParagraphStyle(
        name="ReportSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#244A64"),
        spaceBefore=12,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        name="ReportBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceAfter=4,
    )

    note_style = ParagraphStyle(
        name="ReportNote",
        parent=body_style,
        textColor=colors.grey,
    )

    story = []
    image_buffers = []

    story.append(
        Paragraph(
            "E-Bike-Simulationsbericht",
            title_style,
        )
    )

    creation_time = datetime.now().strftime(
        "%d.%m.%Y um %H:%M Uhr"
    )

    story.append(
        Paragraph(
            f"Erstellt am {creation_time}",
            note_style,
        )
    )

    story.append(
        Spacer(
            1,
            0.5 * cm,
        )
    )

    story.append(
        Paragraph(
            "Simulationsergebnisse",
            section_style,
        )
    )

    if selected_sections:
        metric_lines = format_selected_metrics(
            metrics=results["metrics"],
            selected_sections=selected_sections,
        )

        for line in metric_lines:
            if not line:
                story.append(
                    Spacer(
                        1,
                        0.2 * cm,
                    )
                )
                continue

            # Überschriften aus console.py erkennen.
            if (
                line.startswith("---")
                and line.endswith("---")
            ):
                heading = line.strip("- ").strip()

                story.append(
                    Paragraph(
                        escape(heading),
                        section_style,
                    )
                )
                continue

            # Bezeichnung und Wert optisch trennen.
            if ":" in line:
                label, value = line.split(
                    ":",
                    maxsplit=1,
                )

                formatted_line = (
                    f"<b>{escape(label.strip())}:</b> "
                    f"{escape(value.strip())}"
                )
            else:
                formatted_line = escape(line)

            story.append(
                Paragraph(
                    formatted_line,
                    body_style,
                )
            )
    else:
        story.append(
            Paragraph(
                "Es wurden keine Kennzahlen ausgewählt.",
                note_style,
            )
        )

    if not selected_plot_ids:
        story.append(
            Spacer(
                1,
                0.4 * cm,
            )
        )

        story.append(
            Paragraph(
                "Es wurden keine Diagramme ausgewählt.",
                note_style,
            )
        )

    try:
        # Jedes Diagramm erhält eine eigene PDF-Seite.
        for plot_id in selected_plot_ids:
            plot_options = get_plot_options()
            plot_name = plot_options[plot_id]

            plot_image, image_buffer = (
                create_plot_image(
                    results=results,
                    plot_id=plot_id,
                )
            )

            # Der Speicher muss bis zur vollständigen
            # Erstellung der PDF geöffnet bleiben.
            image_buffers.append(
                image_buffer
            )

            story.append(
                PageBreak()
            )

            story.append(
                Paragraph(
                    escape(plot_name),
                    section_style,
                )
            )

            story.append(
                Spacer(
                    1,
                    0.3 * cm,
                )
            )

            story.append(
                plot_image
            )

        document.build(
            story,
            onFirstPage=add_page_number,
            onLaterPages=add_page_number,
        )

    finally:
        for image_buffer in image_buffers:
            image_buffer.close()

    return output_file