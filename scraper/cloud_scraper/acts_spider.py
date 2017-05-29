import datetime
import typing
from google.cloud import pubsub
from google.cloud.pubsub import message  # pylint: disable=unused-import
from scraper.cloud_scraper import acts_scraper
from scraper.cloud_scraper import acts_storage


class ActsSpider:

    SEEDS = ['http://laws-lois.justice.gc.ca/eng/acts/']

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

    def seed_topic(self):
        for seed in self.SEEDS:
            self.__topic.publish(seed.encode('utf-8'), timestamp=datetime.datetime.now(), type='main_page')

    def _store_breadcrumbs(self, breadcrumbs: typing.Sequence[acts_scraper.Breadcrumb]) -> None:
        with self.__topic.batch() as batch:
            for breadcrumb in breadcrumbs:
                batch.publish(breadcrumb.url.encode('utf-8'), **breadcrumb.attrs)

    def _store_items(self, items: typing.Sequence[acts_scraper.ActItem]) -> None:
        for item in items:
            self.__storage.store(item)

    def listen(self):
        for ack_id, msg in self.__sub.pull():  # type: str, message.Message
            input_breadcrumb = acts_scraper.Breadcrumb(url=msg.data.decode('utf-8'), attrs=msg.attributes)
            breadcrumbs, items = self.__scraper.scrape(input_breadcrumb)

            self._store_breadcrumbs(breadcrumbs)
            self._store_items(items)

            self.__sub.acknowledge([ack_id])

    def keep_listening(self):
        while True:
            self.listen()
