import scrapy
from justice.justice import items


class ActsSpider(scrapy.Spider):
    name = 'acts'

    start_urls = ['http://laws-lois.justice.gc.ca/eng/acts/']

    custom_settings = {
        'ITEM_PIPELINES': {
            'justice.justice.pipelines.JusticePipeline': 100
        },
        'LOG_LEVEL': 'WARNING',
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self._parse_main_page)

    @classmethod
    def _parse_main_page(cls, response):
        for link in response.xpath('//div[@id="alphaList"]//a[@class="btn btn-default"]'):
            url = link.xpath('@href').extract_first()
            yield scrapy.Request(url=response.urljoin(url), callback=cls._parse_letter)

    @classmethod
    def _parse_letter(cls, response):
        for link in response.xpath('//div[@class="contentBlock"]/ul/li/span[@class="objTitle"]/a'):
            url = link.xpath('@href').extract_first()
            metadata = {
                'title': link.xpath('text()').extract_first().strip(),
                'code': url.split('/')[0].split('.html')[0]
            }
            yield scrapy.Request(url=response.urljoin(url), callback=cls._parse_act, meta=metadata)

    @classmethod
    def _parse_act(cls, response):
        for link in response.xpath('//div[@id="printAll"]/ul/li/a[text()="HTML"]'):
            url = link.xpath('@href').extract_first()
            yield scrapy.Request(url=response.urljoin(url), callback=cls._parse_act_fulltext, meta=response.meta)

    @staticmethod
    def _parse_act_fulltext(response):
        for doc in response.xpath('//div[@id="docCont"]'):
            yield items.ActItem(
                body=doc.extract(),
                title=response.meta['title'],
                code=response.meta['code'],
            )