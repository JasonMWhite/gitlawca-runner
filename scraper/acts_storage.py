from google.cloud import datastore

from scraper import acts_scraper
from scraper import storage


class ActsStorage:

    def __init__(self, ds: datastore.Client, st: storage.Storage) -> None:
        self.__datastore = ds
        self.__bucket = st

    def __act_in_datastore(self, item: acts_scraper.ActItem) -> datastore.Entity:
        act_key = self.__datastore.key('Act', item.code)
        act = self.__datastore.get(act_key)

        if not act:
            act = datastore.Entity(act_key)
            act.update({
                'code': item.code,
                'title': item.title,
            })
            self.__datastore.put(act)
        return act

    def __act_version_in_datastore(self, item: acts_scraper.ActItem, act_key: datastore.Key):
        version_key = self.__datastore.key('ActVersion', item.start, parent=act_key)
        version = self.__datastore.get(version_key)

        if not version:
            version = datastore.Entity(version_key)
            version.update({
                'start': item.start,
                'end': item.end,
            })
            self.__datastore.put(version)
        return version

    def __store_raw_in_storage(self, item: acts_scraper.ActItem) -> str:
        path = 'acts/raw/{}/{}'.format(item.code, item.start)
        blob = self.__bucket.get_blob(path)
        blob.upload_from_string(item.body)
        return path

    def store(self, item: acts_scraper.ActItem) -> None:
        act = self.__act_in_datastore(item)
        act_version = self.__act_version_in_datastore(item, act.key)

        if not act_version.get('raw_blob'):
            act_version['raw_blob'] = self.__store_raw_in_storage(item)
            self.__datastore.put(act_version)
