import argparse
import logging
from pathlib import Path

import requests
from tqdm import tqdm

from scrape.report import Report
from scrape.scraping import (
    all_rows,
    extract,
    get_len_total_entries,
    get_scraped_ids,
    write,
)
from scrape.util import DATA_DIR, LIST_SEPARATOR, check_non_negative

logger = logging.getLogger("scrape")  # use package root logger

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
    default=DATA_DIR,
    nargs="?",
)

parser.add_argument(
    "-f",
    "--fresh",
    help="overwrite existing files",
    action="store_true",
    default=False,
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
    logger.setLevel(logging.ERROR)

if args.fresh:
    logger.info("Overwriting existing files")

ignore_ids = [] if args.fresh else get_scraped_ids(args.dir)

with requests.Session() as session:
    len_all_entries = get_len_total_entries(session)
    total_entries = len_all_entries if args.lines is None else args.lines

    def progress(**kwargs):
        chars_needed = str(len(str(total_entries)))
        bar_format = (
            "{l_bar}{bar}|{n_fmt:>"
            + chars_needed
            + "}/{total_fmt:>"
            + chars_needed
            + "} "
        )
        return lambda iterator: tqdm(
            iterable=iterator,
            disable=not args.show_progress,
            bar_format=bar_format,
            **kwargs,
        )

    if args.fresh:
        rows_total = total_entries
        reports_initial = 0
        reports_total = total_entries
    else:
        rows_total = len_all_entries
        reports_initial = len(ignore_ids)
        reports_total = (
            len_all_entries
            if args.lines is None
            else len(ignore_ids) + args.lines
        )

    extracted = extract(
        session,
        all_rows(session),
        n_jobs=args.jobs,
        ignore_ids=ignore_ids,
        progress_rows=progress(
            desc="Parsing rows    ", colour="yellow", total=rows_total
        ),
        progress_reports=progress(
            desc="Scraping reports",
            colour="green",
            initial=reports_initial,
            total=reports_total,
        ),
    )

    write(
        out_dir=args.dir,
        overwrite=args.fresh,
        num_entries=args.lines,
        gen=extracted,
    )
