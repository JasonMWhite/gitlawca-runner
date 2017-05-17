from google.cloud import datastore  # pylint: disable=import-error
import pytest
from scrapy.crawler import Crawler
from scrapy.exceptions import IgnoreRequest
from scrapy.http.request import Request
from scrapy.http.response.html import HtmlResponse
from scraper.justice.middlewares import JusticeSpiderMiddleware
from scraper.justice.spiders.acts import ActsSpider


def test_ignore(datastore_client: datastore.Client) -> None:
    act_key = datastore_client.key('Act', 'A-1')
    act = datastore.Entity(act_key)
    datastore_client.put(act)

    version_key = datastore_client.key('ActVersion', '2017-01-01', parent=act_key)
    version = datastore.Entity(version_key)
    version.update({'start': '2017-01-01', 'end': '2017-02-01'})
    datastore_client.put(version)

    meta = {
        'code': 'A-1',
        'start': '2017-01-01',
        'end': '2017-02-01',
    }
    request = Request('http://justice.gc.ca', meta=meta)
    response = HtmlResponse(url='http://justice.gc.ca', body='<html></html>'.encode('utf-8'), request=request)

    spider = ActsSpider()

    crawler = Crawler(ActsSpider, {JusticeSpiderMiddleware.DATASTORE_PROJECT_KEY: 'gitlawca'})
    middleware = JusticeSpiderMiddleware.from_crawler(crawler)

    with pytest.raises(IgnoreRequest):
        middleware.process_spider_input(response, spider)


def test_doesnt_ignore(datastore_client: datastore.Client) -> None:
    act_key = datastore_client.key('Act', 'A-1')
    act = datastore.Entity(act_key)
    datastore_client.put(act)

    version_key = datastore_client.key('ActVersion', '2017-01-01', parent=act_key)
    version = datastore.Entity(version_key)
    version.update({'start': '2017-01-01', 'end': ''})
    datastore_client.put(version)

    meta = {
        'code': 'A-1',
        'start': '2017-01-01',
        'end': '2017-02-01',
    }
    request = Request('http://justice.gc.ca', meta=meta)
    response = HtmlResponse(url='http://justice.gc.ca', body='<html></html>'.encode('utf-8'), request=request)

    spider = ActsSpider()

    crawler = Crawler(ActsSpider, {JusticeSpiderMiddleware.DATASTORE_PROJECT_KEY: 'gitlawca'})
    middleware = JusticeSpiderMiddleware.from_crawler(crawler)

    assert middleware.process_spider_input(response, spider) is None
