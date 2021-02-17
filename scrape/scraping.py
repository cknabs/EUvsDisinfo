import functools
import logging
from csv import DictWriter
from itertools import islice
from multiprocessing import Pool
from pathlib import Path
from typing import Collection, Generator, Iterator, List, Optional, Tuple

import pandas as pd
from bs4 import BeautifulSoup

from scrape.report import Report, Row, get_report, get_row
from scrape.util import (
    ANNOTATIONS_FILENAME,
    POSTS_FILENAME,
    PUBLICATIONS_FILENAME,
    URL,
    Annotation,
    Post,
    Publication,
    stringify,
)

logger = logging.getLogger(__name__)


def all_rows(session) -> Generator:
    """Generator, yields all rows"""
    offset = 0
    while True:
        html = session.get(URL, params={"offset": offset, "per_page": 100})
        soup = BeautifulSoup(html.text, "html.parser")
        all_posts = soup.find_all(attrs={"class": "disinfo-db-post"})
        if len(all_posts) == 0:
            return
        for post in all_posts:
            yield post
            offset += 1


def get_len_total_entries(session) -> int:
    html = session.get(URL)
    soup = BeautifulSoup(html.text, "html.parser")
    return int(
        soup.find(attrs={"class": "disinfo-db-results"})
        .find("span")
        .contents[0]
    )


def get_scraped_ids(out_dir: Path) -> Collection[str]:
    read = pd.read_csv(out_dir / POSTS_FILENAME)
    return set(read["id"])  # for efficient membership test


def translate(
    row: Row, report: Report
) -> Tuple[Post, Annotation, List[Publication]]:
    post = Post(
        date=row.date,
        id=row.id,
        title=row.title,
        countries=row.countries,
        keywords=report.keywords,
        languages=report.languages,
        outlets=row.outlets,
    )

    annotation = Annotation(
        id=row.id,
        summary=report.summary,
        disproof=report.disproof,
        summary_links=report.summary_links,
        summary_links_resolved=report.summary_links_resolved,
        disproof_links=report.disproof_links,
        disproof_links_resolved=report.disproof_links_resolved,
    )

    publications = [
        Publication(id=row.id, publication=link, archive=archived_link)
        for link, archived_link in report.publications
    ]
    return post, annotation, publications


def extract(
    session,
    rows_html,
    n_jobs: int,
    ignore_ids: Collection[str],
    progress_rows,
    progress_reports,
) -> Iterator[Tuple[Post, Annotation, List[Publication]]]:
    with Pool(n_jobs) as pool:
        rows = progress_rows(
            o
            for o in map(get_row, rows_html)
            if o is not None and o.id not in ignore_ids
        )

        for row, report in progress_reports(
            o
            for o in pool.imap(functools.partial(get_report, session), rows)
            if o is not None
        ):
            yield translate(row, report)


def write(
    out_dir: Path,
    overwrite: bool,
    num_entries: Optional[int],
    gen: Iterator[Tuple[Post, Annotation, List[Publication]]],
):
    mode = "w" if overwrite else "a"
    encoding = "utf-8"
    with open(
        out_dir / POSTS_FILENAME, mode, encoding=encoding
    ) as posts_file, open(
        out_dir / ANNOTATIONS_FILENAME, mode, encoding=encoding
    ) as annotations_file, open(
        out_dir / PUBLICATIONS_FILENAME, mode, encoding=encoding
    ) as publications_file:
        posts_writer = DictWriter(posts_file, Post._fields)
        annotations_writer = DictWriter(annotations_file, Annotation._fields)
        publications_writer = DictWriter(
            publications_file, Publication._fields
        )
        if overwrite:
            posts_writer.writeheader()
            annotations_writer.writeheader()
            publications_writer.writeheader()

        for post, annotation, publications in islice(gen, num_entries):
            for publication in publications:
                publications_writer.writerow(stringify(publication._asdict()))
            publications_file.flush()

            annotations_writer.writerow(stringify(annotation._asdict()))
            annotations_file.flush()

            posts_writer.writerow(stringify(post._asdict()))
            posts_file.flush()


print("scraping.py", __name__)
