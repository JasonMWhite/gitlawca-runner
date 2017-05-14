import typing
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

    def __act_in_datastore(self, item: ActItem) -> typing.Optional[datastore.Entity]:
        query = self.__datastore.query(kind='Act')
        query.add_filter('code', '=', item['code'])
        acts = list(query.fetch())
        if acts:
            return acts[0]

    def __store_raw_in_storage(self, item: ActItem) -> str:
        path = 'acts/raw/{}'.format(item['code'])
        blob = self.__bucket.get_blob(path)
        blob.upload_from_string(item['body'])
        return path

    def __store_act_in_datastore(self, item: ActItem) -> datastore.Entity:
        key = self.__datastore.key('Act')
        task = datastore.Entity(key, exclude_from_indexes=('body',))

        task.update({
            'title': item['title'],
            'code': item['code'],
        })
        return task

    def export_item(self, item: ActItem) -> ActItem:
        act_entity = self.__act_in_datastore(item)

        if act_entity:
            if not act_entity['raw_blob']:
                act_entity['raw_blob'] = self.__store_raw_in_storage(item)
                self.__datastore.put(act_entity)
        else:
            act_entity = self.__store_act_in_datastore(item)
            act_entity['raw_blob'] = self.__store_raw_in_storage(item)
            self.__datastore.put(act_entity)
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
