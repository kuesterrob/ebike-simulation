# E-Bike-Simulation

## 1. Einleitung

### 1.1 Ziel des Projekts

Ziel dieses Projekts ist die Entwicklung einer objektorientierten E-Bike-Simulation in Python. Das Programm untersucht anhand realer GPS-Daten, welche Kräfte, Leistungen und Energiemengen während einer Fahrt auftreten. Ein besonderer Schwerpunkt liegt auf dem Vergleich zweier Akkutypen: eines Lithium-Polymer-Akkus (LiPo) und eines Nickel-Mangan-Cobalt-Akkus (NMC).

Neben dem Energieverbrauch berücksichtigt die Simulation auch die Rückgewinnung von Bremsenergie durch Rekuperation. Dadurch kann untersucht werden, wie sich unterschiedliche Streckenabschnitte, Steigungen, Geschwindigkeiten und Fahrzeugparameter auf den Motor, die Akkus und das Bremssystem auswirken.

### 1.2 Kurze Beschreibung der Anwendung

Die Anwendung wird über ein Terminal-Menü bedient. Nach dem Programmstart kann zwischen einer Parameterstudie und einer einzelnen Simulation mit konkreten Eingabewerten gewählt werden.

Als Grundlage verwendet das Programm eine CSV-Datei mit GPS-Koordinaten, Zeitpunkten und Höhenwerten. Aus diesen Daten berechnet die Anwendung unter anderem:

- die Länge der einzelnen Streckenabschnitte,
- die Geschwindigkeit und Beschleunigung,
- die Steigung und das Höhenprofil,
- den Luft- und Rollwiderstand,
- die benötigte Motorleistung,
- den Stromverbrauch,
- den Ladezustand und die Temperatur der Akkus,
- die beim Bremsen zurückgewonnene Energie,
- die Belastung der Bremswiderstände und der mechanischen Bremsen.

Zusätzlich werden Wetter- und Ortsdaten über externe Schnittstellen abgerufen und zwischengespeichert. Die Simulation wird sowohl für den LiPo- als auch für den NMC-Akku durchgeführt, damit die Ergebnisse miteinander verglichen werden können.

Die Ergebnisse können im Terminal ausgegeben, als Diagramme dargestellt und in einem PDF-Bericht gespeichert werden. Außerdem erzeugt das Programm eine interaktive HTML-Karte der gefahrenen Route.

## 2. Projekt starten

### 2.1 Voraussetzungen

Zum Ausführen des Projekts werden Python 3.9 oder neuer sowie Git benötigt. Für das erstmalige Abrufen von Wetter- und Ortsdaten kann außerdem eine Internetverbindung erforderlich sein.

Die benötigten Python-Bibliotheken werden zentral in der Datei `requirements.txt` verwaltet.

### 2.2 Installation

Zuerst muss das Projekt von GitHub geklont werden. Dannach kann Optional kann eine virtuelle Python-Umgebung erstellt werden.
Anschließend müssen die benötigten Bibliotheken aus der Datei `requirements.txt` installiert:

```bash
python -m pip install -r requirements.txt
```

### 2.3 Starten des Programms

Das Programm wird im Projektordner mit folgendem Befehl gestartet:

```bash
python main.py
```

Nach dem Start erscheint das Terminal-Menü der E-Bike-Simulation.

## 3. Bedienung des Programms

### 3.1 Aufbau des Terminal-Menüs

Nach dem Programmstart erscheint folgende Auswahl:

```text
Möchtest du eine Parameterstudie durchführen oder
mit bestimmten Werten simulieren?

[1] Parameterstudie
[2] Konkrete Werte
Auswahl (1–2):
```

Die gewünschte Funktion wird durch Eingabe der entsprechenden Zahl und anschließendes Drücken der Eingabetaste ausgewählt.

### 3.2 Erklärung der Hauptmenüpunkte

#### Menüpunkt 1: Parameterstudie

Die Parameterstudie führt automatisch 20 vordefinierte Simulationen aus. Dazu gehören beispielsweise:

- eine Basiskonfiguration,
- ein Pendler-E-Bike,
- ein Lastenrad,
- ein sportliches Fahrrad,
- ein Mountainbike,
- verschiedene Fahrer- und Fahrradgewichte,
- unterschiedliche Luftwiderstände,
- verschiedene Reifentypen,
- unterschiedliche Motor- und Radkonfigurationen,
- ein Best-Case- und ein Worst-Case-Szenario.

Jede Konfiguration wird mit der Basiskonfiguration verglichen. Im Terminal wird dargestellt, wie stark der verbleibende Ladezustand von der Referenz abweicht. Dadurch lässt sich erkennen, welche Parameter den größten Einfluss auf den Energieverbrauch besitzen.

#### Menüpunkt 2: Konkrete Werte

Bei dieser Auswahl kann eine einzelne Simulation mit konkreten Parametern durchgeführt werden. Zunächst fragt das Programm, ob die Standardwerte verwendet werden sollen:

```text
Standardwerte für alle Parameter verwenden? [J/n]:
```

Wird die Eingabetaste gedrückt oder `j` eingegeben, verwendet das Programm folgende Standardwerte:

- Fahrergewicht: 70 kg
- Fahrradgewicht: 10 kg
- effektive Stirnfläche: 0,5625 m²
- Raddurchmesser: 27 Zoll
- Motorkonstante: 1,5 Nm/A
- Rollwiderstandsbeiwert: 0,0077

Bei der Eingabe von `n` können diese Werte einzeln verändert werden. Eine leere Eingabe übernimmt jeweils den angezeigten Standardwert. Dezimalzahlen können mit einem Punkt oder einem Komma eingegeben werden.

### 3.3 Auswahl der Terminalausgaben

Anschließend wird ausgewählt, welche Ergebnisse nach der Simulation im Terminal angezeigt werden sollen:

1. **Route und Fahrdaten:** Gesamtstrecke, Fahrzeit, Durchschnittsgeschwindigkeit, maximale Geschwindigkeit, Aufstieg und Abstieg.
2. **Umgebungsdaten:** Temperaturwerte und berechnete Luftdichte.
3. **Motor und Antrieb:** Rollwiderstand, Motorleistung, Motorstrom und benötigte mechanische Energie.
4. **Akkudaten:** Ladezustand, Spannung, Temperatur und Leistung des LiPo- und NMC-Akkus.
5. **Rekuperation und Bremsen:** zurückgewonnene Bremsenergie sowie Belastung der Bremswiderstände und mechanischen Bremsen.

Mehrere Menüpunkte können durch Kommas oder Leerzeichen getrennt eingegeben werden:

```text
1,3,4
```

Zusätzlich stehen folgende Eingaben zur Verfügung:

- `a` wählt alle Menüpunkte aus.
- `0` wählt keine Terminalausgabe aus.
- `q` bricht das Programm ab.

### 3.4 Auswahl der Diagramme

Danach können die gewünschten Diagramme ausgewählt werden. Folgende Darstellungen stehen zur Verfügung:

1. Geschwindigkeit
2. Beschleunigung
3. Steigung
4. Luftdichte
5. zurückgelegte Strecke
6. Windkraft
7. Antriebskraft
8. Motorleistung
9. Drehmoment
10. Motorstrom
11. Akkustrom
12. Batterieladezustand
13. Batteriespannung
14. Akkutemperatur
15. Akkuleistung
16. Akku-Innenwiderstand
17. Bremsleistungsbedarf
18. Rekuperationsleistung
19. Bremswiderstandsleistung
20. Bremswiderstandstemperatur
21. mechanische Bremsleistung

Auch hier können mehrere Nummern gemeinsam eingegeben werden. Mit `a` werden alle Diagramme ausgewählt. Mit `0` wird die Simulation ohne Diagrammausgabe fortgesetzt. Durch die Eingabe von `q` kann das Programm abgebrochen werden.

### 3.5 Erstellung des PDF-Berichts

Nach der Diagrammauswahl fragt das Programm, ob ein PDF-Bericht erstellt werden soll:

```text
Möchtest du aus dieser Auswahl einen PDF-Bericht erstellen? (j/n/q):
```

Folgende Eingaben sind möglich:

- `j` erstellt einen PDF-Bericht.
- `n` setzt die Simulation ohne PDF-Bericht fort.
- `q` bricht das Programm ab.

Der Bericht enthält die zuvor ausgewählten Kennzahlengruppen und Diagramme. Er wird unter folgendem Pfad gespeichert:

```text
outputs/ebike_simulation_report.pdf
```

Die gefahrene Route wird zusätzlich als interaktive Karte gespeichert:

```text
outputs/karte.html
```

### 3.6 Beispiel eines Programmablaufs

Ein möglicher Programmablauf sieht folgendermaßen aus:

1. Das Programm mit `python main.py` starten.
2. Menüpunkt 2 „Konkrete Werte“ auswählen.
3. Die Standardwerte mit `j` bestätigen.
4. Die Terminalausgaben 1, 4 und 5 auswählen.
5. Die Diagramme 1, 8, 12, 13, 14 und 18 auswählen.
6. Die PDF-Erstellung mit `j` bestätigen.

Anschließend liest das Programm die GPS-Daten ein, ergänzt Wetter- und Ortsinformationen und führt die Simulation für beide Akkutypen aus. Danach werden die gewählten Kennzahlen im Terminal ausgegeben, der PDF-Bericht und die Karte gespeichert sowie die ausgewählten Diagramme angezeigt.

### 3.7 Eingaben und Ausgaben

Die wichtigste Eingabedatei ist:

```text
data/final_project_input_data.csv
```

Sie enthält die GPS- und Streckendaten, die für die Berechnungen benötigt werden. Weitere Eingaben erfolgen über das Terminal. Dazu gehören beispielsweise das Fahrergewicht, das Fahrradgewicht und der Rollwiderstandsbeiwert.

Die Anwendung erzeugt folgende Ausgaben:

- Status- und Fehlermeldungen im Terminal,
- ausgewählte Simulationsergebnisse im Terminal,
- eine Vergleichstabelle bei der Parameterstudie,
- grafische Diagramme,
- einen optionalen PDF-Bericht,
- eine interaktive HTML-Karte der Route,
- Cache-Dateien für bereits abgerufene Wetter- und Ortsdaten.