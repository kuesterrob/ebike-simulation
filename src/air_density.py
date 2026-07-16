import numpy as np

def calculate_air_density(
    temperatures_c: np.ndarray,
    altitudes_m: np.ndarray,
) -> np.ndarray:
    """
    Berechnet die Luftdichte aus Temperatur und Höhe
    für mehrere Streckenabschnitte.
    """

    temperatures_c = np.asarray(
        temperatures_c,
        dtype=float,
    )

    altitudes_m = np.asarray(
        altitudes_m,
        dtype=float,
    )

    # Für jeden Streckenabschnitt müssen sowohl eine Temperatur
    # als auch eine Höhe vorhanden sein.
    if len(temperatures_c) != len(altitudes_m):
        raise ValueError(
            "Temperaturen und Höhen müssen gleich "
            "viele Werte enthalten."
        )

    # NaN- und Unendlich-Werte würden zu ungültigen Ergebnissen bei der Luftdichte führen.
    if not (
        np.all(np.isfinite(temperatures_c))
        and np.all(np.isfinite(altitudes_m))
    ):
        raise ValueError(
            "Temperaturen und Höhen müssen gültige "
            "Zahlen enthalten."
        )

    # Der absolute Nullpunkt ist die niedrigste physikalisch mögliche Temperatur.
    if np.any(temperatures_c <= -273.15):
        raise ValueError(
            "Die Temperaturen müssen über -273,15 °C liegen."
        )

    # Konstanten der Standardatmosphäre.
    sea_level_pressure_pa = 101_325.0
    sea_level_temperature_k = 288.15
    temperature_gradient_k_per_m = 0.0065
    gravity_m_per_s2 = 9.80665
    specific_gas_constant = 287.05

    # Mit zunehmender Höhe nimmt der Luftdruck ab, weil sich weniger Luft über dem betrachteten Punkt befindet.
    pressure_exponent = (
        gravity_m_per_s2
        / (
            specific_gas_constant
            * temperature_gradient_k_per_m
        )
    )

    pressure_pa = sea_level_pressure_pa * (
        1.0
        - (
            temperature_gradient_k_per_m
            * altitudes_m
            / sea_level_temperature_k
        )
    ) ** pressure_exponent

    # Die ideale Gasgleichung benötigt die Temperatur in Kelvin.
    temperatures_k = temperatures_c + 273.15

    # Aus lokalem Luftdruck und lokaler Temperatur wird für jeden Streckenabschnitt die Luftdichte bestimmt.
    air_densities = (
        pressure_pa
        / (
            specific_gas_constant
            * temperatures_k
        )
    )

    return air_densities