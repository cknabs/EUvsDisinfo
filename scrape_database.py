# Scrape the euvsdisinfo.eu database and produce a .json of the entries
import json
from datetime import datetime

import requests as req
from bs4 import BeautifulSoup

URL = 'https://euvsdisinfo.eu/disinformation-cases'

html = req.get(URL)
soup = BeautifulSoup(html.text, 'html.parser')


def get_data_columns(soup, data_col: str):
    return soup.find_all(None, attrs={'data-column': data_col})


def get_data_column(soup, data_col):
    data_columns = get_data_columns(soup, data_col)
    assert (len(data_columns) == 1)
    return data_columns[0]

# TODO: use API to scrape N entries, use date ranges, etc.
for post in soup.find_all('div', attrs={'class': 'disinfo-db-post'}):
    post_dict = {}
    d = get_data_column(post, 'Date').contents[0].strip()
    post_dict['date'] = datetime.strptime(d, '%d.%m.%Y').date().isoformat()
    title_link = get_data_column(post, 'Title').find('a')
    title = title_link.contents[0].strip()
    id = title_link['href']
    post_dict['title'] = title
    post_dict['id'] = id
    outlets = [o.strip() for o in get_data_column(post, 'Outlets').contents[0].split(',')]
    post_dict['outlets'] = outlets
    countries = [c.strip() for c in get_data_column(post, 'Country').contents[0].split(',')]
    post_dict['countries'] = countries

    # TODO: use `id' to get more info (language, article urls, summary, disproof)
    print(json.dumps(post_dict))
