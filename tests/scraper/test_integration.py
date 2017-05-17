import os
from google.cloud import datastore
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
    result = sorted(list(query.fetch()), key=lambda x: (x['code'], x['start']))
    assert len(result) == 6

    assert dict(result[0]) == {
        'code': 'A-1',
        'title': 'Access to Information Act',
        'start': '2015-07-09',
        'end': '2015-07-29',
        'raw_blob': 'acts/raw/A-1'
    }
    blob_text = stor.get_blob('acts/raw/A-1').download_to_string()
    assert len(blob_text) > 100
    assert '<div class="info">Version of document from 2015-07-09 to 2015-07-29:</div>' in blob_text

    assert result[2]['code'] == 'B-1.01'
