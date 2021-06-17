import logging
import re
from typing import Optional, Tuple

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

    return None


aoc = [
    "https://app.thestorygraph.com/books/70962fbf-178f-40f5-882d-510a9f46c70e", # Parable of the Sower
    "https://app.thestorygraph.com/books/c4dd9bd3-ac66-4c94-8381-c3bd7d570dfa", # An Unkindness of Ghosts
    "https://app.thestorygraph.com/books/b18844ef-15f7-493f-8724-fe32fec12771", # The Water Dancer
    "https://app.thestorygraph.com/books/eb739396-25fd-403e-8a88-ad0ec046d291", # The Underground Railroad
    "https://app.thestorygraph.com/books/367bcd99-cc75-4f49-94eb-4e1f27bff536", # Ring Shout
    "https://app.thestorygraph.com/books/984d51b1-bfb5-454e-8e9f-74f555dee9d6", # Dhalgren
    "https://app.thestorygraph.com/books/fa5eab26-ad2c-4fbf-9bdd-a220d763cb03", # Who Fears Death
    "https://app.thestorygraph.com/books/6faea454-48af-4b54-b4ec-71c08055c4ba", # Brown Girl in the Ring
    "https://app.thestorygraph.com/books/44f77705-feb2-4d46-b68a-192a7c46d9fe", # Version Control
    "https://app.thestorygraph.com/books/00dcca82-4ede-4700-880b-bc839cf11cc6"  # The Hundred Thousand Kingdoms
]

aow = [
    "https://app.thestorygraph.com/books/3a94ec7e-55c3-49d3-bb10-09e806eea299", # A Game of Thrones
    "https://app.thestorygraph.com/books/0ec18b47-1721-471d-9a0c-9f87164641a7", # The Name of the Wind
    "https://app.thestorygraph.com/books/ca07b067-8c64-4b8e-985c-52efc4b94f3e", # Gideon the Ninth
    "https://app.thestorygraph.com/books/7b81e26d-781a-4f06-bf90-08d50476901e", # Jhereg
    "https://app.thestorygraph.com/books/47d756b5-9a0b-440a-ba6c-26cc082b044c", # Jack the Bodiless
    "https://app.thestorygraph.com/books/905b4845-28a7-4025-8aec-98355bbfb8f9", # The City & the City
    "https://app.thestorygraph.com/books/0df3f760-2c94-440b-9299-7ced9100027b", # Upright Women Wanted
    "https://app.thestorygraph.com/books/4319278a-e266-41e0-9355-5515429d5df3", # A Wizard of Earthsea
    "https://app.thestorygraph.com/books/e69b1fe2-daae-4dc0-aa21-276bb31d0e08", # In the Garden of Iden
    "https://app.thestorygraph.com/books/c8ebb6f7-991e-4598-b3f5-ed65bede625f"  # The Atrocity Archive
]

#cws_c = pd.concat([get_cws(url) for url in aoc])
#cws_w = pd.concat([get_cws(url) for url in aow])


bookurl = "https://app.thestorygraph.com/books/397703ae-3ad2-4aa1-a07e-88f0bddef864" # The Henna Wars https://twitter.com/adiba_j/status/1404212450837344256

#cws = get_cws(bookurl)
reviews =  get_reviews(bookurl)

# TODO
# - normalize by # reviews
# - statistical comparisons over sets of books
# - uh logging config I guess

import pdb; pdb.set_trace()