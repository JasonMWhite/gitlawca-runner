from google.cloud import datastore  # pylint:disable=import-error
import pytest
from scraper import storage
from scraper.justice.items import ActItem
from scraper.justice.pipelines import DataStoreExporter


def test_datastore_is_clean(datastore_client):
    key = datastore_client.key('Act')

    query = datastore_client.query(kind='Act')
    acts = list(query.fetch())
    assert acts == []

    new_act = datastore.Entity(key)
    new_act.update({
        'id': 1,
        'value': 'foo'
    })
    datastore_client.put(new_act)

    query = datastore_client.query(kind='Act')
    acts = list(query.fetch())
    assert dict(acts[0].items()) == {'id': 1, 'value': 'foo'}
    assert len(acts) == 1


@pytest.fixture
def exporter(datastore_client: datastore.Client, stor) -> DataStoreExporter:
    return DataStoreExporter(datastore_client, stor)


def test_datastore_is_still_clean(datastore_client):
    key = datastore_client.key('Act')

    query = datastore_client.query(kind='Act')
    acts = list(query.fetch())
    assert acts == []

    new_act = datastore.Entity(key)
    new_act.update({
        'id': 2,
        'value': 'bar'
    })
    datastore_client.put(new_act)

    query = datastore_client.query(kind='Act')
    acts = list(query.fetch())
    assert dict(acts[0].items()) == {'id': 2, 'value': 'bar'}
    assert len(acts) == 1


def test_store_item_in_datastore(datastore_client: datastore.Client,
                                 exporter: DataStoreExporter,
                                 stor: storage.Storage) -> None:
    item = ActItem({
        'code': 'A-1',
        'title': 'Access to Information',
        'body': 'Text of Act',
        'start': '2016-01-01',
        'end': '2016-02-01',
    })
    output = exporter.export_item(item)
    assert output == item

    query = datastore_client.query(kind='Act')
    query.add_filter('code', '=', 'A-1')
    items = list(query.fetch())

    expected = {
        'code': 'A-1',
        'title': 'Access to Information',
        'raw_blob': 'acts/raw/A-1/2016-01-01',
        'start': '2016-01-01',
        'end': '2016-02-01',
    }
    assert [dict(x) for x in items] == [expected]

    assert stor.get_blob(expected['raw_blob']).download_to_string() == 'Text of Act'


def test_store_multiple_versions(datastore_client: datastore.Client,
                                 exporter: DataStoreExporter,
                                 stor: storage.Storage) -> None:
    item0 = ActItem({
        'code': 'A-1',
        'title': 'Access to Information',
        'body': 'Text of Act',
        'start': '2016-01-01',
        'end': '2016-02-01',
    })
    exporter.export_item(item0)

    item1 = ActItem({
        'code': 'A-1',
        'title': 'Access to Information',
        'body': 'Revised Text of Act',
        'start': '2016-02-02',
        'end': '',
    })
    exporter.export_item(item1)

    query = datastore_client.query(kind='Act')
    query.add_filter('code', '=', 'A-1')
    items = sorted(list(query.fetch()), key=lambda item: (item['code'], item['start']))

    assert items[0]['code'] == 'A-1'
    assert items[1]['code'] == 'A-1'

    assert items[0]['start'] == '2016-01-01'
    assert items[0]['end'] == '2016-02-01'

    assert items[1]['start'] == '2016-02-02'
    assert items[1]['end'] == ''

    assert stor.get_blob(items[0]['raw_blob']).download_to_string() == item0['body']
    assert stor.get_blob(items[1]['raw_blob']).download_to_string() == item1['body']


def test_store_item_saves_missing_body(datastore_client: datastore.Client,
                                       exporter: DataStoreExporter,
                                       stor: storage.Storage) -> None:
    item = ActItem({
        'code': 'A-1',
        'title': 'Access to Information',
        'body': 'Text of Act',
        'start': '2016-01-01',
        'end': '2016-02-01',
    })

    key = datastore_client.key('Act')
    act = datastore.Entity(key=key)
    act.update({
        'code': item['code'],
        'title': item['title'],
        'raw_blob': '',
        'start': item['start'],
        'end': item['end'],
    })
    datastore_client.put(act)
    assert not stor.get_blob('acts/raw/A-1').exists()

    exporter.export_item(item)

    query = datastore_client.query(kind='Act')
    query.add_filter('code', '=', 'A-1')
    query.add_filter('start', '=', '2016-01-01')
    output = list(query.fetch())

    assert len(output) == 1
    assert output[0]['raw_blob'] == 'acts/raw/A-1/2016-01-01'
    assert stor.get_blob(output[0]['raw_blob']).download_to_string() == 'Text of Act'


def test_exporter_doesnt_overwrite(datastore_client: datastore.Client,
                                   exporter: DataStoreExporter,
                                   stor: storage.Storage) -> None:
    item1 = ActItem({
        'code': 'A-1',
        'title': 'Foo',
        'body': 'Bar',
        'start': '2016-01-01',
        'end': '2016-02-01',
    })
    exporter.export_item(item1)

    query = datastore_client.query(kind='Act')
    query.add_filter('code', '=', 'A-1')
    output = list(query.fetch())
    assert len(output) == 1
    assert stor.get_blob(output[0]['raw_blob']).download_to_string() == 'Bar'

    item2 = ActItem({
        'code': 'A-1',
        'title': 'Access to Information',
        'body': 'Text of Act',
        'start': '2016-01-01',
        'end': '2016-03-01',
    })
    exporter.export_item(item2)
    output = list(query.fetch())
    assert len(output) == 1
    assert output[0]['title'] == 'Foo'
    assert stor.get_blob(output[0]['raw_blob']).download_to_string() == 'Bar'
