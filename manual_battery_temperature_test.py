from src.lipo_battery import LiPoBatteryPack


def main() -> None:
    # Testakku mit einer Anfangstemperatur von 25 °C erstellen.
    battery = LiPoBatteryPack(
        capacity_nom_Ah=50.0,
        initial_temperature_c=25.0,
    )

    # Innenwiderstand vor der Erwärmung ausgeben.
    print(
        "Innenwiderstand vor dem Test: "
        f"{battery.effective_internal_resistance():.4f} Ohm"
    )

    # Einen Simulationsschritt durchführen:
    # Stromstärke: 10 A
    # Zeitdauer: 10 s
    # Umgebungstemperatur: 25 °C
    battery.update_temperature(
        current=10.0,
        duration=10.0,
        ambient_temperature_c=25.0,
    )

    # Akkutemperatur nach dem Simulationsschritt ausgeben.
    print(
        "Akkutemperatur nach dem Test: "
        f"{battery.temperature_c:.4f} °C"
    )


if __name__ == "__main__":
    main()