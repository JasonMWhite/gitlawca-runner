import os
import typing
from google.cloud import datastore  # pylint:disable=import-error
import pytest
from scrapy import crawler
from scrapy.settings import Settings
from scraper import storage
from scraper.justice.spiders import acts


def prepopulate_one_version(datastore_client: datastore.Client,
                            stor: storage.Storage):
    act_key = datastore_client.key('Act', 'A-1')
    act = datastore.Entity(key=act_key)
    act.update({'code': 'A-1', 'title': 'Access to Information Act'})
    datastore_client.put(act)

    version_key = datastore_client.key('ActVersion', '2015-07-09', parent=act_key)
    version = datastore.Entity(key=version_key)
    version.update({'start': '2015-07-09', 'end': '2015-07-29', 'raw_blob': 'acts/raw/A-1/2015-07-09'})
    datastore_client.put(version)

    stor.get_blob(version['raw_blob']).upload_from_string('Prepopulated')


def crawler_settings() -> Settings:
    from scraper.justice import settings
    settings_ = Settings()
    settings_.setmodule(settings)
    settings_.set('ROBOTSTXT_OBEY', False)
    settings_.set('DOWNLOAD_DELAY', 0)
    return settings_


def crawl() -> None:
    test_home = os.path.join(os.path.dirname(__file__), 'justice/fixtures/acts_home.html')
    start_urls = ['file://' + test_home]

    process = crawler.CrawlerProcess(crawler_settings())
    process.crawl(acts.ActsSpider, start_urls=start_urls)
    process.start()
    process.join()


ACTS = []  # type: typing.List[datastore.Entity]
VERSIONS = []  # type: typing.List[datastore.Entity]
STORAGE = None  # type: typing.Optional[storage.Storage]


def _crawl_and_materialize(datastore_client: datastore.Client, stor: storage.Storage) -> None:
    global ACTS  # pylint: disable=global-statement
    global VERSIONS  # pylint: disable=global-statement
    global STORAGE  # pylint: disable=global-statement

    prepopulate_one_version(datastore_client, stor)
    crawl()
    ACTS = sorted(list(datastore_client.query(kind='Act').fetch()), key=lambda x: x['code'])
    VERSIONS = sorted(list(datastore_client.query(kind='ActVersion').fetch()),
                      key=lambda x: (x.key.parent.name, x['start']))
    STORAGE = stor


@pytest.fixture
def materialized_acts(datastore_client: datastore.Client,
                      stor: storage.Storage) -> typing.List[datastore.Entity]:
    if not ACTS:
        _crawl_and_materialize(datastore_client, stor)
    return ACTS


@pytest.fixture
def materialized_versions(datastore_client: datastore.Client,
                          stor: storage.Storage) -> typing.List[datastore.Entity]:
    if not VERSIONS:
        _crawl_and_materialize(datastore_client, stor)
    return VERSIONS


def test_acts(materialized_acts: typing.List[datastore.Entity]) -> None:
    acts_dict = [dict(x) for x in materialized_acts]
    assert acts_dict == [
        {'code': 'A-1', 'title': 'Access to Information Act'},
        {'code': 'A-1.5', 'title': 'Administrative Tribunals Support Service of Canada Act'},
        {'code': 'B-1.01', 'title': 'Bank Act'},
    ]


def test_versions(materialized_versions: typing.List[datastore.Entity]) -> None:
    versions_dict = [dict(x) for x in materialized_versions]

    assert versions_dict == [
        {'start': '2015-07-09', 'end': '2015-07-29', 'raw_blob': 'acts/raw/A-1/2015-07-09'},
        {'start': '2015-07-30', 'end': '2016-04-04', 'raw_blob': 'acts/raw/A-1/2015-07-30'},
        {'start': '2016-04-05', 'end': '', 'raw_blob': 'acts/raw/A-1/2016-04-05'},
        {'start': '2014-06-19', 'end': '2014-10-31', 'raw_blob': 'acts/raw/A-1.5/2014-06-19'},
        {'start': '2014-11-01', 'end': '', 'raw_blob': 'acts/raw/A-1.5/2014-11-01'},
        {'start': '2017-04-01', 'end': '', 'raw_blob': 'acts/raw/B-1.01/2017-04-01'},
    ]

    assert STORAGE
    blob_texts = [STORAGE.get_blob(version['raw_blob']).download_to_string() for version in materialized_versions]

    assert blob_texts[0] == 'Prepopulated'
    assert all([len(blob_text) > 100 for blob_text in blob_texts[1:]])
    assert '<div class="info">Version of document from 2015-07-30 to 2016-04-04:</div>' in blob_texts[1]
    assert '<div class="info">Version of document from 2016-04-05 to ' in blob_texts[2]
    assert '<div class="info">Version of document from 2014-06-19 to 2014-10-31:</div>' in blob_texts[3]
    assert '<div class="info">Version of document from 2014-11-01 to ' in blob_texts[4]
    assert '<div class="info">Version of document from 2017-04-01 to ' in blob_texts[5]
