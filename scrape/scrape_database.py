# Scrape the euvsdisinfo.eu database and produce a .json of the entries
import argparse
import logging
from csv import DictWriter
from datetime import date, datetime
from itertools import islice
from multiprocessing import Pool
from typing import Generator, List, Tuple, Union

import requests as req
from bs4 import BeautifulSoup
from tqdm import tqdm
from util import check_non_negative, list2str

URL = "https://euvsdisinfo.eu/disinformation-cases"
LOGGER = logging.getLogger(__name__)


def all_entries() -> Generator:
    """Generator, yields all entries"""
    offset = 0
    while True:
        html = req.get(URL, params={"offset": offset, "per_page": 100})
        soup = BeautifulSoup(html.text, "html.parser")
        all_posts = soup.find_all(attrs={"class": "disinfo-db-post"})
        if len(all_posts) == 0:
            return
        for post in all_posts:
            yield post
            offset += 1


def get_total_entries() -> int:
    html = req.get(URL)
    soup = BeautifulSoup(html.text, "html.parser")
    return int(
        soup.find(attrs={"class": "disinfo-db-results"})
        .find("span")
        .contents[0]
    )


class Entry:
    date: date
    title: str = ""
    id: str = ""
    outlets: List[str] = []
    countries: List[str] = []

    def __init__(self, entry):
        # Get basic data from database entry
        try:
            date_str = self.get_data_column(entry, "Date").contents[0].strip()
            self.date = datetime.strptime(date_str, "%d.%m.%Y").date()
            title_link = self.get_data_column(entry, "Title").find("a")
            self.title = title_link.contents[0].strip()
            self.id = title_link["href"]

            self.outlets = [
                o.strip()
                for o in self.get_data_column(entry, "Outlets")
                .contents[0]
                .split(",")
            ]
            self.countries = [
                c.strip()
                for c in self.get_data_column(entry, "Country")
                .contents[0]
                .split(",")
            ]
        except Exception as exception:
            raise MalformedDataError(
                "Malformed entry error", self.id
            ) from exception

    @staticmethod
    def get_data_column(soup: BeautifulSoup, data_col):
        data_columns = soup.find_all(None, attrs={"data-column": data_col})
        assert len(data_columns) == 1
        return data_columns[0]


class Report:
    entry: Entry
    id: str = ""
    keywords: List[str] = []
    summary: str = ""
    disproof: str = ""
    languages: List[str] = []
    publications: List[Tuple[str, str]] = []

    def __init__(self, entry: Entry):
        self.entry = entry
        self.id = self.entry.id

        # Get keywords, summary, disproof from report page
        try:
            report = BeautifulSoup(req.get(self.id).text, "html.parser")

            try:
                self.keywords = [
                    k.strip()
                    for k in report.find(
                        text="Keywords:"
                    ).parent.next.next.split(",")
                ]
            except AttributeError:
                self.warn_missing("keywords")
            try:
                self.summary = report.find(
                    attrs={"class": "b-report__summary-text"}
                ).text.strip()
            except AttributeError:
                self.warn_missing("summary")
            try:
                self.disproof = report.find(
                    attrs={"class": "b-report__disproof-text"}
                ).text.strip()
            except AttributeError:
                self.warn_missing("disproof")
        except Exception as exception:
            raise MalformedDataError(
                "Malformed report error", self.id
            ) from exception

        # Get data on publications from report page
        try:
            try:
                self.languages = [
                    lang.strip()
                    for lang in report.find(
                        text="Language/target audience:"
                    ).next.split(",")
                ]
            except AttributeError:
                self.warn_missing("languages")

            publications = report.find_all(attrs={"class": "b-catalog__link"})
            self.publications = []
            for publication in publications:
                links = [a["href"] for a in publication.find_all("a")]
                assert 0 < len(links) <= 2
                l1, l2 = links[0], links[1] if len(links) == 2 else None
                self.publications.append((l1, l2))
        except Exception as exception:
            raise MalformedDataError(
                "Malformed publications error", self.id
            ) from exception

    def warn_missing(self, name: str):
        LOGGER.warning(f"Missing data '{name}' for {self.id}")


class MalformedDataError(Exception):
    def __init__(self, message: str, id_: str):
        self.message = message
        self.id = id_


def get_entry(entry_html) -> Union[Entry, None]:
    """Wrapper for :class:`Entry` initialization, return None on error.
    Defined here to be picklable.
    """
    try:
        return Entry(entry_html)
    except MalformedDataError as mde:
        LOGGER.warning(f"WARNING: {repr(mde)} from {repr(mde.__cause__)}")
    return None


def get_report(entry: Entry) -> Union[Report, None]:
    """Wrapper for :class:`Report` initialization, return None on error.
    Defined here to be picklable.
    """
    try:
        return Report(entry)
    except MalformedDataError as mde:
        LOGGER.warning(f"WARNING: {repr(mde)} from {repr(mde.__cause__)}")
    return None


def extract(
    entries_html, posts_out, annotations_out, publications_out, n_jobs
):
    post_keys = [
        "date",
        "id",
        "title",
        "countries",
        "keywords",
        "languages",
        "outlets",
    ]
    annotation_keys = ["id", "summary", "disproof"]
    publication_keys = ["id", "publication", "archive"]

    posts_writer = DictWriter(posts_out, post_keys)
    posts_writer.writeheader()
    annotations_writer = DictWriter(annotations_out, annotation_keys)
    annotations_writer.writeheader()
    publications_writer = DictWriter(publications_out, publication_keys)
    publications_writer.writeheader()

    pool = Pool(n_jobs)
    entries = filter(lambda o: o is not None, map(get_entry, entries_html))

    for report in filter(
        lambda o: o is not None, pool.imap(get_report, entries)
    ):
        entry = report.entry

        posts_writer.writerow(
            {
                "date": entry.date,
                "id": entry.id,
                "title": entry.title,
                "countries": list2str(entry.countries),
                "keywords": list2str(report.keywords),
                "languages": list2str(report.languages),
                "outlets": list2str(entry.outlets),
            }
        )

        annotations_writer.writerow(
            {
                "id": report.id,
                "summary": report.summary,
                "disproof": report.disproof,
            }
        )

        for link, archived_link in report.publications:
            publications_writer.writerow(
                {
                    "id": report.id,
                    "publication": link,
                    "archive": archived_link,
                }
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape entries listed in the euvsdisinfo.eu database. "
    )
    parser.add_argument(
        "posts",
        metavar="POSTS",
        help="where to output the scraped posts",
        type=argparse.FileType("w"),
    )
    parser.add_argument(
        "annotations",
        metavar="ANNOTATIONS",
        help="where to output the scraped annotations",
        type=argparse.FileType("w"),
    )
    parser.add_argument(
        "publications",
        metavar="PUBLICATIONS",
        help="where to output the scraped publications list",
        type=argparse.FileType("w"),
    )

    parser.add_argument(
        "-n",
        "--lines",
        metavar="N",
        help="number of entries to scrape",
        type=check_non_negative,
        default=None,
    )
    parser.add_argument(
        "-j",
        "--jobs",
        metavar="N",
        help="number of jobs to use (default: %(default)s)",
        type=check_non_negative,
        default=10,
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

    with args.posts as posts_file, args.annotations as annotations_file, args.publications as publications_file:

        iterator = islice(all_entries(), args.lines)
        if args.show_progress:
            total_entries = (
                get_total_entries() if args.lines is None else args.lines
            )
            iterator = tqdm(iterator, total=total_entries)

        extract(
            iterator,
            posts_out=posts_file,
            annotations_out=annotations_file,
            publications_out=publications_file,
            n_jobs=args.jobs,
        )
