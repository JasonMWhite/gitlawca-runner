import datetime
import click
from google.cloud import datastore
from google.cloud import pubsub
from scraper import acts_scraper
from scraper import acts_storage
from scraper import spider
from scraper import storage


@click.group()
def main() -> None:
    pass


@main.command()
def trigger() -> None:
    pubsub_client = pubsub.Client()
    topic = pubsub_client.topic('acts_requests')
    topic.publish('http://laws-lois.justice.gc.ca/eng/acts/'.encode('UTF-8'),
                  type='main_page', timestamp=datetime.datetime.now().isoformat())


def _get_spider() -> spider.ActsSpider:
    pubsub_client = pubsub.Client()
    scraper = acts_scraper.ActsScraper()

    datastore_client = datastore.Client()
    stor = storage.get_storage()
    acts_stor = acts_storage.ActsStorage(datastore_client, stor)

    return spider.ActsSpider(pubsub_client, scraper, acts_stor)


@main.command()
@click.option('--wait', type=bool, default=True)
@click.option('--continuous', type=bool, default=True)
def run(wait: bool, continuous: bool) -> bool:
    spider_ = _get_spider()
    if continuous:
        spider_.keep_listening(wait)
        result = True
    else:
        result = spider_.listen(wait)
    return result
