import json
import os
from typing import List, Dict

import country_converter as coco
import langcodes

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

LANGUAGE2TERRITORIES: Dict[str, List[str]]
with open(os.path.join(__location__, 'language-territories.json')) as l2t:
    LANGUAGE2TERRITORIES = json.load(l2t)


def language_to_iso2(lang: str) -> str:
    return langcodes.find(lang).language


def territory_to_iso3(terr: str) -> str:
    if terr == 'UK':
        return 'GBR'
    else:
        return coco.convert(terr, to='ISO3')


def territories_from_language(lang: str) -> List[str]:
    lang_iso = langcodes.find(lang).language
    iso2 = LANGUAGE2TERRITORIES[lang_iso]
    iso3 = coco.convert(iso2, src='ISO2', to='ISO3')
    return iso3
