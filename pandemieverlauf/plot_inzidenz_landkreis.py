#!/usr/bin/env python3
"""

Creates a graph showing the pandemic course of selected german counties.
Based on data from Pavel Meyer: https://pavelmayer.de/covid/risks/


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

import argparse
import math
import sys
import re
import time
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests as rq

SOURCE_FILE = "/all-series.csv"
SOURCE_URL = "https://pavelmayer.de/covid/risks/all-series.csv"
LAST_SIZE_FILE = "/all-series.size"


def prepare_data(ctx):
    """Filter the source file for needed data points."""
    # column names for pavels risk-table version 1.0.2.0 and up
    cols = [
        "Datum",
        "Landkreis",
        "AnzahlFall",
        "InzidenzFallNeu_7TageSumme",
    ]

    pavel = pd.read_csv(ctx["cwd"] + SOURCE_FILE)

    # build a map with all counties or take counties from given list
    lk_map = {}  # lk -> [(date, inzidenz) ...]

    lks = ctx["lks"]

    # fill map with datapoints
    for lk in lks:
        lk_map[lk] = []
        curr_lk = pavel[pavel[cols[1]] == lk][[cols[0], cols[3]]]
        for _, row in curr_lk.iterrows():
            if not math.isnan(row[cols[3]]):
                # strptime can't handle non zero padded days
                # dt = datetime.strptime(row[cols[0]], "%d.%m.%y")
                d = row[cols[0]].split(".")  # source example: 23.3.2021
                dt = datetime(int(d[2]), int(d[1]), int(d[0]))
                if ctx["start_date"] <= dt:
                    lk_map[lk].append((dt, row[cols[3]]))

    ctx["data"] = lk_map


def get_all_lks(ctx):
    """Return a list with all counties."""
    pavel = pd.read_csv(ctx["cwd"] + SOURCE_FILE)
    return pavel["Landkreis"].unique().tolist()


def show_lks(ctx):
    """Print a list of available counties."""
    for lk in get_all_lks(ctx):
        print(lk)


def check_for_invalid_lks(ctx):
    """Exit script if a given Landkreis is unknown."""
    for lk in ctx["lks"]:
        if lk not in get_all_lks(ctx):
            print(f'"{lk}" unbekannt. Anzeige aller möglichen Landkreise mit -a')
            sys.exit(1)


def get_remote_file_size():
    """Do a HEAD request to obtain file size."""
    r = rq.head(url=SOURCE_URL)

    if r.status_code == 200:
        return int(r.headers["Content-Length"])
    else:
        print(
            f"""
        unable to obtain file size via head request\n{r.status_code} - {r.reason}"""
        )
        sys.exit(1)


def download_source_file(ctx):
    """
    Download source file and save it to disk.

    The file is saved to SOURCE_FILE and the file size to LAST_FILE_SIZE.
    """
    last_path = Path(ctx["cwd"] + LAST_SIZE_FILE)
    source_path = Path(ctx["cwd"] + SOURCE_FILE)

    r = rq.get(SOURCE_URL)

    if r.status_code == 200:
        file_length = len(r.content)

        # write data
        if source_path.is_file():
            source_path.unlink()

        if file_length == ctx["remote_size"]:
            source_path.write_bytes(r.content)
        else:
            raise ValueError(f"Downloaded file size {file_length} does not match remote size {ctx['remote_size']}")

        # write file size to file
        if last_path.is_file():
            last_path.unlink()
        # last_path.write_text(f"{r.headers['Content-Length']}")
        last_path.write_text(f"{file_length}")

    else:
        print(f"unable to download source file \n{r.status_code} - {r.reason}")
        sys.exit(1)


def get_source_file(ctx):
    """Try to download the source file for retry times if an error happens."""

    success = False
    retry = 3
    while not success:
        try:
            download_source_file(ctx)
            success = True
        except ValueError as e:
            print(e)
            time.sleep(20)
            if retry <= 0:
                print(f"unable to get whole source file")
                sys.exit(1)
            retry -= 1


def fetch_source(ctx):
    """Download new data if available."""
    # debug mode: only check if file is present
    if ctx["debug"]:
        source_path = Path(ctx["cwd"] + SOURCE_FILE)
        if source_path.exists():
            return
        else:
            print(f"Source: {SOURCE_FILE} not present, not downloaded while in debug mode")
            sys.exit(1)
    else:

        last_path = Path(ctx["cwd"] + LAST_SIZE_FILE)
        remote_size = get_remote_file_size()
        ctx["remote_size"] = remote_size

        if last_path.is_file():
            last_size = int(last_path.read_text())
            if last_size == remote_size:
                return  # no new data available
            else:
                get_source_file(ctx)
        else:
            get_source_file(ctx)


def get_last_date(ctx):
    date_list = [date for date, _ in ctx["data"][ctx["lks"][0]]]
    return date_list[-1]


def plot(ctx):
    """Plot the prepared data."""

    last_date = get_last_date(ctx)
    last_date_string = last_date.strftime("%d.%m.%Y")
    start_date_string = ctx["start_date"].strftime("%d.%m.%Y")

    plt.figure(figsize=(16, 9))
    plt.style.use("seaborn")
    plt.title(
        f"Pandemieverlauf für ausgewählte Landkreise - vom {start_date_string} bis {last_date_string}",
        fontsize=20,
        fontweight="bold",
        pad=20,
    )
    plt.ylabel(
        "Inzidenz - Fälle pro 100.000 Einwohner im 7 Tage Intervall",
        fontsize=16,
        labelpad=20,
    )
    plt.xticks(size=12, rotation=45)
    plt.yticks(size=14)

    palette = plt.get_cmap("Set1")

    i = 0
    for k, v in ctx["data"].items():
        plt.plot(
            [date for date, _ in v],
            [x for _, x in v],
            marker="",
            color=palette(i),
            linewidth=1,
            alpha=0.9,
            label=k,
        )
        i += 1

    plt.legend(
        loc="best",
        # bbox_to_anchor=(0.5, 1.12),
        shadow=True,
        ncol=2,
        fontsize=13,
        title="Quelle: pavelmayer.de/covid/risks/",
    )

    # print(f"writefile: {SOURCE_FILE}")
    plt.savefig(f"{ctx['cwd']}/{ctx['output']}")


def check_and_get_date(date_string):
    """Checks if a given string is a valid date of the format YYYY-MM-DD."""

    start_date = None
    today = datetime.utcnow()
    try:
        start_date = datetime.strptime(date_string, "%Y-%m-%d")
        if start_date > today:
            raise ValueError("The passed date is newer than today.")
    except ValueError as e:
        sys.stderr.write(f"The given start date {date_string} is invalid, use YYYY-MM-DD!\n")
        sys.stderr.write(f"Error-Message: {e}\n")
        sys.exit(-1)
    return start_date


def correct_filename(filename):
    """Out a .png suffix to the passed filename if necessary."""
    p = re.compile(".*\\.png", re.IGNORECASE)

    if not p.match(filename):
        filename += ".png"

    return filename


def main():
    """Start procedure."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-l",
        "--landkreis",
        type=str,
        action="append",
        help="Auswahl des Landkreises. Kann mehrfach verwendet werden.",
    )

    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Ausgabe aller möglichen Landkreise.",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Datenquelle wird nicht heruntergeladen.",
    )

    parser.add_argument(
        "-s",
        "--start-date",
        type=str,
        default="2020-03-15",
        help="Startdatum der Anzeige: YYYY-MM-DD",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="pandemic_course.png",
        help="The filename the PNG graphic will be saved to.",
    )

    args = parser.parse_args()

    # build up context
    base_dir = Path(sys.argv[0])
    base_dir = base_dir.parent
    context = {
        "cwd": str(base_dir),
        "lks": args.landkreis,
        "debug": args.debug,
        "output": correct_filename(args.output),
        "start_date": check_and_get_date(args.start_date),
    }

    if args.all:
        show_lks(context)
        sys.exit(0)

    # fetch recent data from pavel's homepage
    fetch_source(context)
    check_for_invalid_lks(context)
    prepare_data(context)
    plot(context)


main()
