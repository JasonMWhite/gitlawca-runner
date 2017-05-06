import json
import os
import py  # pylint:disable=unused-import
import pytest
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from justice.justice.spiders import acts


@pytest.fixture
def output(tmpdir: 'py.path.local') -> 'py.path.local':
    test_home = os.path.join(os.path.dirname(__file__), 'fixtures/acts_home.html')

    start_urls = ['file://' + test_home]
    feed_url = tmpdir.join('output.json')

    settings = Settings({
        'FEED_URI': 'file:/' + str(feed_url),
        'FEED_FORMAT': 'json',
        'FEED_EXPORT_FIELDS': ['code', 'title'],
        'LOG_LEVEL': 'WARNING'
    })
    crawler = CrawlerProcess(settings)
    crawler.crawl(acts.ActsSpider, start_urls=start_urls)
    crawler.start()

    return feed_url


def test_output(output: 'py.path.local'):
    with output.open('r') as f:
        result = json.loads(f.read())

    assert sorted(result, key=lambda r: r['code']) == [
        {'code': 'A-1', 'title': 'Access to Information Act'},
        {'code': 'A-1.5', 'title': 'Administrative Tribunals Support Service of Canada Act'},
        {'code': 'B-1.01', 'title': 'Bank Act'},
    ]
