from google.cloud import datastore  # pylint: disable=import-error
from scrapy import crawler
from scrapy import signals
from scrapy.exceptions import IgnoreRequest
from scrapy.spiders import Spider
from scrapy.http.response.html import HtmlResponse


# pylint: disable=unused-argument

class JusticeSpiderMiddleware:

    DATASTORE_PROJECT_KEY = 'DATASTORE_PROJECT_ID'

    def __init__(self, datastore_client: datastore.Client) -> None:
        self.__datastore_client = datastore_client

    @classmethod
    def from_crawler(cls, crawler_: crawler.Crawler):
        project = crawler_.settings.get(cls.DATASTORE_PROJECT_KEY)
        client = datastore.Client(project)
        middleware = cls(client)

        crawler_.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware

    def process_spider_input(self, response: HtmlResponse, spider: Spider):
        if 'code' in response.meta and 'start' in response.meta:
            version_key = self.__datastore_client.key('Act', response.meta['code'],
                                                      'ActVersion', response.meta['start'])
            version = self.__datastore_client.get(version_key)
            if version and version['end'] == response.meta['end']:
                raise IgnoreRequest()
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, _):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for req in start_requests:
            yield req

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
