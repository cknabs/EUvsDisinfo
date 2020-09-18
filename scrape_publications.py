import argparse
import csv
import sys
from datetime import date
from typing import List
from warnings import warn

from newspaper import Article, ArticleException


class Publication:
    url: str
    title: str
    date: date
    language: str
    authors: List[str]
    text: str

    def __init__(self, url):
        self.url = url
        try:
            article = Article(self.url)
            article.download()
            article.parse()
        except ArticleException as e:
            warn(f"Could not retrieve publication {self.url}: {e}")
            return

        self.title = article.title
        self.date = article.publish_date.date() if article.publish_date is not None else None
        self.language = article.meta_lang
        self.authors = article.authors
        self.text = article.text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scrape publications listed in the euvsdisinfo.eu database. ")
    parser.add_argument('-i', metavar='infile', help="CSV file listing publications",
                        type=argparse.FileType('r'), default='publications.csv')
    parser.add_argument('-o', metavar='outfile', help="output file", type=argparse.FileType('w'),
                        default=sys.stdout)

    args = parser.parse_args()
    with args.i as infile, \
            args.o as outfile:
        reader = csv.DictReader(infile)
        writer = None
        for row in reader:
            pub_id = row['id']
            url = row['publication']
            publication = Publication(url)
            dict_pub = vars(publication)
            if writer is None:
                writer = csv.DictWriter(outfile, fieldnames=dict_pub.keys())
                writer.writeheader()
            writer.writerow(dict_pub)
