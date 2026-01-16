"""Utility functions for processing OpenReview data."""

from __future__ import annotations

import logging
from typing import Iterable, List, Tuple

import h5py
import numpy as np
import openreview
import pandas as pd
from tqdm import tqdm

__all__ = [
    "parse_openreview_hdf5",
    "parse_openreview",
    "match_openreview_googlescholar",
    "get_paperinfo_from_google_scholar",
    "get_openreview_data",
]

logger = logging.getLogger(__name__)


def parse_openreview_hdf5(filename: str) -> pd.DataFrame:
    """Return accepted submissions with rating statistics from an HDF5 file."""
    with h5py.File(filename, "r") as f:
        df = pd.DataFrame(
            {
                "rating": [f[k]["rating"][()] for k in f.keys()],
                "decision": [
                    f[k]["decision"][()].decode("utf-8") for k in f.keys()
                ],
                "title": [f[k]["title"][()].decode("utf-8") for k in f.keys()],
            }
        )

    accepted = df.loc[(df.decision != "Reject") & (df.decision != "N/A")]
    accepted = accepted.reset_index(drop=True)
    accepted["mean_rating"] = accepted["rating"].apply(np.mean)
    accepted["var_rating"] = accepted["rating"].apply(np.var)
    return accepted


def _extract_forum_data(forum) -> Tuple[str, List[str], List[int], str] | None:
    """Return basic information from a forum or ``None`` if incomplete."""
    title = None
    authors = None
    ratings: List[int] = []
    decision = None

    for note in forum:
        content = note.content
        if "authors" in content:
            title = content.get("title")
            authors = content["authors"]
        if "decision" in content:
            decision = content["decision"]
        if "rating" in content:
            ratings.append(int(content["rating"].split(":")[0]))

    if not authors:
        logger.warning("No authors data for forum %s", forum)
        return None
    if not ratings:
        logger.warning("%s has no review", title)
        return None
    if not decision:
        logger.warning("%s has no decision", title)
        return None

    return title, authors, ratings, decision


def parse_openreview(all_data: Iterable) -> pd.DataFrame:
    """Parse a list of forums returned from :func:`get_openreview_data`."""
    records = []

    for forum in all_data:
        result = _extract_forum_data(forum)
        if result is None:
            continue
        title, authors, ratings, decision = result
        records.append(
            {
                "decision": decision,
                "title": title,
                "authors": authors,
                "rating": ratings,
            }
        )

    df = pd.DataFrame(records)
    df = df.loc[df.decision != "Reject"].reset_index(drop=True)
    return df


def match_openreview_googlescholar(
    citation_info: dict, df: pd.DataFrame
) -> pd.DataFrame:
    """Insert citation counts from Google Scholar into the OpenReview DataFrame."""
    for pn, val in citation_info.items():
        df.loc[df.title == pn, "citations"] = val.get("num_citations")
    return df


def get_paperinfo_from_google_scholar(
    title_list: Iterable[str], apikey: str | None = None
) -> dict:
    """Return Google Scholar metadata for each title.

    ``apikey`` -- ScraperAPI key for proxying Google Scholar requests.
    It can take a long time and scraping without a proxy may lead to your IP being
    soft-blocked by Google.
    """
    from scholarly import scholarly, ProxyGenerator

    pg = ProxyGenerator()
    if apikey:
        pg.ScraperAPI(apikey)
        scholarly.use_proxy(pg)

    citations_raw: dict = {}

    for title in tqdm(title_list):
        try:
            aa = scholarly.search_pubs(title)
            data = next(aa)  # the first result
            citations_raw[title] = data
        except:
            print(title, "error")

    for x in citations_raw.keys():
        del citations_raw[x]["source"]

    return citations_raw


def get_openreview_data(
    invitation_link: str = "ICLR.cc/2018/Conference/-/Blind_Submission",
) -> list:
    """Download forums from OpenReview for the given invitation."""
    base_url = "https://api.openreview.net"
    client = openreview.Client(baseurl=base_url)

    blind_notes = list(
        openreview.tools.iterget_notes(
            client, invitation=invitation_link, details="original"
        )
    )
    forum_list = {note.forum for note in blind_notes}

    all_data = []
    for forum in tqdm(forum_list):
        forum_comments = client.get_notes(forum=forum)
        all_data.append(forum_comments)

    return all_data
