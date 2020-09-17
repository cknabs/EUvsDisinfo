# Scrape the euvsdisinfo.eu database and produce a .json of the entries
from csv import DictWriter
from datetime import datetime

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


class MalformedDataException(Exception):
    pass


def check(condition):
    if not condition:
        raise MalformedDataException


def extract(entries):
    POST_KEYS = ['date', 'id', 'title', 'countries', 'keywords', 'languages']
    ANNOTATION_KEYS = ['id', 'summary', 'disproof']
    PUBLICATION_KEYS = ['id', 'outlet', 'publication', 'archive']

    with open('posts.csv', 'w') as posts_file, \
            open('annotations.csv', 'w') as annotations_file, \
            open('publications.csv', 'w') as publications_file:
        posts_writer = DictWriter(posts_file, POST_KEYS)
        annotations_writer = DictWriter(annotations_file, ANNOTATION_KEYS)
        publications_writer = DictWriter(publications_file, PUBLICATION_KEYS)

        for post in entries:
            try:
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

                # Get data on publications from report page
                publications = report.find_all(attrs={'class': 'b-catalog__link'})
                languages = [lang.strip() for lang in report.find(text='Language/target audience:').next.split(',')]
                check(len(publications) == len(outlets))

                # Output data
                posts_writer.writerow({
                    'date': iso_date,
                    'id': id,
                    'title': title,
                    'countries': countries,
                    'keywords': keywords,
                    'languages': languages
                })

                annotations_writer.writerow({
                    'id': id,
                    'summary': summary,
                    'disproof': disproof
                })

                for article, outlet in zip(publications, outlets):
                    link, archived_link = [a['href'] for a in article.find_all('a')]
                    publications_writer.writerow({
                        'id': id,
                        'outlet': outlet,
                        'publication': link,
                        'archive': archived_link
                    })
            except MalformedDataException:
                print(f'WARNING: malformed data for {id}')
            except Exception as e:
                print(f'WARNING: encountered error {e} for {id}')


extract(all_entries())
