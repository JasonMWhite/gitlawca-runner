import logging
import os
import typing
from urllib.parse import urlparse
import scrapy
from scrapy.http import HtmlResponse
from scraper.justice.spiders import acts


LOG = logging.getLogger('gitlawca')


class SpiderRunner:

    def __init__(self, spider: scrapy.Spider) -> None:
        self.__spider = spider

    def results(self) -> typing.Iterable[scrapy.Item]:
        scrapy_requests = []  # type: typing.List[scrapy.Request]
        for result in self.__spider.start_requests():
            if isinstance(result, scrapy.Request):
                scrapy_requests.append(result)
            else:
                assert isinstance(result, scrapy.Item)
                yield result

        while scrapy_requests:
            scrapy_request = scrapy_requests.pop()
            path = urlparse(scrapy_request.url).path
            with open(path, 'r') as f:
                response = HtmlResponse(scrapy_request.url, body=f.read().encode('utf-8'), request=scrapy_request)
            result_iter = scrapy_request.callback(response)

            for result in result_iter:
                if isinstance(result, scrapy.Request):
                    scrapy_requests.append(result)
                else:
                    assert isinstance(result, scrapy.Item)
                    yield result


def test_acts_spider() -> None:
    test_home = os.path.join(os.path.dirname(__file__), 'fixtures/acts_home.html')
    spider = acts.ActsSpider(start_urls=['file://' + test_home])

    runner = SpiderRunner(spider)

    results = sorted(list(runner.results()), key=lambda item: (item['code'], item['start']))
    assert len(results) == 6
    assert all([len(x['body']) > 100 for x in results])

    results_no_body = [
        {
            'code': x['code'],
            'title': x['title'],
            'start': x['start'],
            'end': x['end'],
        } for x in results
    ]

    assert results_no_body == [
        {
            'code': 'A-1',
            'title': 'Access to Information Act',
            'start': '2015-07-09',
            'end': '2015-07-29',
        }, {
            'code': 'A-1',
            'title': 'Access to Information Act',
            'start': '2015-07-30',
            'end': '2016-04-04',
        }, {
            'code': 'A-1',
            'title': 'Access to Information Act',
            'start': '2016-04-05',
            'end': '',
        }, {
            'code': 'A-1.5',
            'title': 'Administrative Tribunals Support Service of Canada Act',
            'start': '2014-06-19',
            'end': '2014-10-31',
        }, {
            'code': 'A-1.5',
            'title': 'Administrative Tribunals Support Service of Canada Act',
            'start': '2014-11-01',
            'end': '',
        }, {
            'code': 'B-1.01',
            'title': 'Bank Act',
            'start': '2017-04-01',
            'end': '',
        }
    ]
