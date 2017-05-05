from google.cloud import datastore


def test_datastore(datastore_client):
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

    query = datastore_client.query(kind='Act')
    query.add_filter('id', '=', 1)
    acts = list(query.fetch())
    assert len(acts) == 1
    assert dict(acts[0].items()) == {'id': 1, 'value': 'foo'}
