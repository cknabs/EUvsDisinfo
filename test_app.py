import frictionless

from scrape.util import DATA_DIR, SCHEMA_FILENAME


def test_data_format():
    report = frictionless.validate_package(
        str(DATA_DIR / SCHEMA_FILENAME), basepath=str(DATA_DIR)
    )
    assert report["valid"]
