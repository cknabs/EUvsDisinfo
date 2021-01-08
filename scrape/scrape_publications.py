import argparse
import csv
import datetime
import logging
import sys
from itertools import islice
from typing import Dict, List, Optional

from newspaper import Article, ArticleException
from tqdm import tqdm
from util import check_non_negative, list2str

LOGGER = logging.getLogger(__name__)


class Publication:
    url: str = None
    title: str = None
    date: datetime.date = None
    language: str = None
    authors: List[str] = []
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
            LOGGER.warning(f"Could not retrieve publication {self.url}: {e}")
            return
        self.title = article.title
        self.date = (
            article.publish_date.date()
            if article.publish_date is not None
            else None
        )
        self.language = article.meta_lang
        self.authors = article.authors
        self.text = article.text
        try:
            self.twitter = article.meta_data["twitter"]["site"]
        except KeyError:
            pass
        try:
            self.facebook = article.meta_data["article"]["publisher"]
        except KeyError:
            pass

    def to_str_dict(self) -> Dict[str, Optional[str]]:
        """Returns the extracted values as a dictionary where both keys and values are strings. """
        return {
            "url": self.url,
            "title": self.title,
            "date": str(self.date),
            "language": self.language,
            "authors": list2str(self.authors),
            "twitter": self.twitter,
            "facebook": self.facebook,
            "text": self.text,
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape publications listed in the euvsdisinfo.eu database. "
    )
    parser.add_argument(
        "input",
        metavar="IN",
        nargs="?",
        help="CSV file listing publications (default: stdin)",
        type=argparse.FileType("r"),
        default=sys.stdin,
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="OUT",
        help="where to output the scraped results (default: stdout)",
        type=argparse.FileType("w"),
        default=sys.stdout,
    )
    parser.add_argument(
        "-n",
        "--lines",
        metavar="N",
        help="number of publications to scrape",
        type=check_non_negative,
        default=None,
    )

    group = parser.add_argument_group("verbosity arguments")
    group_warnings = group.add_mutually_exclusive_group()
    group_warnings.add_argument(
        "-w",
        "--show-warnings",
        dest="show_warnings",
        help="show warnings",
        action="store_true",
        default=False,
    )
    group_warnings.add_argument(
        "-nw",
        "--no-warnings",
        dest="show_warnings",
        help="hide warnings (default)",
        action="store_false",
    )
    group_progress = group.add_mutually_exclusive_group()
    group_progress.add_argument(
        "-p",
        "--show-progress",
        dest="show_progress",
        help="show progress bar (default)",
        action="store_true",
        default=True,
    )
    group_progress.add_argument(
        "-np",
        "--no-progress",
        dest="show_progress",
        help="hide progress bar",
        action="store_false",
    )

    args = parser.parse_args()
    if not args.show_warnings:
        LOGGER.setLevel(logging.ERROR)

    with args.input as infile, args.output as outfile:
        reader = csv.DictReader(infile)

        iterator = islice(reader, args.lines)
        if args.show_progress:
            if infile == sys.stdin:
                total_lines = None
            elif args.lines is not None:
                total_lines = args.lines
            else:
                total_lines = sum(1 for _ in reader)
                infile.seek(0)
                reader = csv.DictReader(infile)
            iterator = tqdm(iterator, total=total_lines)
        writer = None
        for row in iterator:
            pub_id = row["id"]
            url = row["publication"]

            publication = Publication(url)
            dict_pub = publication.to_str_dict()
            del dict_pub["text"]
            dict_pub["id"] = pub_id

            if writer is None:
                writer = csv.DictWriter(outfile, fieldnames=dict_pub.keys())
                writer.writeheader()
            writer.writerow(dict_pub)
