from google.cloud import datastore  # pylint:disable=import-error


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
