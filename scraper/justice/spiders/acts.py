import re
import scrapy
from scraper.justice import items


class ActsSpider(scrapy.Spider):
    name = 'acts'

    start_urls = ['http://laws-lois.justice.gc.ca/eng/acts/']

    custom_settings = {
        'ITEM_PIPELINES': {
            'scraper.justice.pipelines.JusticePipeline': 100
        },
        'LOG_LEVEL': 'WARNING',
    }

    def parse(self, _):
        pass

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
            yield scrapy.Request(url=response.urljoin(url), callback=cls._parse_act_main_page, meta=metadata)

    @classmethod
    def _parse_act_main_page(cls, response):
        for link in response.xpath('//p[@id="assentedDate"]/a/@href'):
            url = link.extract()
            yield scrapy.Request(url=response.urljoin(url), callback=cls._parse_act_versions, meta=response.meta)

    @classmethod
    def _parse_act_versions(cls, response):
        pattern = re.compile('From (\\d{4}-\\d{2}-\\d{2}) to (\\d{4}-\\d{2}-\\d{2})')
        results = []
        for link in response.xpath('//main[@property="mainContentOfPage"]/ul//a'):
            url = link.xpath('@href').extract_first()
            text = link.xpath('text()').extract_first()
            parsed_text = re.match(pattern, text)

            result = {
                'url': url,
                'start': parsed_text.group(1),
                'end': parsed_text.group(2),
            }
            results.append(result)

        first_result = True
        for result in sorted(results, key=lambda r: r['start'], reverse=True):
            url = result['url']
            meta = response.meta.copy()
            meta['start'] = result['start']
            if first_result:
                meta['end'] = ''
                first_result = False
            else:
                meta['end'] = result['end']
            yield scrapy.Request(url=response.urljoin(url), callback=cls._parse_act_fulltext, meta=meta)

    @staticmethod
    def _parse_act_fulltext(response):
        for doc in response.xpath('//div[@id="wb-cont"]'):
            yield items.ActItem(
                body=doc.extract(),
                title=response.meta['title'],
                code=response.meta['code'],
                start=response.meta['start'],
                end=response.meta['end'],
            )
