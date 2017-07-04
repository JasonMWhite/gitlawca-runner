import typing

from google.cloud import pubsub
from google.cloud.pubsub import message  # pylint: disable=unused-import

from scraper import acts_scraper
from scraper import acts_storage
from scraper import logger

LOG = logger.LOG


class ActsSpider:

    def __init__(self, pubsub_client: pubsub.Client,
                 scraper: acts_scraper.Scraper,
                 storage: acts_storage.ActsStorage) -> None:

        self.__pubsub = pubsub_client
        topic = pubsub_client.topic('acts_requests')
        if not topic.exists():
            topic.create()
        self.__topic = topic  # type: pubsub.Topic

        sub = topic.subscription('acts_scraper')
        if not sub.exists():
            sub.create()
        self.__sub = sub
        self.__scraper = scraper
        self.__storage = storage

    def _store_breadcrumbs(self, breadcrumbs: typing.Sequence[acts_scraper.Breadcrumb]) -> None:
        with self.__topic.batch() as batch:
            for breadcrumb in breadcrumbs:
                batch.publish(breadcrumb.url.encode('utf-8'), **breadcrumb.attrs)

    def _store_items(self, items: typing.Sequence[acts_scraper.ActItem]) -> None:
        for item in items:
            self.__storage.store(item)

    def listen(self, wait: bool = True) -> bool:
        message_received = False
        for ack_id, msg in self.__sub.pull(return_immediately=not wait):  # type: str, message.Message
            message_received = True
            url = msg.data.decode('utf-8')
            LOG.info('Following breadcrumb: %s', url)
            input_breadcrumb = acts_scraper.Breadcrumb(url=url, attrs=dict(msg.attributes))
            result = self.__scraper.scrape(input_breadcrumb)

            if result:
                breadcrumbs, items = result
                self._store_breadcrumbs(breadcrumbs)
                self._store_items(items)

            self.__sub.acknowledge([ack_id])
        return message_received

    def keep_listening(self, wait: bool = True) -> None:
        LOG.info('Starting Pub/Sub Listener')
        while True:
            self.listen(wait)
