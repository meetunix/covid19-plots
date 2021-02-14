#!/usr/bin/env python3

import csv
import hashlib
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.rki.de/"
URL = (
    BASE_URL + "DE/Content/InfAZ/N/Neuartiges_Coronavirus/Daten/Impfquoten-Tab.html"
)

PAVEL_DATA_URL = "https://pavelmayer.de/covid/risks/data.csv"
PAVEL_DATA_LOCAL = "/pavel.csv"

LAST_UPDATE_RKI = "/last_rki_file_hash"
FILE_OUT = "Impfstatistik_relativ.png"
STATES = 16

ARCHIVE = "archiv"

HISTORICAL_STATE_DATA = "/hist_states.csv"


def get_file_from_rki():
    """Scrape the rki page for correct link and return downloaded data."""
    response = requests.get(URL)

    soup = BeautifulSoup(response.text, "html.parser")

    a_tags = soup.findAll("a")

    link = ""
    for tag in a_tags:
        try:
            link = str(tag["href"])
            if link.index("Impfquotenmonitoring.xlsx"):
                break
        except KeyError:
            pass
        except ValueError:
            pass

    link = BASE_URL + link
    # print(link)
    response = requests.get(link)

    excel_file = response.content

    return excel_file


def is_rki_file_new(rki_file, context):
    """Return true if the downloaded rki file is newer than the last one.

    If no entry in LAST_UPDATE_FILE exists, a new entry will be created.
    """
    current_hash = hashlib.sha256(rki_file).hexdigest()
    last_path = Path(context["cwd"] + LAST_UPDATE_RKI)

    if last_path.is_file():
        last_log = last_path.read_text()
        old_hash = last_log.split(";")[1]
        if current_hash == old_hash:
            return False
        else:
            last_path.unlink()
            last_path.write_text(f"{get_date_string()};{current_hash}")
            return True
    else:
        last_path.write_text(f"{get_date_string()};{current_hash}")
        return True


def get_pavel_data(context):
    """Try to use the local variant of pavels data.

    If no local file exists, it will be downloaded.
    """
    file_path = Path(context["cwd"] + PAVEL_DATA_LOCAL)

    if not file_path.is_file():
        response = requests.get(PAVEL_DATA_URL)
        if not response.status_code == 200:
            sys.stderr.write(f"Unable to fetch data from {PAVEL_DATA_URL}")
            sys.exit(2)
        else:
            file_path.write_text(response.text)


def store_rki_file(rki_file, context):
    """Store the previously downloaded file from RKI."""
    filename = f"{context['cwd']}/{ARCHIVE}/{get_date_string()}-Impfmonitoring.xlsx"

    with open(filename, "wb") as f:
        f.write(rki_file)


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


def plot(rki_file, context):
    """Plot a stacked graph."""
    fed_map = {
        "Baden-Württemberg": "BW",
        "Bayern": "BY",
        "Berlin": "BE",
        "Brandenburg": "BB",
        "Bremen": "HB",
        "Hamburg": "HH",
        "Hessen": "HE",
        "Mecklenburg-Vorpommern": "MV",
        "Niedersachsen": "NI",
        "Nordrhein-Westfalen": "NW",
        "Rheinland-Pfalz": "RP",
        "Saarland": "SL",
        "Sachsen": "SN",
        "Sachsen-Anhalt": "ST",
        "Schleswig-Holstein": "SH",
        "Thüringen": "TH",
    }

    try:
        # https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Daten/Impfquoten-Tab.html
        rki = pd.read_excel(
            rki_file, sheet_name=1, nrows=STATES, skiprows=3, header=None
        )
    except Exception:
        sys.stderr.write("Unable to read file from rki.\n")
        sys.exit(1)

    # read an arbitrary list from pavels homepage to get inhabitants by federal state
    # https://pavelmayer.de/covid/risks/
    pavel = pd.read_csv(context["cwd"] + PAVEL_DATA_LOCAL, index_col=0)

    pavel = pavel[pavel["LandkreisTyp"] == "B"][["Landkreis", "Bevoelkerung"]]

    dosis_first = []
    dosis_second = []
    inhabitants = []
    states_short = []
    for i in range(STATES):
        state = rki[1][i]
        # there are annotation directly added in the field separated by space
        # therfore a cleaned state is needed to compare with pavels data
        cleaned_state = state.split(" ")[0]

        series_inhab = pavel[pavel["Landkreis"] == cleaned_state]["Bevoelkerung"]
        inhabitants.append(series_inhab.values[0])

        # amount of first dosis
        series_dosis_first = rki[rki[1] == state][3]
        dosis_first.append(series_dosis_first.values[0])

        # amount of second dosis
        # NOTE: if new vaccines are allowed this column must be incremented
        series_dosis_second = rki[rki[1] == state][9]
        dosis_second.append(series_dosis_second.values[0])

        states_short.append(fed_map[cleaned_state])

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

    vacc_rate = [i / j * 100 for i, j in zip(dosis_first, inhabitants)]
    vacc_rate_2 = [i / j * 100 for i, j in zip(dosis_second, inhabitants)]
    total_rate = [i + j for i, j in zip(vacc_rate, vacc_rate_2)]
    rest = [100 - i for i in total_rate]

    # print(vacc_rate)
    # print(rest)
    d = get_human_time()

    plt.figure(figsize=(16, 8))
    plt.style.use("seaborn")
    plt.ylabel("%", fontsize=22, labelpad=30)
    names = [
        f"{s}\n({str(round(i, 2))})" for s, i in zip(states_short, vacc_rate_2)
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
        label="Anteil Zweitimpfung erhalten",
    )
    plt.bar(
        range(STATES + 1),
        vacc_rate,
        bottom=vacc_rate_2,
        color="lightgreen",
        edgecolor="white",
        width=bar_width,
        label="Anteil Erstimpfung erhalten",
    )
    plt.bar(
        range(STATES + 1),
        rest,
        # bottom=vacc_rate,
        bottom=total_rate,
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

    plt.text(-3.5, -3, "Quelle: RKI", fontsize=12)
    plt.text(5, -12.5, "(Anteil Zweitimpfung erhalten in %)", fontsize=14)

    return plt


def store_plot(plot, context):
    """Store the plot into the archive and link to FILE_OUT."""
    # create archive dir
    archive_path = Path(ARCHIVE)
    archive_path.mkdir(exist_ok=True)

    filename = f"{context['cwd']}/{ARCHIVE}/{get_date_string()}-{FILE_OUT}"
    link_path = Path(context["cwd"] + "/" + FILE_OUT)
    plt.savefig(filename)
    if link_path.exists():
        link_path.unlink()
    link_path.symlink_to(filename)


def main():
    """Start the whole procedure."""
    base_dir = Path(sys.argv[0])
    base_dir = base_dir.parent
    context = {"cwd": str(base_dir)}
    get_pavel_data(context)
    rki_file = get_file_from_rki()
    if is_rki_file_new(rki_file, context):
        plt = plot(rki_file, context)
        store_plot(plt, context)
        store_rki_file(rki_file, context)


main()
