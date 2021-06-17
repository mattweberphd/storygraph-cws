import logging
import re
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
from bs4 import BeautifulSoup

class BadContentWarningError(ValueError):
    """
    Error for content warnings that fail parse_cw()
    """
    pass


def parse_cw(cw: str) -> Tuple[str, int]:
    """
    From a content warning built like e.g. "Religious bigotry (1)" return a
    tuple of (warning, count) e.g. ("Religious bigotry", 1)
    """
    try:
        warning, countparens = cw.split("(")
    except BadContentWarningError:
        logging.error("Warning {cw} not parsed correctly by parse_cw()")
        raise

    count = int(countparens[0:-1])

    return warning, count


def get_cws(url: str) -> pd.DataFrame:
    """
    Given a book URL, find the content warning URL and pull content warnings
    and counts into a nice DataFrame.
    """
    cwurl = f"{url}/content_warnings"

    html = requests.get(cwurl).text

    soup = BeautifulSoup(html, "html.parser")

    cwpane = soup.find_all("div", class_="standard-pane")[1]

    dfs = []

    for level in cwpane.find_all("p"):
        cws = []
        for tag in level.next_siblings:
            # parse cws from links and assign them to this level -- i.e., do this DataFrame stuff below separately for each level
            if tag.name == "div":
                link = tag.find("a")
                if "content_warning" not in link.get("href"):
                    continue
                cws.append(parse_cw(link.text))

        df = pd.DataFrame.from_records(cws, columns=["CW", "Count"])
        df["Level"] = level.text
        dfs.append(df)

    df = pd.concat(dfs).reset_index(drop=True)

    return df


def get_reviews(url: str) -> Optional[int]:
    """
    Pull reviews from a StoryGraph book URL
    """
    html = requests.get(url).text

    soup = BeautifulSoup(html, "html.parser")

    p_reviews = soup.find_all("p", class_="italic text-sm mb-4")

    regex = "summary of (\d+) ratings"

    for para in p_reviews:
        match_ = re.match(regex, para.text)
        if match_:
            return int(match_.group(1))

    raise ValueError(f"No reviews found on {url}")


def get_ratings(url: str) -> Optional[float]:
    """
    Pull ratings from a StoryGraph URL
    """
    html = requests.get(url).text

    soup = BeautifulSoup(html, "html.parser")

    spans = soup.find_all("span", class_="average-star-rating")

    for span in spans:
        try:
            rating = float(span.text)
        except ValueError:
            continue

        return rating

    raise ValueError(f"No ratings found on {url}")

sources = {
    "AOC": {
        "https://app.thestorygraph.com/books/70962fbf-178f-40f5-882d-510a9f46c70e": "Parable of the Sower",
        "https://app.thestorygraph.com/books/c4dd9bd3-ac66-4c94-8381-c3bd7d570dfa": "An Unkindness of Ghosts",
        "https://app.thestorygraph.com/books/b18844ef-15f7-493f-8724-fe32fec12771": "The Water Dancer",
        "https://app.thestorygraph.com/books/eb739396-25fd-403e-8a88-ad0ec046d291": "The Underground Railroad",
        "https://app.thestorygraph.com/books/367bcd99-cc75-4f49-94eb-4e1f27bff536": "Ring Shout",
        "https://app.thestorygraph.com/books/984d51b1-bfb5-454e-8e9f-74f555dee9d6": "Dhalgren",
        "https://app.thestorygraph.com/books/fa5eab26-ad2c-4fbf-9bdd-a220d763cb03": "Who Fears Death",
        "https://app.thestorygraph.com/books/6faea454-48af-4b54-b4ec-71c08055c4ba": "Brown Girl in the Ring",
        "https://app.thestorygraph.com/books/44f77705-feb2-4d46-b68a-192a7c46d9fe": "Version Control",
        "https://app.thestorygraph.com/books/00dcca82-4ede-4700-880b-bc839cf11cc6": "The Hundred Thousand Kingdoms"
    },
    "AOW": {
        "https://app.thestorygraph.com/books/3a94ec7e-55c3-49d3-bb10-09e806eea299": "A Game of Thrones",
        "https://app.thestorygraph.com/books/0ec18b47-1721-471d-9a0c-9f87164641a7": "The Name of the Wind",
        "https://app.thestorygraph.com/books/ca07b067-8c64-4b8e-985c-52efc4b94f3e": "Gideon the Ninth",
        "https://app.thestorygraph.com/books/fb359497-14f2-435e-8ca6-d95251622919": "Annihilation",
        "https://app.thestorygraph.com/books/9d7fd57f-89be-4afa-8190-d8b398997eb1": "The Only Harmless Great Thing",
        "https://app.thestorygraph.com/books/cf6d23b9-b348-4819-9e37-e520a5d41723": "Perdido Street Station",
        "https://app.thestorygraph.com/books/0df3f760-2c94-440b-9299-7ced9100027b": "Upright Women Wanted",
        "https://app.thestorygraph.com/books/4319278a-e266-41e0-9355-5515429d5df3": "A Wizard of Earthsea",
        "https://app.thestorygraph.com/books/ed0a2053-0859-46d3-bbc0-450101fa6060": "Deathless",
        "https://app.thestorygraph.com/books/c8ebb6f7-991e-4598-b3f5-ed65bede625f": "The Atrocity Archive"
    }
}

logging.basicConfig(level=logging.DEBUG)

dfs = []

for cohort, urls in sources.items():
    for url, title in urls.items():

        logging.info(f"Retrieving data for {title}...")

        cws = get_cws(url)
        reviews = get_reviews(url)
        rating = get_ratings(url)
        cws["Title"] = title
        cws["Cohort"] = cohort
        cws["Reviews"] = reviews
        cws["Rating"] = rating

        dfs.append(cws)

df = pd.concat(dfs)

df["Normed CW count"] = df["Count"] / df["Reviews"]

npb = df.groupby("Title").aggregate({"Count": np.sum, "Normed CW count": np.sum, "Cohort": np.max})

for measure in ("Count", "Normed CW Count"):
    ax = sns.boxplot(x=measure, y="Cohort", data=npb, whis=np.inf, palette="pastel")
    ax = sns.swarmplot(x=measure, y="Cohort", data=npb, color=".2")
    savename = measure.replace(" ", "-")
    plt.savefig(f"{savename}.png")

import pdb; pdb.set_trace()