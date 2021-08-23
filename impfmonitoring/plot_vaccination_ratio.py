#!/usr/bin/env python3
"""

Creates a graph showing the vaccination rates (covid-19) of the German states.
For this purpose, an Excel from the Robert Koch Institute is used.


Copyright 2021 Martin Steinbach

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import csv
import sys
import hashlib
from datetime import datetime
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests as rq

DOSES_URL = "https://impfdashboard.de/static/data/germany_vaccinations_by_state.tsv"
INHAB_DATA = "/CensusByRKIAgeGroups.csv"

# the impfdashboard does not send an eTag anymore but the filename is still the same
LAST_UPDATE_RKI = "/last_doses_etag"
FILE_OUT = "Impfstatistik_relativ.png"
STATES = 16

HISTORICAL_STATE_DATA = "/hist_states.csv"

fed_map = {
    "DE-BW": "Baden-Württemberg",
    "DE-BY": "Bayern",
    "DE-BE": "Berlin",
    "DE-BB": "Brandenburg",
    "DE-HB": "Bremen",
    "DE-HH": "Hamburg",
    "DE-HE": "Hessen",
    "DE-MV": "Mecklenburg-Vorpommern",
    "DE-NI": "Niedersachsen",
    "DE-NW": "Nordrhein-Westfalen",
    "DE-RP": "Rheinland-Pfalz",
    "DE-SL": "Saarland",
    "DE-SN": "Sachsen",
    "DE-ST": "Sachsen-Anhalt",
    "DE-SH": "Schleswig-Holstein",
    "DE-TH": "Thüringen",
}

# they do not send eTag via HEAD anymore (since 2021-08-22)
def get_hash(url):
    """Calculate sha256 over content."""
    r = rq.get(url)
    if r.status_code == 200:
        m = hashlib.sha256()
        m.update(r.content)
        print(m.hexdigest())
        return m.hexdigest()
    else:
        print(f"unable to get etag \n{r.status_code} - {r.reason}")
        sys.exit(1)


def is_dashboard_file_new(context):
    """Return true if the downloaded file is newer than the last one.

    If no entry in LAST_UPDATE_FILE exists, a new entry will be created.
    """
    remote_etag = get_hash(DOSES_URL)
    last_path = Path(context["cwd"] + LAST_UPDATE_RKI)

    if last_path.is_file():
        last_log = last_path.read_text()
        old_etag = last_log.split(";")[1]
        if remote_etag == old_etag:
            return False
        else:
            last_path.unlink()
            last_path.write_text(f"{get_date_string()};{remote_etag}")
            return True
    else:
        last_path.write_text(f"{get_date_string()};{remote_etag}")
        return True


def get_source(url):
    """Download data ."""
    r = rq.get(url)
    if r.status_code == 200:
        return r.content
    else:
        sys.stderr.write(f"unable to get source {url} \n{r.status_code} - {r.reason}\n")
        sys.exit(1)


def get_inhab_data(context):
    """Use local census data and return data frame."""
    file_path = Path(context["cwd"] + INHAB_DATA)

    if not file_path.is_file():
        sys.stderr.write(f"Unable to load {INHAB_DATA}")
        sys.exit(2)

    return pd.read_csv(context["cwd"] + INHAB_DATA)


def get_date_string():
    """Return date string: YYYY-MM-DD."""
    unow = datetime.utcnow()
    return "{:%Y-%m-%d}".format(unow)


def get_human_time():
    """Return human readable time string."""
    unow = datetime.utcnow()
    return "{:%d.%m.%Y}".format(unow)


def write_state_data_to_csv(heading, values, context):
    """Write the doses per state to a csv file for future use."""
    csv_path = Path(context["cwd"] + HISTORICAL_STATE_DATA)
    date = get_date_string()

    if not csv_path.is_file():
        heading = ["DATE"] + heading
        with open(str(csv_path), mode="w") as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=",")
            csv_writer.writerow(heading)

    values = [date] + values
    with open(str(csv_path), mode="a") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=",")
        csv_writer.writerow(values)


def plot(doses_file, context):
    """Plot a stacked graph."""

    try:
        doses = pd.read_table(BytesIO(doses_file))
    except Exception as e:
        sys.stderr.write("Unable to read doses_file.\n")
        sys.stderr.write(str(e))
        sys.exit(1)

    inhab = get_inhab_data(context)

    dosis_first = []
    dosis_second = []
    inhabitants = []
    states_short = [state.split("-")[1] for state in doses["code"].tolist()]
    for state in doses["code"].tolist():

        if state != "DE-BUND":  # they added DE-BUND on 2021-08-22
            long_state = fed_map[state]
            series_inhab = inhab[inhab["Name"] == long_state]["Insgesamt-total"]
            inhabitants.append(series_inhab.values[0])

            # amount of first dosis
            series_dosis_first = doses[doses["code"] == state]["peopleFirstTotal"]
            dosis_first.append(series_dosis_first.values[0])

            # amount of second dosis
            series_dosis_second = doses[doses["code"] == state]["peopleFullTotal"]
            dosis_second.append(series_dosis_second.values[0])

    # add country wide data
    states_short.append("DE")
    inhabitants.append(sum(inhabitants))
    dosis_first.append(sum(dosis_first))
    dosis_second.append(sum(dosis_second))

    # print(states_short
    # print(inhabitants)
    # print(dosis)

    dosis_total = [i + j for i, j in zip(dosis_first, dosis_second)]
    write_state_data_to_csv(states_short, dosis_total, context)

    # Percentage of people who have received the first dose.
    vacc_rate = [i / j * 100 for i, j in zip(dosis_first, inhabitants)]

    # Percentage of people who have received the second dose.
    vacc_rate_2 = [i / j * 100 for i, j in zip(dosis_second, inhabitants)]

    # Percentage of people who have received the first dose but not the second.
    vacc_diff = [i - j for i, j in zip(vacc_rate, vacc_rate_2)]

    rest = [100 - (i + j) for i, j in zip(vacc_diff, vacc_rate_2)]

    d = get_human_time()

    plt.figure(figsize=(16, 9))
    plt.style.use("seaborn")
    plt.ylabel("%", fontsize=22, labelpad=30)
    names = [
        f"{s}\n({str(round(i, 1))})\n\n[{str(round(j, 1))}]" for s, i, j in zip(states_short, vacc_rate, vacc_rate_2)
    ]
    plt.xticks(range(STATES + 1), names, size=14)
    plt.yticks(range(0, 101, 10), size=14)
    plt.title(
        f"Anteil verabreichter COVID-19 Impfdosen nach Bundesländern - {d}\n",
        fontsize=20,
        fontweight="bold",
        pad=20,
    )

    bar_width = 0.85

    plt.bar(
        range(STATES + 1),
        vacc_rate_2,
        color="darkgreen",
        edgecolor="white",
        width=bar_width,
        label="[Anteil vollständig geimpft]",
    )
    plt.bar(
        range(STATES + 1),
        vacc_diff,
        bottom=vacc_rate_2,
        color="lightgreen",
        edgecolor="white",
        width=bar_width,
        label="(Anteil Erstimpfung erhalten)",
    )
    plt.bar(
        range(STATES + 1),
        rest,
        bottom=vacc_rate,
        color="#ff9cA6",
        edgecolor="white",
        width=bar_width,
        label="Anteil - keine Impfdosen verabreicht",
    )

    plt.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.08),
        shadow=True,
        ncol=3,
        fontsize=16,
    )

    plt.text(-3.9, -5, "Quelle: impfdashboard.de", fontsize=12)
    plt.savefig(f"{context['cwd']}/{FILE_OUT}")


def main():
    """Start the whole procedure."""
    base_dir = Path(sys.argv[0])
    base_dir = base_dir.parent
    context = {"cwd": str(base_dir)}
    if is_dashboard_file_new(context):
        doses_file = get_source(DOSES_URL)
        plot(doses_file, context)


main()
