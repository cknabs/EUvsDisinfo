# Scrape the euvsdisinfo.eu database and produce a .json of the entries
import argparse
import logging
import urllib.error
import urllib.parse
from collections import namedtuple
from csv import DictWriter
from datetime import date, datetime
from itertools import islice
from multiprocessing import Pool
from pathlib import Path
from typing import Generator, Iterator, List, Optional, Tuple

import requests
import requests as req
import urllib3
from bs4 import BeautifulSoup
from tqdm import tqdm
from util import LIST_SEPARATOR, check_non_negative, stringify

URL = "https://euvsdisinfo.eu/disinformation-cases"
LOGGER = logging.getLogger(__name__)
POSTS_FILENAME = "posts.csv"
PUBLICATIONS_FILENAME = "publications.csv"
ANNOTATIONS_FILENAME = "annotations.csv"

Post = namedtuple(
    "Post",
    [
        "date",
        "id",
        "title",
        "countries",
        "keywords",
        "languages",
        "outlets",
    ],
)
Annotation = namedtuple(
    "Annotation",
    [
        "id",
        "summary",
        "disproof",
        "summary_links",
        "summary_links_resolved",
        "disproof_links",
        "disproof_links_resolved",
    ],
)
Publication = namedtuple("Publication", ["id", "publication", "archive"])


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

            self.outlets = self.get_strings_for_col(entry, "Outlets")
            self.countries = self.get_strings_for_col(
                entry, "Country", separator=","
            )
        except Exception as exception:
            raise MalformedDataError(
                "Malformed entry error", self.id
            ) from exception

    @classmethod
    def get_data_column(cls, soup: BeautifulSoup, data_col):
        data_columns = soup.find_all(None, attrs={"data-column": data_col})
        assert len(data_columns) == 1
        return data_columns[0]

    @classmethod
    def get_strings_for_col(
        cls, soup: BeautifulSoup, col_name: str, separator=None
    ) -> List[str]:
        data_col = cls.get_data_column(soup, col_name)
        strings = [str(s).strip() for s in data_col.strings]
        if separator is not None:
            strings = [
                s.strip() for lst in strings for s in lst.split(separator)
            ]
        return [s for s in strings if len(s) > 0]


class Report:
    entry: Entry
    id: str = ""
    keywords: List[str] = []
    summary: str = ""
    disproof: str = ""
    summary_links: List[str] = []
    summary_links_resolved: List[str] = []
    disproof_links: List[str] = []
    disproof_links_resolved: List[str] = []
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
                summary_container = report.find(
                    attrs={"class": "b-report__summary-text"}
                )
                self.summary = summary_container.text.strip()
                links = [a["href"] for a in summary_container.find_all("a")]
                self.summary_links = [self.url_encode(link) for link in links]
                self.summary_links_resolved = [
                    self.url_encode(self.resolve_link(link)) for link in links
                ]
            except AttributeError:
                self.warn_missing("summary")
            try:
                disproof_container = report.find(
                    attrs={"class": "b-report__disproof-text"}
                )
                self.disproof = disproof_container.text.strip()
                links = [a["href"] for a in disproof_container.find_all("a")]
                self.disproof_links = [self.url_encode(link) for link in links]
                self.disproof_links_resolved = [
                    self.url_encode(self.resolve_link(link)) for link in links
                ]
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

    @staticmethod
    def resolve_link(url: str) -> str:
        try:
            response = requests.head(url, allow_redirects=True)
            if response.status_code == 200:
                return response.url
            else:
                return str(response.status_code)
        except (
            urllib3.exceptions.HTTPError,
            requests.exceptions.RequestException,
        ) as e:
            # urllib3.exceptions.HTTPError needs to be caught, see https://github.com/psf/requests/issues/5744
            return type(e).__name__

    @staticmethod
    def url_encode(url: str) -> str:
        try:
            return urllib.parse.quote(url)
        except urllib.error.URLError as e:
            return type(e).__name__


class MalformedDataError(Exception):
    def __init__(self, message: str, id_: str):
        self.message = message
        self.id = id_


def get_entry(entry_html) -> Optional[Entry]:
    """Wrapper for :class:`Entry` initialization, return None on error.
    Defined here to be picklable.
    """
    try:
        return Entry(entry_html)
    except MalformedDataError as mde:
        LOGGER.warning(f"WARNING: {repr(mde)} from {repr(mde.__cause__)}")
    return None


def get_report(entry: Entry) -> Optional[Report]:
    """Wrapper for :class:`Report` initialization, return None on error.
    Defined here to be picklable.
    """
    try:
        return Report(entry)
    except MalformedDataError as mde:
        LOGGER.warning(f"WARNING: {repr(mde)} from {repr(mde.__cause__)}")
    return None


def extract(
    entries_html,
    n_jobs,
    progress_entries,
    progress_reports,
) -> Iterator[Tuple[Post, Annotation, List[Publication]]]:
    with Pool(n_jobs) as pool:
        entries = progress_entries(
            o for o in map(get_entry, entries_html) if o is not None
        )

        for report in progress_reports(
            o for o in pool.imap(get_report, entries) if o is not None
        ):
            entry = report.entry

            post = Post(
                date=entry.date,
                id=entry.id,
                title=entry.title,
                countries=entry.countries,
                keywords=report.keywords,
                languages=report.languages,
                outlets=entry.outlets,
            )

            annotation = Annotation(
                id=report.id,
                summary=report.summary,
                disproof=report.disproof,
                summary_links=report.summary_links,
                summary_links_resolved=report.summary_links_resolved,
                disproof_links=report.disproof_links,
                disproof_links_resolved=report.disproof_links_resolved,
            )

            publications = [
                Publication(
                    id=report.id, publication=link, archive=archived_link
                )
                for link, archived_link in report.publications
            ]
            yield (post, annotation, publications)


def write(
    out_dir: Path, gen: Iterator[Tuple[Post, Annotation, List[Publication]]]
):
    mode = "w"
    with open(out_dir / POSTS_FILENAME, mode) as posts_file, open(
        out_dir / ANNOTATIONS_FILENAME, mode
    ) as annotations_file, open(
        out_dir / PUBLICATIONS_FILENAME, mode
    ) as publications_file:
        posts_writer = DictWriter(posts_file, Post._fields)
        posts_writer.writeheader()
        annotations_writer = DictWriter(annotations_file, Annotation._fields)
        annotations_writer.writeheader()
        publications_writer = DictWriter(
            publications_file, Publication._fields
        )
        publications_writer.writeheader()

        for post, annotation, publications in gen:
            for publication in publications:
                publications_writer.writerow(stringify(publication._asdict()))
            publications_file.flush()

            annotations_writer.writerow(stringify(annotation._asdict()))
            annotations_file.flush()

            posts_writer.writerow(stringify(post._asdict()))
            posts_file.flush()


if __name__ == "__main__":
    # Ensure lists of links can be encoded correctly
    assert Report.url_encode(LIST_SEPARATOR) != LIST_SEPARATOR

    parser = argparse.ArgumentParser(
        description="Scrape entries listed in the euvsdisinfo.eu database. "
    )

    parser.add_argument(
        "dir",
        metavar="DIR",
        help="output directory",
        type=lambda p: Path(p).absolute(),
        default=Path(__file__).absolute().parent.parent / "data",
        nargs="?",
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
        default=16,
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

    iterator = islice(all_entries(), args.lines)

    total_entries = get_total_entries() if args.lines is None else args.lines
    chars_needed = str(len(str(total_entries)))
    bar_format = (
        "{l_bar}{bar}|{n_fmt:>"
        + chars_needed
        + "}/{total_fmt:>"
        + chars_needed
        + "} "
    )

    extracted = extract(
        iterator,
        n_jobs=args.jobs,
        progress_entries=lambda it: tqdm(
            it,
            desc="Entries  ",
            total=total_entries,
            colour="yellow",
            position=0,
            disable=not args.show_progress,
            bar_format=bar_format,
        ),
        progress_reports=lambda it: tqdm(
            it,
            desc="╰╴Reports",
            total=total_entries,
            colour="green",
            position=1,
            disable=not args.show_progress,
            bar_format=bar_format,
        ),
    )

    write(args.dir, extracted)
