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
    # column names for pavels risk-table version 1.0.2.0
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
        unable to obtain filesize via head request\n{r.status_code} - {r.reason}"""
        )
        sys.exit(1)


def get_source_file(ctx):
    """
    Download source file and save it to disk.

    The file is saved to SOURCE_FILE and the file size to LAST_FILE_SIZE.
    """
    last_path = Path(ctx["cwd"] + LAST_SIZE_FILE)
    source_path = Path(ctx["cwd"] + SOURCE_FILE)

    r = rq.get(SOURCE_URL)

    if r.status_code == 200:

        # write data
        if source_path.is_file():
            source_path.unlink()
        source_path.write_bytes(r.content)

        # write file size to file
        if last_path.is_file():
            last_path.unlink()
        last_path.write_text(f"{r.headers['Content-Length']}")

    else:
        print(f"unable to download source file \n{r.status_code} - {r.reason}")
        sys.exit(1)


def fetch_source(ctx):
    """Download new data if available."""
    # debug mode: only check if file is present
    if ctx["debug"]:
        source_path = Path(ctx["cwd"] + SOURCE_FILE)
        if source_path.exists():
            return
        else:
            print(
                f"Source: {SOURCE_FILE} not present, not downloades while in debug mode"
            )
            sys.exit(1)
    else:

        last_path = Path(ctx["cwd"] + LAST_SIZE_FILE)

        if last_path.is_file():
            last_size = int(last_path.read_text())
            remote_size = get_remote_file_size()
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
    date_string = last_date.strftime("%d.%m.%Y")

    plt.figure(figsize=(16, 9))
    plt.style.use("seaborn")
    plt.title(
        f"Pandemieverlauf für ausgewählte Landkreise - Stand: {date_string}",
        fontsize=20,
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
    plt.savefig(f"{ctx['cwd']}/pandemic_course.png")


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

    args = parser.parse_args()

    # build context
    base_dir = Path(sys.argv[0])
    base_dir = base_dir.parent
    context = {"cwd": str(base_dir), "lks": args.landkreis, "debug": args.debug}

    if args.all:
        show_lks(context)
        sys.exit(0)

    # fetch recent data from pavel's homepage
    fetch_source(context)
    check_for_invalid_lks(context)
    prepare_data(context)
    plot(context)


main()
