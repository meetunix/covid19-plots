<h1 align="center">covid19-Plots</h1>


<p align="center">
<a href="https://github.com/meetunix/covid19-impfmonitoring-plot/blob/main/LICENSE" title="License">
<img src="https://img.shields.io/badge/License-Apache%202.0-green.svg?style=flat"></a>
</p>


## Impfmonitoring nach Bundesländern

### Anteil verabreichter Impfdosen relativ zur Bevölkerung
Das Python3-Skript `impfmonitoring/plot_vaccination_ratio.py` generiert folgenden Plot
auf meiner Website: [Covid-19 Impfmonitoring](https://nachtsieb.de/covid-19.html).

<p align="center">
<img width="480" src="https://nachtsieb.de/img/current_vaccination.png">
</p>

Als Quelle verwendet es die Daten vom [Impfdashboard](https://impfdashboard.de/daten), erstellt die Grafik und schreibt
die Summe aller bisher verabreichten Dosen in die Datei `hist_states.csv`, aufgeschlüsselt
nach Bundesland. Ein neuer Plot wird nur bei Änderungen der entsprechenden
Quelldatei erstellt.

Die benötigten
[Einwohnerdaten](https://github.com/pavel-mayer/Corona/blob/master/CensusByRKIAgeGroups.csv)
wurden aus dem Repository von Pavel Meyer bezogen.


#### Verwendung

Das Skript kann direkt ausgeführt werden:

```
python plot_vaccination_ratio.py
```

Der Plot steht danach unter dem Namen `Impfstatistik_relativ.png` zur Verfügung.

## Anteil der verabreichten und gelieferten Impfdosen

Das Skript `impfdosen/plot_vaccination_doses_per_state.py` erstellt folgenden Plot, der ebenfalls auf meiner
[Homepage](https://nachtsieb.de/covid-19.html) zu finden ist.

<p align="center">
<img  width="480" src="https://nachtsieb.de/img/doses_delivered_vaccinated_ratio.png">
</p>p>

Als Quelle dient hier ebenfalls das [Impfdashboard](https://impfdashboard.de/daten). 


## Pandemieverlauf für Landkreise und Bundesländer

Das Skript `impfmonitoring/plot_inzidenz_landkreis.py` generiert folgenden Plot
auf meiner Website: [Covid-19 Impfmonitoring](https://nachtsieb.de/covid-19.html).

Als Datenquelle verwendet es die aufbereiteten Daten von
[Pavel Meyer](https://pavelmayer.de/covid/risks/).

<p align="center">
<img  width="480" src="https://nachtsieb.de/img/pandemic_course.png">
</p>

#### Verwendung

Erstellen eines Plots für mehrere Landkreise, Länder und der Bundesrepublik:


```
python plot_inzidenz_landkreis.py -l "SK Rostock" -l "Mecklenburg-Vorpommern" -l "LK Rostock" -l "Deutschland"
```

Anzeige aller möglichen Landkreise:

```
python plot_inzidenz_landkreis.py -a
```

Der Plot steht unter dem Namen `pandemic_course.png` zur Verfügung.

Es ist auch möglich eine alternative Ausgabedatei und ein **Startdatum** anzugeben:

```
python plot_inzidenz_landkreis.py -l "SK Köln" -l "SK Düsseldorf" -l "SK Bonn" -o nrw_2021.png -s 2021-01-01  

```

Vor jedem Plot wird geprüft, ob aktualisierte Quelldaten auf
[pavelmeyer.de](https://pavelmayer.de/covid/risks/) zur Verfügung stehen.
Soll auch diese Prüfung unterbleiben und keine Aktualisierung der Quelldaten erfolgen,
kann die option `-d` verwendet werden.
