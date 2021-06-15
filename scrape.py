import logging
from typing import Tuple

import pandas as pd
import requests
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


bookurl = "https://app.thestorygraph.com/books/397703ae-3ad2-4aa1-a07e-88f0bddef864" # The Henna Wars https://twitter.com/adiba_j/status/1404212450837344256

cws = get_cws(bookurl)

# TODO
# - normalize by # reviews
# - statistical comparisons over sets of books

import pdb; pdb.set_trace()