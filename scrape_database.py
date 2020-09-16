# Scrape the euvsdisinfo.eu database and produce a .json of the entries
from csv import DictWriter
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
POST_KEYS = ['date', 'id', 'title', 'countries', 'keywords']
ANNOTATION_KEYS = ['id', 'summary', 'disproof']
PUBLICATION_KEYS = ['id', 'language', 'outlet', 'publication', 'archive']
with open('posts.csv', 'w') as posts_file, \
        open('annotations.csv', 'w') as annotations_file, \
        open('publications.csv', 'w') as publications_file:
    posts_writer = DictWriter(posts_file, POST_KEYS)
    annotations_writer = DictWriter(annotations_file, ANNOTATION_KEYS)
    publications_writer = DictWriter(publications_file, PUBLICATION_KEYS)

    for post in soup.find_all('div', attrs={'class': 'disinfo-db-post'}):
        # Get basic data from database entry
        date = get_data_column(post, 'Date').contents[0].strip()
        iso_date = datetime.strptime(date, '%d.%m.%Y').date().isoformat()
        title_link = get_data_column(post, 'Title').find('a')
        title = title_link.contents[0].strip()
        id = title_link['href']

        outlets = [o.strip() for o in get_data_column(post, 'Outlets').contents[0].split(',')]
        countries = [c.strip() for c in get_data_column(post, 'Country').contents[0].split(',')]

        # Get keywords, summary, disproof from report page
        report = BeautifulSoup(req.get(id).text, 'html.parser')

        keywords = report.find(text='Keywords:').parent.parent.contents[-1].strip()
        summary = report.find(attrs={'class': 'b-report__summary-text'}).text.strip()
        disproof = report.find(attrs={'class': 'b-report__disproof-text'}).text.strip()

        # Get data on articles from report page
        articles = report.find_all(attrs={'class': 'b-catalog__link'})
        languages = [l.strip() for l in report.find(text='Language/target audience:').next.split(',')]
        assert (len(articles) == len(languages))
        assert (len(articles) == len(outlets))

        # Output data

        posts_writer.writerow({
            'date': iso_date,
            'id': id,
            'title': title,
            'countries': countries,
            'keywords': keywords
        })

        annotations_writer.writerow({
            'id': id,
            'summary': summary,
            'disproof': disproof
        })

        for article, outlet, language in zip(articles, outlets, languages):
            link, archived_link = [a['href'] for a in article.find_all('a')]
            publications_writer.writerow({
                'id': id,
                'language': language,
                'outlet': outlet,
                'publication': link,
                'archive': archived_link
            })
