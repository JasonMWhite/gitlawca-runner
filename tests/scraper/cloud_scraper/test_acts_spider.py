import datetime
import typing  # pylint: disable=unused-import
from google.cloud import pubsub
from google.cloud.pubsub import message  # pylint: disable=unused-import
from scraper.cloud_scraper import acts_scraper
from scraper.cloud_scraper import acts_spider


def scraper_test_function(input_breadcrumb: acts_scraper.Breadcrumb) -> acts_scraper.ScraperResult:
    output_attrs0 = dict(input_breadcrumb.attrs.items())
    output_attrs0['foo'] = 'bar'
    output_attrs1 = dict(input_breadcrumb.attrs.items())
    output_attrs1['baz'] = '1'

    output_breadcrumbs = [
        acts_scraper.Breadcrumb(url=input_breadcrumb.url, attrs=output_attrs0),
        acts_scraper.Breadcrumb(url=input_breadcrumb.url, attrs=output_attrs1),
    ]

    output_items = [
        acts_scraper.ActItem(
            code=input_breadcrumb.attrs['code'],
            title=input_breadcrumb.attrs['title'],
            start=input_breadcrumb.attrs['start'],
            end=input_breadcrumb.attrs['end'],
            body=input_breadcrumb.attrs['body'],
        )
    ]

    return output_breadcrumbs, output_items


def test_listen(pubsub_client: pubsub.Client) -> None:
    spider = acts_spider.ActsSpider(pubsub_client)
    spider.TYPE_DECODER['foo'] = scraper_test_function

    input_attrs = {
        'code': 'A-1',
        'title': 'Act Title',
        'start': datetime.date(2016, 1, 1).strftime('%Y-%m-%D'),
        'end': datetime.date(2017, 1, 1).strftime('%Y-%m-%D'),
        'body': 'Act Body',
        'type': 'foo',
    }

    topic = pubsub_client.topic('acts_requests')
    topic.publish('http://foo.bar'.encode('utf-8'), **input_attrs)

    spider.listen()

    sub = topic.subscription('acts_scraper')

    results = []  # type: typing.List[message.Message]
    while True:
        new_results = sub.pull(return_immediately=True)
        if new_results:
            results.extend([msg for _, msg in new_results])
        else:
            break

    assert len(results) == 2
    assert all([msg.data.decode('utf-8') == 'http://foo.bar' for msg in results])
    assert results[0].attributes['foo'] == 'bar'
    assert results[1].attributes['baz'] == '1'
