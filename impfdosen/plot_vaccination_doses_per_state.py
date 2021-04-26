#!/usr/bin/env python3

"""
Creates a graph showing how much vaccines have been delivered and vaccinated
for each german state.

Source: https://impfdashboard.de/daten


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

import pickle
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests as rq

BASE_URL = "https://impfdashboard.de/static/data"
TIME_SERIES_DELIVERY = "/germany_deliveries_timeseries_v2.tsv"
VACCINATION_STATE = "/germany_vaccinations_by_state.tsv"

PICKLE_FILE = "sources.pickle"


class Sources:
    """Stores the url, length and etag information for the data sources."""

    def __init__(self, delivery_url, vacc_url):
        self.__delivery_url = delivery_url
        self.__vacc_url = vacc_url
        self.__etags = {f"{delivery_url}": None, f"{vacc_url}": None}
        self.__data = {f"{delivery_url}": None, f"{vacc_url}": None}
        self.__date = None

    def set_etag(self, etag, url):
        if url not in self.__etags.keys:
            print(f"url {url} unknown\n")
            sys.exit(1)
        self.__etags[url] = etag

    def get_urls(self):
        return [self.__delivery_url, self.__vacc_url]

    def get_etags(self):
        return self.__etags

    def get_data(self):
        return self.__data

    def is_etag_new(self, url):
        """Return True if the server etag is other than local."""
        local_etag = self.get_etags()[url]
        remote_etag = self.__get_remote_etag(url)

        return not (local_etag == remote_etag)

    def get_date_string(self):
        return self.__date.strftime("%d.%m.%Y")

    def download_sources(self):
        """Download data source files if necessary."""
        urls = self.get_urls()
        for url in urls:
            if self.is_etag_new(url):
                r = rq.get(url)
                if r.status_code == 200:
                    # print(f"downloaded the updated file {url.split('/')[-1]}")
                    self.__data[url] = r.content
                    # update etags
                    self.__etags[url] = r.headers["etag"]
                    # update date
                    date_string = r.headers["last-modified"]
                    self.__date = datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %Z")

                else:
                    print(f"unable to get source {url} \n{r.status_code - r.reason}")
                    sys.exit(1)

    def __get_remote_etag(self, url):
        r = rq.head(url)
        if r.status_code == 200:
            # print(r.headers["etag"])
            return r.headers["etag"]
        else:
            print(f"unable to get etag \n{r.status_code - r.reason}")
            sys.exit(1)


def load_object(context):
    """Load a stored Sources instance if available, otherwise None is returned."""
    sources_path = Path(context["cwd"] + f"/{PICKLE_FILE}")

    if sources_path.exists():
        with open(sources_path, "rb") as f:
            obj = pickle.load(f)
        return obj
    else:
        return None


def store_object(context, source):
    """Store a Sources instance to file."""
    sources_path = Path(context["cwd"] + f"/{PICKLE_FILE}")

    with open(sources_path, "wb") as f:
        pickle.dump(source, f, pickle.DEFAULT_PROTOCOL)


def prepare_data(context, urls, source_data):
    """Prepare data for plotting."""
    data = {}
    delivery = pd.read_table(BytesIO(source_data[urls["delivery"]]))
    vaccination = pd.read_table(BytesIO(source_data[urls["vaccination"]]))
    states = delivery["region"].unique().tolist()

    # exclude direct deliveries to the federal state, because of very low quantities
    for s in ["DE-BUND", "DE-Bund", "de-bund"]:
        try:
            states.remove(s)
        except ValueError:
            pass

    context["states"] = states

    for state in states:
        delivered = int(delivery[delivery["region"] == state][["dosen"]].sum())
        v = vaccination[vaccination["code"] == state][["vaccinationsTotal"]].values

        data[state] = (delivered, int(v))
        # print(state, data[state])

    context["data"] = data


def plot(context, sources):

    states = context["states"]
    states_short = [n.split("-")[1] for n in states]

    data = context["data"]
    delivered = []
    vaccinated = []
    for state in states:
        delivered.append(data[state][0])
        vaccinated.append(data[state][1])

    # percentage of used doses from delivered doses max 100% for clean presentation
    used_doses_norm = [100 if (i / j * 100) > 100 else i / j * 100 for i, j in zip(vaccinated, delivered)]

    # percentage of used doses from delivered doses
    used_doses = [i / j * 100 for i, j in zip(vaccinated, delivered)]

    # percentage of unused dosis
    rest = [100 - i for i in used_doses_norm]

    plt.figure(figsize=(16, 9))
    plt.style.use("seaborn")

    plt.ylabel("%", fontsize=22, labelpad=30)
    names = [f"{s}\n\n({str(round(i, 1))})" for s, i in zip(states_short, used_doses)]

    plt.xticks(range(len(states)), names, size=14)
    plt.yticks(range(0, 101, 10), size=14)
    ds = sources.get_date_string()
    plt.title(
        f"Anteil verimpfter und gelieferter Impfdosen nach Bundesländern - {ds}\n",
        fontsize=20,
        fontweight="bold",
        pad=20,
    )

    bar_width = 0.85

    plt.bar(
        range(len(states)),
        used_doses_norm,
        color="#9dad86",
        edgecolor="white",
        width=bar_width,
        label="Anteil verimpfter Dosen",
    )
    plt.bar(
        range(len(states)),
        rest,
        bottom=used_doses_norm,
        color="#9686ad",
        edgecolor="white",
        width=bar_width,
        label="Anteil noch nicht verimpfter Dosen",
    )

    plt.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.08),
        shadow=True,
        ncol=3,
        fontsize=16,
    )

    plt.text(-3.9, -5, "Quelle: impfdashboard.de", fontsize=12)
    plt.savefig(f"{context['cwd']}/doses_delivered_vaccinated_ratio.png")


def main():
    """Start the whole procedure."""
    context = {}
    urls = {}
    urls["delivery"] = BASE_URL + TIME_SERIES_DELIVERY
    urls["vaccination"] = BASE_URL + VACCINATION_STATE
    context["cwd"] = str(Path(sys.argv[0]).parent)

    # load last state
    sources = load_object(context)
    if sources is None:
        sources = Sources(urls["delivery"], urls["vaccination"])

    sources.download_sources()
    prepare_data(context, urls, sources.get_data())
    plot(context, sources)

    # store current state
    store_object(context, sources)


main()
