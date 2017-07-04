import datetime
import os
from google.cloud import datastore
from google.cloud import pubsub
import pytest
from scraper import acts_scraper
from scraper import acts_storage
from scraper import spider
from scraper import storage


@pytest.fixture
def acts_spider(pubsub_client: pubsub.Client,
                datastore_client: datastore.Client,
                stor: storage.Storage) -> spider.ActsSpider:
    scraper = acts_scraper.ActsScraper()
    acts_stor = acts_storage.ActsStorage(datastore_client, stor)
    return spider.ActsSpider(pubsub_client, scraper, acts_stor)


def test_integration(pubsub_client: pubsub.Client,
                     datastore_client: datastore.Client,
                     stor: storage.Storage,
                     acts_spider: spider.ActsSpider):
    topic = pubsub_client.topic('acts_requests')
    fixture_file = os.path.join(os.path.dirname(__file__), 'fixtures', 'acts_home.html')
    attrs = {'type': 'main_page', 'timestamp': datetime.datetime.now().isoformat()}
    topic.publish(('file://' + fixture_file).encode('utf-8'), **attrs)

    done = False
    while not done:
        done = not acts_spider.listen(wait=False)

    query = datastore_client.query(kind='Act')
    acts = sorted(list(query.fetch()), key=lambda act: act['code'])
    assert len(acts) == 3
    assert [act['code'] for act in acts] == ['A-1', 'A-1.5', 'B-1.01']

    query = datastore_client.query(kind='ActVersion')
    act_versions = sorted(list(query.fetch()), key=lambda ver: ver['raw_blob'])
    assert len(act_versions) == 6
    assert [act_version['raw_blob'] for act_version in act_versions] == [
        'acts/raw/A-1.5/2014-06-19',
        'acts/raw/A-1.5/2014-11-01',
        'acts/raw/A-1/2015-07-09',
        'acts/raw/A-1/2015-07-30',
        'acts/raw/A-1/2016-04-05',
        'acts/raw/B-1.01/2017-04-01',
    ]

    acts_texts = [stor.get_blob(act_version['raw_blob']).download_to_string() for act_version in act_versions]
    assert all([len(act_text) > 1000 for act_text in acts_texts])
