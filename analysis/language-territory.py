# TODO: scope is fuzzy, maybe use non-official languages to estimate impact based on number of speakers

import json
from typing import Dict, List

import requests

URL = 'https://raw.githubusercontent.com/unicode-cldr/cldr-core/master/supplemental/territoryInfo.json'
OUT = 'language-territories.json'

territory2info = json.loads(requests.get(URL).text)
territory2info = territory2info['supplemental']['territoryInfo']
language2territories: Dict[str, List[str]] = {}

for territory, terr_info in territory2info.items():
    try:
        language_info = terr_info['languagePopulation']
    except KeyError:
        continue

    for language, lang_info in language_info.items():
        try:
            official_status = lang_info['_officialStatus']
        except KeyError:
            continue
        is_official = official_status in ['official', 'official_regional', 'de_facto_official']
        if not is_official:
            continue
        if language not in language2territories:
            language2territories[language] = []
        language2territories[language].append(territory)

with open(OUT, 'w') as outfile:
    json.dump(language2territories, outfile)
