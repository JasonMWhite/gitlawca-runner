import time
from google.cloud import datastore  # pylint:disable=import-error


def test_datastore_is_clean(datastore_client):
    key = datastore_client.key('Act')

    query = datastore_client.query(kind='Act')
    query.add_filter('id', '=', 1)
    acts = list(query.fetch())
    assert acts == []

    new_act = datastore.Entity(key)
    new_act.update({
        'id': 1,
        'value': 'foo'
    })
    datastore_client.put(new_act)
    time.sleep(0.5)

    query = datastore_client.query(kind='Act')
    query.add_filter('id', '=', 1)
    acts = list(query.fetch())
    assert len(acts) == 1
    assert dict(acts[0].items()) == {'id': 1, 'value': 'foo'}


def test_datastore_is_still_clean(datastore_client):
    key = datastore_client.key('Act')

    query = datastore_client.query(kind='Act')
    query.add_filter('id', '=', 1)
    acts = list(query.fetch())
    assert acts == []

    new_act = datastore.Entity(key)
    new_act.update({
        'id': 1,
        'value': 'foo'
    })
    datastore_client.put(new_act)
    time.sleep(0.5)

    query = datastore_client.query(kind='Act')
    query.add_filter('id', '=', 1)
    acts = list(query.fetch())
    assert len(acts) == 1
    assert dict(acts[0].items()) == {'id': 1, 'value': 'foo'}
