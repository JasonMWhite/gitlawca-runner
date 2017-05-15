import os
import py
import pytest
from google.cloud import datastore
from scrapy.crawler import CrawlerProcess
from scrapy.utils import project
from scrapy.settings import Settings
from scraper import storage
from scraper.justice.spiders import acts


@pytest.fixture
def stor(tmpdir: 'py.path.local') -> storage.Storage:
    os.environ['MOCK_STORAGE'] = str(tmpdir.join('gitlawca'))
    return storage.get_storage()


def test_crawler(datastore_client: datastore.Client, stor: storage.Storage) -> None:
    test_home = os.path.join(os.path.dirname(__file__), 'fixtures/acts_home.html')
    start_urls = ['file://' + test_home]

    crawler_settings = Settings()
    from scraper.justice import settings
    crawler_settings.setmodule(settings)
    crawler = CrawlerProcess(crawler_settings)
    crawler.crawl(acts.ActsSpider, start_urls=start_urls)
    crawler.start()
    crawler.join()

    query = datastore_client.query(kind='Act')
    result = sorted(list(query.fetch()), key=lambda x: (x['code'], x['start']))
    assert len(result) == 3

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
