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
def stor() -> storage.Storage:
    return storage.get_storage()


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
    })
    output = exporter.export_item(item)
    assert output == item

    query = datastore_client.query(kind='Act')
    query.add_filter('code', '=', 'A-1')
    items = list(query.fetch())

    expected = [{
        'code': 'A-1',
        'title': 'Access to Information',
        'raw_blob': 'acts/raw/A-1',
    }]
    assert [dict(x) for x in items] == expected

    assert stor.get_blob('acts/raw/A-1').download_to_string() == 'Text of Act'


def test_store_item_saves_missing_body(datastore_client: datastore.Client,
                                       exporter: DataStoreExporter,
                                       stor: storage.Storage) -> None:
    item = ActItem({
        'code': 'A-1',
        'title': 'Access to Information',
        'body': 'Text of Act',
    })

    key = datastore_client.key('Act')
    act = datastore.Entity(key=key)
    act.update({
        'code': item['code'],
        'title': item['title'],
        'raw_blob': '',
    })
    datastore_client.put(act)
    assert not stor.get_blob('acts/raw/A-1').exists()

    exporter.export_item(item)

    query = datastore_client.query(kind='Act')
    query.add_filter('code', '=', 'A-1')
    output = list(query.fetch())

    assert len(output) == 1
    assert output[0]['raw_blob'] == 'acts/raw/A-1'
    assert stor.get_blob('acts/raw/A-1').download_to_string() == 'Text of Act'


def test_exporter_doesnt_overwrite(datastore_client: datastore.Client,
                                   exporter: DataStoreExporter,
                                   stor: storage.Storage) -> None:
    item1 = ActItem({
        'code': 'A-1',
        'title': 'Foo',
        'body': 'Bar',
    })
    exporter.export_item(item1)

    query = datastore_client.query(kind='Act')
    query.add_filter('code', '=', 'A-1')
    output = list(query.fetch())
    assert len(output) == 1
    assert stor.get_blob('acts/raw/A-1').download_to_string() == 'Bar'

    item2 = ActItem({
        'code': 'A-1',
        'title': 'Access to Information',
        'body': 'Text of Act',
    })
    exporter.export_item(item2)
    output = list(query.fetch())
    assert len(output) == 1
    assert output[0]['title'] == 'Foo'
    assert stor.get_blob('acts/raw/A-1').download_to_string() == 'Bar'
