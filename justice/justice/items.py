import scrapy


class ActItem(scrapy.Item):
    body = scrapy.Field()
    title = scrapy.Field()
    code = scrapy.Field()

