![CI](https://github.com/cknabs/EUvsDisinfo/workflows/CI/badge.svg)
[![Requirements Status](https://requires.io/github/cknabs/EUvsDisinfo/requirements.svg?branch=main)](https://requires.io/github/cknabs/EUvsDisinfo/requirements/?branch=main)
[![frictionless](https://github.com/cknabs/EUvsDisinfo/actions/workflows/frictionless.yml/badge.svg)](https://github.com/cknabs/EUvsDisinfo/actions/workflows/frictionless.yml)

# EUvsDisinfo

This project aims to scrape, visualize and analyse data from [euvsdisinfo.eu](https://euvsdisinfo.eu/), in particular the [EUvsDisinfo database](https://euvsdisinfo.eu/disinformation-cases/) compiled by the EU East StratCom Task Force.
Check out a live deployment of this repo on [eu-vs-disinfo.herokuapp.com](https://eu-vs-disinfo.herokuapp.com/)!

## Running locally
To run the dashboard locally, simply clone the repository, install the  required dependencies, and run `index.py`. 

```bash
git clone https://github.com/cknabs/EUvsDisinfo.git
cd EUvsDisinfo
poetry install # or create a virtual environment and use `pip install -r requirements.txt`
poetry run python index.py
```

## Dependencies
This project relies heavily on the [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) library (v4) for scraping, and on the [plotly](https://plotly.com/python/) library for all the visualizations. 
Dependencies are managed using [Poetry](https://python-poetry.org/); the `requirements.txt` file is generated from the dependencies specified in `pyproject.toml`, and is used for the Heroku deployment of the dashboard.
