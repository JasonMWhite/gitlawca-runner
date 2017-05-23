from google.cloud import pubsub  # pylint:disable=import-error


def test_pubsub_is_blank(pubsub_client: pubsub.Client) -> None:
    topic = pubsub_client.topic('topic')
    assert not topic.exists()
    topic.create()

    sub = topic.subscription('my_sub')
    assert not sub.exists()
    sub.create()
    assert sub.pull(return_immediately=True) == []

    topic.publish(b'test message', foo='bar')

    pulled = sub.pull()
    for ack_id, message in pulled:
        assert message.data == b'test message'
        assert message.attributes['foo'] == 'bar'
        sub.acknowledge([ack_id])


def test_pubsub_is_still_blank(pubsub_client: pubsub.Client) -> None:
    topic = pubsub_client.topic('topic')
    assert not topic.exists()
    topic.create()

    sub = topic.subscription('my_sub')
    assert not sub.exists()
    sub.create()
    assert sub.pull(return_immediately=True) == []

    topic.publish(b'test message', foo='bar')

    pulled = sub.pull()
    for ack_id, message in pulled:
        assert message.data == b'test message'
        assert message.attributes['foo'] == 'bar'
        sub.acknowledge([ack_id])
