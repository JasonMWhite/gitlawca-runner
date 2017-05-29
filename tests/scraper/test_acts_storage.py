from google.cloud import datastore

from scraper import acts_scraper
from scraper import acts_storage
from scraper import storage


def test_datastore_is_clean(datastore_client: datastore.Client) -> None:
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


def test_store_item(datastore_client: datastore.Client, stor: storage.Storage) -> None:
    item = acts_scraper.ActItem(
        code='A-1',
        title='Access to Information Act',
        body='Text of Act',
        start='2016-01-01',
        end='2016-02-01',
    )

    acts_storage.ActsStorage(datastore_client, stor).store(item)

    act_key = datastore_client.key('Act', item.code)
    act = datastore_client.get(act_key)
    assert dict(act) == {'code': 'A-1', 'title': 'Access to Information Act'}

    act_version_key = datastore_client.key('ActVersion', item.start, parent=act_key)
    act_version = datastore_client.get(act_version_key)
    assert dict(act_version) == {'start': '2016-01-01', 'end': '2016-02-01', 'raw_blob': 'acts/raw/A-1/2016-01-01'}
    assert stor.get_blob(act_version['raw_blob']).download_to_string() == 'Text of Act'
