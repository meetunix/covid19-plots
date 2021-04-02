<h1 align="center">covid19-Plots</h1>


<p align="center">
<a href="https://github.com/meetunix/covid19-impfmonitoring-plot/blob/main/LICENSE" title="License">
<img src="https://img.shields.io/badge/License-Apache%202.0-green.svg?style=flat"></a>
</p>


## Impfmonitoring nach Bundesländern

Das Python3-Skript `impfmonitoring/plot_vaccination_ratio.py` generiert folgenden Plot
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


#### Verwendung

Das Skript kann direkt ausgeführt werden:

```
python plot_vaccination_ratio.py
```

Der Plot steht danach unter dem Namen `Impfstatistik_relativ.png` zur Verfügung.
Die Excel-Dateien und neu generierte Grafiken werden im `archiv`-Verzeichnis gespeichert.


### Pandemieverlauf für Landkreise und Bundesländer

Das Skript `impfmonitoring/plot_pandemic_course.py` generiert folgenden Plot
auf meiner Website: [Covid-19 Impfmonitoring](https://nachtsieb.de/covid-19.html).

Als Datenquelle verwendet es die aufbereiteten Daten von
[Pavel Meyer](https://pavelmayer.de/covid/risks/).

<img src="https://nachtsieb.de/img/pandemic_course.png">


#### Verwendung

Erstellen eines Plots für mehrere Landkreise, Länder und der Bundesrepublik:


```
python plot_pandemic_course.py -l "SK Rostock" -l "Mecklenburg-Vorpommern" -l "LK Rostock" -l "Deutschland"
```



Anzeige aller möglichen Landkreise:


```
python plot_pandemic_course.py -a
```

Der Plot steht unter dem Namen `pandemic_course.png` zur Verfügung.

Vor jedem Plot wird geprüft ob aktualisierte Quelldaten auf
[pavelmeyer.de](https://pavelmayer.de/covid/risks/) vorliegen und nur da heruntergeladen.
Soll auch diese Prüfung unterbleiben und keine Aktualisierung der Quelldaten erfolgen, 
kann man option `-d` verwenden.
