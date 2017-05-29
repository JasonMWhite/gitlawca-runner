import typing
from google.cloud import pubsub
from google.cloud import datastore
from google.cloud.pubsub import message  # pylint: disable=unused-import
from scraper import logger
from scraper import storage
from scraper.cloud_scraper import acts_scraper
from scraper.cloud_scraper import acts_storage


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

    def listen(self):
        for ack_id, msg in self.__sub.pull():  # type: str, message.Message
            url = msg.data.decode('utf-8')
            LOG.info('Following breadcrumb: %s', url)
            input_breadcrumb = acts_scraper.Breadcrumb(url=url, attrs=dict(msg.attributes))
            breadcrumbs, items = self.__scraper.scrape(input_breadcrumb)

            self._store_breadcrumbs(breadcrumbs)
            self._store_items(items)

            self.__sub.acknowledge([ack_id])

    def keep_listening(self):
        LOG.info('Starting Pub/Sub Listener')
        while True:
            self.listen()


def get_spider() -> ActsSpider:
    pubsub_client = pubsub.Client()
    scraper = acts_scraper.ActsScraper()

    datastore_client = datastore.Client()
    stor = storage.get_storage()
    acts_stor = acts_storage.ActsStorage(datastore_client, stor)

    return ActsSpider(pubsub_client, scraper, acts_stor)


if __name__ == '__main__':
    SPIDER = get_spider()
    SPIDER.keep_listening()
