import scrapy


class ActItem(scrapy.Item):  # pylint:disable=too-many-ancestors
    body = scrapy.Field()
    title = scrapy.Field()
    code = scrapy.Field()
