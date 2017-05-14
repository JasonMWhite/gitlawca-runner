import json
import logging
import os
import py  # pylint:disable=unused-import
import pytest
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from scraper.justice.spiders import acts


LOG = logging.getLogger('gitlawca')

@pytest.fixture
def output(tmpdir: 'py.path.local') -> 'py.path.local':
    test_home = os.path.join(os.path.dirname(__file__), 'fixtures/acts_home.html')

    start_urls = ['file://' + test_home]
    feed_url = tmpdir.join('output.json')

    settings = Settings({
        'FEED_URI': 'file://' + str(feed_url),
        'FEED_FORMAT': 'json',
        'FEED_EXPORT_FIELDS': ['code', 'title', 'start', 'end'],
        'LOG_LEVEL': 'WARNING'
    })
    crawler = CrawlerProcess(settings)
    crawler.crawl(acts.ActsSpider, start_urls=start_urls)
    crawler.start()
    crawler.join()

    return feed_url

@pytest.mark.usefixtures('datastore_client')
def test_output(output: 'py.path.local'):
    with output.open('r') as f:
        result = json.loads(f.read())
    assert sorted(result, key=lambda r: (r['code'], r['start'])) == [
        {'code': 'A-1', 'title': 'Access to Information Act', 'start': '2015-07-09', 'end': '2015-07-29'},
        {'code': 'A-1', 'title': 'Access to Information Act', 'start': '2015-07-30', 'end': '2016-04-04'},
        {'code': 'A-1', 'title': 'Access to Information Act', 'start': '2016-04-05', 'end': '2017-04-25'},
        {'code': 'A-1.5', 'title': 'Administrative Tribunals Support Service of Canada Act', 'start': '2014-06-19',
         'end': '2014-10-31'},
        {'code': 'A-1.5', 'title': 'Administrative Tribunals Support Service of Canada Act', 'start': '2014-11-01',
         'end': '2017-04-25'},
        {'code': 'B-1.01', 'title': 'Bank Act', 'start': '2017-04-01', 'end': '2017-04-25'},
    ]