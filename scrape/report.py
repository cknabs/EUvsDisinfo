import logging
import urllib.error
import urllib.parse
from datetime import date, datetime
from typing import List, Optional, Tuple

import requests
import urllib3
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class Row:
    date: date
    title: str = ""
    id: str = ""
    outlets: List[str] = []
    countries: List[str] = []

    def __init__(self, row):
        # Get basic data from database row
        try:
            date_str = self.get_data_column(row, "Date").contents[0].strip()
            self.date = datetime.strptime(date_str, "%d.%m.%Y").date()
            title_link = self.get_data_column(row, "Title").find("a")
            self.title = title_link.contents[0].strip()
            self.id = title_link["href"]

            self.outlets = self.get_strings_for_col(row, "Outlets")
            self.countries = self.get_strings_for_col(
                row, "Country", separator=","
            )
        except Exception as exception:
            raise MalformedDataError(
                "Malformed row error", self.id
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
    row: Row
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

    def __init__(self, id_, report, req=requests):
        self.id = id_

        # Get keywords, summary, disproof from report page
        try:
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
                    self.url_encode(self.resolve_link(req, link))
                    for link in links
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
                    self.url_encode(self.resolve_link(req, link))
                    for link in links
                ]
            except AttributeError:
                self.warn_missing("disproof")
        except Exception as exception:
            self.warn_missing(repr(exception))

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
            self.warn_missing(repr(exception))

    def warn_missing(self, name: str):
        self.warn(f"Missing data '{name}' for {self.id}")

    def warn(self, msg: str):
        logger.warning(msg)

    @staticmethod
    def resolve_link(session, url: str) -> str:
        try:
            response = session.head(url, allow_redirects=True)
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


def get_row(row_html) -> Optional[Row]:
    """Wrapper for :class:`Row` initialization, return None on error.
    Defined here to be picklable.
    """
    try:
        return Row(row_html)
    except MalformedDataError as mde:
        logger.warning(f"WARNING: {repr(mde)} from {repr(mde.__cause__)}")
    return None


def get_report(session, row: Row) -> Optional[Tuple[Row, Report]]:
    """Wrapper for :class:`Report` initialization, return None on error.
    Defined here to be picklable.
    """
    try:
        report = BeautifulSoup(session.get(row.id).text, "html.parser")
        return row, Report(row.id, report, req=session)
    except MalformedDataError as mde:
        logger.warning(f"WARNING: {repr(mde)} from {repr(mde.__cause__)}")
    return None
