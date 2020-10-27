import argparse
import csv
import sys
from datetime import date
from itertools import islice
from typing import List, Dict, Optional
from warnings import warn

from newspaper import Article, ArticleException

from util import list2str


class Publication:
    url: str = None
    title: str = None
    date: date = None
    language: str = None
    authors: List[str] = None
    text: str = None
    twitter: str = None
    facebook: str = None

    def __init__(self, url_: str):
        self.url = url_
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
        try:
            self.twitter = article.meta_data['twitter']['site']
        except KeyError:
            pass
        try:
            self.facebook = article.meta_data['article']['publisher']
        except KeyError:
            pass

    def to_str_dict(self) -> Dict[str, Optional[str]]:
        """Returns the extracted values as a dictionary where both keys and values are strings. """
        return {
            'url': self.url,
            'title': self.title,
            'date': str(self.date),
            'language': self.language,
            'authors': list2str(self.authors),
            'twitter': self.twitter,
            'facebook': self.facebook,
            'text': self.text
        }


if __name__ == '__main__':
    def check_non_negative(string: str) -> int:
        value = int(string)
        if value < 0:
            raise argparse.ArgumentTypeError(f"argument must be positive (was {value})")
        return value


    parser = argparse.ArgumentParser(description="Scrape publications listed in the euvsdisinfo.eu database. ")
    parser.add_argument('input', metavar='IN', nargs='?',
                        help="CSV file listing publications (default: stdin)",
                        type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('-o', '--output', metavar='OUT',
                        help="where to output the scraped results (default: stdout)",
                        type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-n', '--lines', metavar='N',
                        help="number of entries to scrape",
                        type=check_non_negative, default=None)

    args = parser.parse_args()
    with args.input as infile, args.output as outfile:
        reader = csv.DictReader(infile)
        writer = None
        for row in islice(reader, args.lines):
            pub_id = row['id']
            url = row['publication']

            publication = Publication(url)
            dict_pub = publication.to_str_dict()
            del dict_pub['text']
            dict_pub['id'] = pub_id

            if writer is None:
                writer = csv.DictWriter(outfile, fieldnames=dict_pub.keys())
                writer.writeheader()
            writer.writerow(dict_pub)
