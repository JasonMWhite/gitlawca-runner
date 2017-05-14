from google.cloud import datastore
from scrapy.exceptions import IgnoreRequest
from scrapy.http.response.html import HtmlResponse
from scraper.justice.spiders.acts import ActsSpider


class JusticeSpiderMiddleware:

    def __init__(self, datastore_client: datastore.Client) -> None:
        self.__datastore_client = datastore_client

    DATASTORE_PROJECT_KEY = 'DATASTORE_PROJECT_ID'

    @classmethod
    def from_crawler(cls, crawler):
        project = crawler.settings.get(cls.DATASTORE_PROJECT_KEY)
        client = datastore.Client(project)
        return cls(client)

    def process_spider_input(self, response: HtmlResponse, spider: ActsSpider) -> None:
        if 'code' in response.meta and 'start' in response.meta:
            key = self.__datastore_client.key('Act', '{}/{}'.format(response.meta['code'], response.meta['start']))
            item = self.__datastore_client.get(key)
            if item and item['end'] == response.meta['end']:
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

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for req in start_requests:
            yield req
