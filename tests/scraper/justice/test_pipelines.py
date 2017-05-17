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

    act_key = datastore_client.key('Act', item['code'])
    act = datastore_client.get(act_key)
    assert dict(act) == {'code': 'A-1', 'title': 'Access to Information'}

    version_key = datastore_client.key('ActVersion', item['start'], parent=act_key)
    version = datastore_client.get(version_key)
    assert dict(version) == {'start': '2016-01-01', 'end': '2016-02-01', 'raw_blob': 'acts/raw/A-1/2016-01-01'}
    assert stor.get_blob(version['raw_blob']).download_to_string() == 'Text of Act'


def test_store_version_in_datastore(datastore_client: datastore.Client,
                                    exporter: DataStoreExporter) -> None:
    item = ActItem({
        'code': 'A-1',
        'title': 'Access to Information',
        'body': 'Text of Act',
        'start': '2016-01-01',
        'end': '2016-02-01',
    })

    act_key = datastore_client.key('Act', 'A-1')
    act = datastore.Entity(act_key)
    act.update({'title': 'Access to Information'})
    datastore_client.put(act)

    exporter.export_item(item)

    version_key = datastore_client.key('ActVersion', item['start'], parent=act_key)
    version = datastore_client.get(version_key)
    assert version
    assert version['start'] == '2016-01-01'


def test_store_multiple_versions(datastore_client: datastore.Client,
                                 exporter: DataStoreExporter,
                                 stor: storage.Storage) -> None:
    items = [
        ActItem({
            'code': 'A-1',
            'title': 'Access to Information',
            'body': 'Text of Act',
            'start': '2016-01-01',
            'end': '2016-02-01',
        }),
        ActItem({
            'code': 'A-1',
            'title': 'Access to Information',
            'body': 'Revised Text of Act',
            'start': '2016-02-02',
            'end': '2016-03-01',
        })
    ]
    for item in items:
        exporter.export_item(item)

    version_keys = [datastore_client.key('Act', x['code'], 'ActVersion', x['start']) for x in items]
    versions = [datastore_client.get(key) for key in version_keys]
    version_bodies = [stor.get_blob(x['raw_blob']).download_to_string() for x in versions]

    assert version_bodies == ['Text of Act', 'Revised Text of Act']
    assert versions[0].key.parent == versions[1].key.parent


def test_dont_overwrite_item(datastore_client: datastore.Client,
                             exporter: DataStoreExporter,
                             stor: storage.Storage) -> None:
    item1 = ActItem({
        'code': 'A-1',
        'title': 'Access to Information',
        'body': 'Text of Act',
        'start': '2016-01-01',
        'end': '2016-02-01',
    })

    item2 = ActItem({
        'code': 'A-1',
        'title': 'New Access to Information',
        'body': 'Revised Text of Act',
        'start': '2016-01-01',
        'end': '2016-03-01',
    })

    exporter.export_item(item1)
    exporter.export_item(item2)

    act_key = datastore_client.key('Act', item1['code'])
    version_key = datastore_client.key('ActVersion', item1['start'], parent=act_key)

    act = datastore_client.get(act_key)
    assert act['title'] == item1['title']
    assert act['title'] != item2['title']

    version = datastore_client.get(version_key)
    assert version['end'] == item1['end']
    assert version['end'] != item2['end']

    version_text = stor.get_blob(version['raw_blob']).download_to_string()
    assert version_text == item1['body']
    assert version_text != item2['body']


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

    act_key = datastore_client.key('Act', item['code'])
    act = datastore.Entity(act_key)
    act.update({
        'code': item['code'],
        'title': item['title'],
    })
    datastore_client.put(act)

    version_key = datastore_client.key('ActVersion', item['start'], parent=act_key)
    version = datastore.Entity(version_key)
    version.update({
        'start': item['start'],
        'end': item['end'],
    })
    datastore_client.put(version)

    exporter.export_item(item)

    version = datastore_client.get(version_key)
    assert stor.get_blob(version['raw_blob']).download_to_string() == 'Text of Act'
