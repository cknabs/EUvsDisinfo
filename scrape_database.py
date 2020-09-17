# Scrape the euvsdisinfo.eu database and produce a .json of the entries
from csv import DictWriter
from datetime import datetime
from typing import List, Tuple

import requests as req
from bs4 import BeautifulSoup

URL = 'https://euvsdisinfo.eu/disinformation-cases'


def get_data_column(soup, data_col):
    data_columns = soup.find_all(None, attrs={'data-column': data_col})
    assert (len(data_columns) == 1)
    return data_columns[0]


def all_entries():
    offset = 0
    while True:
        html = req.get(URL, params={'offset': offset, 'per_page': 100})
        soup = BeautifulSoup(html.text, 'html.parser')
        all_posts = soup.find_all('div', attrs={'class': 'disinfo-db-post'})
        if len(all_posts) == 0:
            return
        for post in all_posts:
            yield post
            offset += 1


class Entry:
    iso_date: str
    title: str
    id: str
    outlets: List[str]
    countries: List[str]
    keywords: List[str]
    summary: str
    disproof: str
    languages: List[str]
    publications: List[Tuple[str, str]]

    def __init__(self, entry):
        try:
            # Get basic data from database entry
            date = get_data_column(entry, 'Date').contents[0].strip()
            self.iso_date = datetime.strptime(date, '%d.%m.%Y').date().isoformat()
            title_link = get_data_column(entry, 'Title').find('a')
            self.title = title_link.contents[0].strip()
            self.id = title_link['href']

            self.outlets = [o.strip() for o in get_data_column(entry, 'Outlets').contents[0].split(',')]
            self.countries = [c.strip() for c in get_data_column(entry, 'Country').contents[0].split(',')]
        except Exception as exception:
            raise MalformedDataError('malformed entry error', self.id) from exception

        try:
            # Get keywords, summary, disproof from report page
            report = BeautifulSoup(req.get(self.id).text, 'html.parser')

            self.keywords = report.find(text='Keywords:').parent.parent.contents[-1].strip()
            self.summary = report.find(attrs={'class': 'b-report__summary-text'}).text.strip()
            self.disproof = report.find(attrs={'class': 'b-report__disproof-text'}).text.strip()
        except Exception as exception:
            raise MalformedDataError('malformed report error', self.id) from exception

        try:
            # Get data on publications from report page
            publications = report.find_all(attrs={'class': 'b-catalog__link'})
            self.languages = [lang.strip() for lang in report.find(text='Language/target audience:').next.split(',')]
            assert (len(publications) == len(self.outlets))

            self.publications = []
            for publication in publications:
                links = [a['href'] for a in publication.find_all('a')]
                assert 0 < len(links) <= 2
                l1, l2 = links[0], links[1] if len(links) == 2 else None
                self.publications.append((l1, l2))
        except Exception as exception:
            raise MalformedDataError('malformed publications error', self.id) from exception


class MalformedDataError(Exception):
    def __init__(self, message: str, id: str):
        self.message = message
        self.id = id


def extract(entries):
    post_keys = ['date', 'id', 'title', 'countries', 'keywords', 'languages']
    annotation_keys = ['id', 'summary', 'disproof']
    publication_keys = ['id', 'outlet', 'publication', 'archive']

    with open('posts.csv', 'w') as posts_file, \
            open('annotations.csv', 'w') as annotations_file, \
            open('publications.csv', 'w') as publications_file:
        posts_writer = DictWriter(posts_file, post_keys)
        posts_writer.writeheader()
        annotations_writer = DictWriter(annotations_file, annotation_keys)
        annotations_writer.writeheader()
        publications_writer = DictWriter(publications_file, publication_keys)
        publications_writer.writeheader()

        for entry_html in entries:
            try:
                entry = Entry(entry_html)
            except MalformedDataError as mde:
                print(f'WARNING: {repr(mde)} from {repr(mde.__cause__)}')

            posts_writer.writerow({
                'date': entry.iso_date,
                'id': entry.id,
                'title': entry.title,
                'countries': entry.countries,
                'keywords': entry.keywords,
                'languages': entry.languages
            })

            annotations_writer.writerow({
                'id': entry.id,
                'summary': entry.summary,
                'disproof': entry.disproof
            })

            for publication, outlet in zip(entry.publications, entry.outlets):
                link, archived_link = publication
                publications_writer.writerow({
                    'id': entry.id,
                    'outlet': outlet,
                    'publication': link,
                    'archive': archived_link
                })


extract(all_entries())
