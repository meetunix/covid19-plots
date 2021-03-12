<h1 align="center">covid19-Impfmonitoring</h1>

<p align="center">
<a href="https://github.com/meetunix/covid19-impfmonitoring-plot/blob/main/LICENSE" title="License">
<img src="https://img.shields.io/badge/License-Apache%202.0-green.svg?style=flat"></a>
</p>

Das Python3-Skript `plot_vaccination_ratio.py` generiert folgenden Plot
auf meiner Website: [Covid-19 Impfmonitoring](https://nachtsieb.de/covid-19.html).

<img src="https://nachtsieb.de/img/current_vaccination.png">


Dazu durchsucht es die
[Impfmonitoring-Website](https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Daten/Impfquoten-Tab.html)
des Robert Koch Institutes nach der
aktuellen Excel-Datei, ermittelt die benötigten Daten, erstellt die Grafik und schreibt
die Summe aller bisher verabreichten Dosen in die Datei `hist_states.csv`, aufgeschlüsselt
nach Bundesland. Ein neuer Plot wird nur bei Änderungen der entsprechenden
Excel-Tabelle erstellt.

Die benötigten
[Einwohnerdaten](https://github.com/pavel-mayer/Corona/blob/master/CensusByRKIAgeGroups.csv)
wurden aus dem Repository von Pavel Meyer bezogen.


## Verwendung

Das Skript kann direkt ausgeführt werden:

```
python plot_vaccination_ratio.py
```

Der Plot steht danach unter dem Namen `Impfstatistik_relativ.png` zur Verfügung.
Die Excel-Dateien und neu generierte Grafiken werden im `archiv`-Verzeichnis gespeichert.
