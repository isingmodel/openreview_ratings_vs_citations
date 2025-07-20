import pandas as pd
import h5py
import time
import random
import numpy as np
from tqdm import tqdm
import json
import openreview


def parsing_openreview_hdf5(fn):
    """Parse an OpenReview hdf5 file and return a processed DataFrame."""
    ratings = []
    decisions = []
    titles = []

    with h5py.File(fn, "r") as f:
        for k in f.keys():
            ratings.append(f[k]["rating"][()])
            decisions.append(f[k]["decision"][()].decode("utf-8"))
            titles.append(f[k]["title"][()].decode("utf-8"))

    dict_for_df = {"rating": ratings, "decision": decisions, "title": titles}
    df = pd.DataFrame(dict_for_df)

    df_accept = (
        df.loc[(df.decision != "Reject") & (df.decision != "N/A")]
        .reset_index(drop=True)
    )

    df_accept["mean_rating"] = [np.mean(x) for x in df_accept.rating]
    df_accept["var_rating"] = [np.var(x) for x in df_accept.rating]

    return df_accept


def parsing_openreview(all_data):
    decisions = []
    titles = []
    authors_list = []
    ratings_list = []

    for forum in all_data:
        ratings = []
        decision = False
        authors = False

        for note in forum:
            if "authors" in note.content.keys():
                title = note.content["title"]
                authors = note.content["authors"]
            if 'decision' in note.content.keys():
                decision = note.content['decision']

            if 'rating' in note.content.keys():
                ratings.append(int(note.content['rating'].split(":")[0]))
                
        if not authors:
            print("no authors data")
            print(*forum)
            continue
            
        if len(ratings) == 0:
            print(title, "no review", "\n")
            print(*forum)
            continue
            
        if not decision:
            print(title, "no decision", "\n")
            continue
            

        decisions.append(decision)
        titles.append(title)
        authors_list.append(authors)
        ratings_list.append(ratings)

    summary = {"decision": decisions, "title": titles,
               "authors": authors_list, "rating": ratings_list}
    df = pd.DataFrame(summary)
    df = df.loc[df.decision != "Reject"].reset_index(drop=True)

    return df
    
    
def matching_openreview_googlescholar(citation_info, df):
    for pn, val in citation_info.items():
        df.loc[df.title == pn, "citations"] = val["num_citations"]
    return df


def get_paperinfo_from_google_scholar(title_list, apikey=None):

    """
      apikey: ScraperAPI key for scraping google scholar results. See https://www.scraperapi.com/

      It takes long long time for now.
      You can scrape without a proxy, but if you do, Google will (soft)block your IP.

    """
    from scholarly import scholarly, ProxyGenerator

    pg = ProxyGenerator()
    if apikey:
        API_KEY = apikey
        success = pg.ScraperAPI(API_KEY)
        scholarly.use_proxy(pg)

    citations_raw = {}

    for title in tqdm(title_list):
        try:
            aa = scholarly.search_pubs(title)
            data = next(aa) # the first result
            citations_raw[title] = data
        except:
            print(title, "error")
            
            
    for x in citations_raw.keys():
        del citations_raw[x]["source"]
        
    return citations_raw


def get_openreview_data(invitation_link='ICLR.cc/2018/Conference/-/Blind_Submission'):
    base_url = 'https://api.openreview.net'
    c = openreview.Client(baseurl=base_url)
    blind_notes = [note for note in openreview.tools.iterget_notes(c,
                                                                   invitation = invitation_link,
                                                                   details='original')]
    forum_list = set([h.forum for h in blind_notes])

    all_data = []
    for forum in tqdm(forum_list):
        forum_comments = c.get_notes(forum=forum)
        all_data.append(forum_comments)

    return all_data


