from google.cloud import datastore  # pylint:disable=import-error
from scrapy import exporters
from scrapy import signals
from scraper import storage
from scraper.justice.items import ActItem


class DataStoreExporter(exporters.BaseItemExporter):

    def __init__(self, ds: datastore.Client, st: storage.Storage, **kwargs) -> None:
        super().__init__(**kwargs)
        self.__datastore = ds
        self.__bucket = st
        self.export_empty_fields = True

    def __act_in_datastore(self, item: ActItem) -> datastore.Entity:
        act_key = self.__datastore.key('Act', item['code'])
        act = self.__datastore.get(act_key)

        if not act:
            act = datastore.Entity(act_key)
            act.update({
                'code': item['code'],
                'title': item['title'],
            })
            self.__datastore.put(act)
        return act

    def __version_in_datastore(self, item: ActItem, act: datastore.Entity) -> datastore.Entity:
        version_key = self.__datastore.key('ActVersion', item['start'], parent=act.key)
        version = self.__datastore.get(version_key)

        if not version:
            version = datastore.Entity(version_key)
            version.update({
                'start': item['start'],
                'end': item['end'],
            })
            self.__datastore.put(version)
        return version

    def __store_raw_in_storage(self, item: ActItem) -> str:
        path = 'acts/raw/{}/{}'.format(item['code'], item['start'])
        blob = self.__bucket.get_blob(path)
        blob.upload_from_string(item['body'])
        return path

    def export_item(self, item: ActItem) -> ActItem:
        act_entity = self.__act_in_datastore(item)
        version_entity = self.__version_in_datastore(item, act_entity)

        if not version_entity.get('raw_blob'):
            version_entity['raw_blob'] = self.__store_raw_in_storage(item)
            self.__datastore.put(version_entity)
        return item


class JusticePipeline(object):

    DATASTORE_PROJECT_KEY = 'DATASTORE_PROJECT_ID'

    def __init__(self, exporter: DataStoreExporter) -> None:
        self.exporter = exporter

    @classmethod
    def from_crawler(cls, crawler):
        project = crawler.settings.get(cls.DATASTORE_PROJECT_KEY)
        client = datastore.Client(project)
        stor = storage.get_storage()
        exporter = DataStoreExporter(client, stor)

        pipeline = cls(exporter)
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):  # pylint:disable=unused-argument
        self.exporter.start_exporting()

    def spider_closed(self, spider):  # pylint:disable=unused-argument
        self.exporter.finish_exporting()

    def process_item(self, item, _):
        self.exporter.export_item(item)
        return item
