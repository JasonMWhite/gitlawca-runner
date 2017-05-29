import datetime
import typing  # pylint: disable=unused-import

from google.cloud import datastore
from google.cloud import pubsub
from google.cloud.pubsub import message  # pylint: disable=unused-import

from scraper import acts_scraper
from scraper import acts_storage
from scraper import spider
from scraper import storage


class MockScraper(acts_scraper.Scraper):

    def scrape(self, input_breadcrumb: acts_scraper.Breadcrumb) -> acts_scraper.ScraperResult:
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


def test_listen_publishes_to_pubsub(pubsub_client: pubsub.Client,
                                    datastore_client: datastore.Client,
                                    stor: storage.Storage) -> None:
    acts_stor = acts_storage.ActsStorage(datastore_client, stor)
    spider_ = spider.ActsSpider(pubsub_client, MockScraper(), acts_stor)

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

    spider_.listen()

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


def test_listen_stores_results(pubsub_client: pubsub.Client,
                               datastore_client: datastore.Client,
                               stor: storage.Storage) -> None:
    acts_stor = acts_storage.ActsStorage(datastore_client, stor)
    spider_ = spider.ActsSpider(pubsub_client, MockScraper(), acts_stor)

    input_attrs = {
        'code': 'A-1',
        'title': 'Act Title',
        'start': datetime.date(2016, 1, 1).strftime('%Y-%m-%d'),
        'end': datetime.date(2017, 1, 1).strftime('%Y-%m-%d'),
        'body': 'Act Body',
        'type': 'foo',
    }

    topic = pubsub_client.topic('acts_requests')
    topic.publish('http://foo.bar'.encode('utf-8'), **input_attrs)

    spider_.listen()

    act_key = datastore_client.key('Act', 'A-1')
    act = datastore_client.get(act_key)
    assert act['code'] == 'A-1'
    assert act['title'] == 'Act Title'

    act_version_key = datastore_client.key('ActVersion', '2016-01-01', parent=act_key)
    act_version = datastore_client.get(act_version_key)
    assert act_version['start'] == '2016-01-01'
    assert act_version['end'] == '2017-01-01'

    act_text = stor.get_blob(act_version['raw_blob']).download_to_string()
    assert act_text == 'Act Body'
