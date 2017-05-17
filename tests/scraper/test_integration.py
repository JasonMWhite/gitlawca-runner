import os
from google.cloud import datastore  # pylint:disable=import-error
import pytest
from scrapy import crawler
from scrapy.settings import Settings
from scraper import storage
from scraper.justice.spiders import acts


@pytest.fixture
def crawler_settings() -> Settings:
    from scraper.justice import settings
    settings_ = Settings()
    settings_.setmodule(settings)
    settings_.set('ROBOTSTXT_OBEY', False)
    return settings_


def test_crawler(datastore_client: datastore.Client, stor: storage.Storage, crawler_settings: Settings) -> None:
    test_home = os.path.join(os.path.dirname(__file__), 'justice/fixtures/acts_home.html')
    start_urls = ['file://' + test_home]

    process = crawler.CrawlerProcess(crawler_settings)
    process.crawl(acts.ActsSpider, start_urls=start_urls)
    process.start()
    process.join()

    query = datastore_client.query(kind='Act')
    results = sorted(list(query.fetch()), key=lambda x: (x['code'], x['start']))
    assert len(results) == 6

    assert dict(results[0]) == {
        'code': 'A-1',
        'title': 'Access to Information Act',
        'start': '2015-07-09',
        'end': '2015-07-29',
        'raw_blob': 'acts/raw/A-1/2015-07-09'
    }
    assert results[5]['code'] == 'B-1.01'

    blob_texts = [stor.get_blob(result['raw_blob']).download_to_string() for result in results]
    assert all([len(blob_text) > 100 for blob_text in blob_texts])
    assert '<div class="info">Version of document from 2015-07-09 to 2015-07-29:</div>' in blob_texts[0]
    assert '<div class="info">Version of document from 2017-04-01 to 2017-04-25:</div>' in blob_texts[5]
