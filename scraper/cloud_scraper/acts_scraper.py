import datetime
import typing
from urllib import parse
from lxml.etree import Element
from lxml.etree import HTML  # type: ignore  # pylint: disable=no-name-in-module
import requests
from requests_file import FileAdapter


class Breadcrumb(typing.NamedTuple):
    url: str
    attrs: typing.Dict[str, str] = {}


class ActItem(typing.NamedTuple):
    code: str
    title: str
    start: str
    end: str
    body: str


ScraperInput = typing.Tuple[Element, str, typing.Mapping[str, str]]
ScraperResult = typing.Tuple[typing.Sequence[Breadcrumb], typing.Sequence[ActItem]]  # pylint:disable=invalid-name


class ActsScraper:

    def __init__(self):
        self.__functions = {
            'main_page': self.parse_main_page,
            'letter_page': self.parse_letter_page,
            'act_main': self.parse_act_main,
        }

    @staticmethod
    def follow_breadcrumb(input_breadcrumb: Breadcrumb) -> ScraperInput:
        sess = requests.Session()
        sess.mount('file://', FileAdapter())

        response = sess.get(input_breadcrumb.url)
        tree = HTML(response.content)

        attrs = input_breadcrumb.attrs.copy()
        attrs.update({
            'timestamp': datetime.datetime.now().isoformat(),
        })

        return tree, response.url, attrs

    @classmethod
    def parse_main_page(cls, scraper_input: ScraperInput) -> ScraperResult:
        tree, response_uri, attrs = scraper_input
        results = []  # type: typing.List[Breadcrumb]

        for link in tree.xpath('//div[@id="alphaList"]//a[@class="btn btn-default"]'):
            assert isinstance(response_uri, str)
            next_uri = parse.urljoin(response_uri, link.attrib['href'])
            attrs = attrs.copy()
            attrs.update({'type': 'letter_page'})
            result = Breadcrumb(url=next_uri, attrs=attrs)
            results.append(result)
        return results, []

    @classmethod
    def parse_letter_page(cls, scraper_input: ScraperInput) -> ScraperResult:
        tree, response_uri, attrs = scraper_input
        results = []  # type: typing.List[Breadcrumb]

        for link in tree.xpath('//div[@class="contentBlock"]/ul/li/span[@class="objTitle"]/a'):
            url = link.attrib['href']
            next_uri = parse.urljoin(response_uri, url)
            attrs = attrs.copy()
            attrs.update({
                'title': link.text.strip(),
                'code': url.split('/')[0].split('.html')[0],
                'type': 'act_main',
            })
            result = Breadcrumb(url=next_uri, attrs=attrs)
            results.append(result)
        return results, []

    @classmethod
    def parse_act_main(cls, scraper_input: ScraperInput) -> ScraperResult:
        tree, response_uri, attrs = scraper_input
        results = []  # type: typing.List[Breadcrumb]

        for link in tree.xpath('//p[@id="assentedDate"]/a'):
            next_url = parse.urljoin(response_uri, link.attrib['href'])
            attrs = attrs.copy()
            attrs.update({'type': 'act_version'})
            result = Breadcrumb(url=next_url, attrs=attrs)
            results.append(result)
        return results, []

    def scrape(self, input_breadcrumb: Breadcrumb) -> ScraperResult:
        input_type = input_breadcrumb.attrs['type']
        tree, response_url, attrs = self.follow_breadcrumb(input_breadcrumb)

        return self.__functions[input_type]((tree, response_url, attrs))
