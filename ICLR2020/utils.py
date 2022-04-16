import pandas as pd
import h5py
import time
import random
import numpy as np


def parsing_openreview_hdf5():
    fn = "./data/openreview_data_20191223.hdf5"
    f = h5py.File(fn, 'r')

    c = 0

    ratings = []
    decisions = []
    titles = []
    authors = []

    for k in f.keys():
        ratings.append(f[k]['rating'][()])
        authors.append(f[k]['author'][()])
        decisions.append(f[k]['decision'][()].decode("utf-8"))
        titles.append(f[k]['title'][()].decode("utf-8"))

        
    dict_for_df = {"rating": ratings, "decision": decisions,
                   "authors": authors, "title": titles}
    df = pd.DataFrame(dict_for_df)

    # One paper has changed its title.
    name_after = "Learning from Unlabelled Videos Using Contrastive Predictive Neural 3D Mapping"
    name_before = "Visual Representation Learning With 3d View-constrastive Inverse Graphics Networks"
    df.loc[df.title == name_before, "title"] = name_after

    df_accept = df.loc[(df.decision != "Reject") &(df.decision != "N/A")].reset_index(drop=True)

    df_accept["mean_rating"] = [np.mean(x) for x in df_accept.rating]
    df_accept["var_rating"] = [np.var(x) for x in df_accept.rating]

    return df_accept




def get_paperinfo_from_google_scholar(title_list, saving_path, apikey):

    """
      apikey: ScraperAPI key for scraping google scholar results. See https://www.scraperapi.com/

      It takes long long time for now.
      You can scrape without a proxy, but if you do, Google will (soft)block your IP.

    """

    # todo: use async
    from scholarly import scholarly, ProxyGenerator

    pg = ProxyGenerator()
    API_KEY = apikey
    success = pg.ScraperAPI(API_KEY)
    scholarly.use_proxy(pg)

    citations_raw = {}

    for c, title in enumerate(title_list):
        try:
            aa = scholarly.search_pubs(title)
            data = next(aa) # the first result
            citations_raw[title] = data
        except Error as e:
            print(e, title)
            
            
    for x in citations_raw.keys():
        del citations_raw[x]["source"]
        
        
    with open(saving_path,'w') as f:
        json.dump(citations_raw,f)


        