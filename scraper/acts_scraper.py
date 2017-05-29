import abc
import datetime
import re
import typing
from urllib import parse
from lxml import html  # type: ignore
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


ScraperInput = typing.Tuple[html.HtmlElement, str, typing.Dict[str, str]]  # pylint: disable=invalid-name
ScraperResult = typing.Tuple[typing.Sequence[Breadcrumb], typing.Sequence[ActItem]]  # pylint:disable=invalid-name


class Scraper(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def scrape(self, input_breadcrumb: Breadcrumb) -> ScraperResult:
        pass


class ActsScraper(Scraper):

    def __init__(self):
        self.__functions = {
            'main_page': self.parse_main_page,
            'letter_page': self.parse_letter_page,
            'act_main': self.parse_act_main,
            'act_versions': self.parse_act_versions,
            'act_item': self.parse_act_item
        }

    @staticmethod
    def follow_breadcrumb(input_breadcrumb: Breadcrumb) -> ScraperInput:
        sess = requests.Session()
        sess.mount('file://', FileAdapter())

        response = sess.get(input_breadcrumb.url)
        tree = html.fromstring(response.content)

        attrs = input_breadcrumb.attrs.copy()
        attrs['timestamp'] = datetime.datetime.now().isoformat()

        return tree, response.url, attrs

    @classmethod
    def parse_main_page(cls, scraper_input: ScraperInput) -> ScraperResult:
        tree, response_uri, attrs = scraper_input
        results = []  # type: typing.List[Breadcrumb]

        for link in tree.xpath('//div[@id="alphaList"]//a[@class="btn btn-default"]'):
            assert isinstance(response_uri, str)
            next_uri = parse.urljoin(response_uri, link.attrib['href'])
            attrs = attrs.copy()
            attrs['type'] = 'letter_page'
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
            attrs['type'] = 'act_versions'
            result = Breadcrumb(url=next_url, attrs=attrs)
            results.append(result)
        return results, []

    @classmethod
    def parse_act_versions(cls, scraper_input: ScraperInput) -> ScraperResult:
        tree, response_uri, attrs = scraper_input

        results = []  # type: typing.List[Breadcrumb]
        pattern = re.compile('From (\\d{4}-\\d{2}-\\d{2}) to (\\d{4}-\\d{2}-\\d{2})')

        for i, link in enumerate(tree.xpath('//main[@property="mainContentOfPage"]/ul//a')):
            next_url = parse.urljoin(response_uri, link.attrib['href'])
            text = link.text
            parsed_text = re.match(pattern, text)

            link_attrs = attrs.copy()
            link_attrs.update({
                'start': parsed_text.group(1),
                'end': parsed_text.group(2) if i > 0 else '',
                'type': 'act_item'
            })
            result = Breadcrumb(url=next_url, attrs=link_attrs)
            results.append(result)
        return results, []

    @classmethod
    def parse_act_item(cls, scraper_input: ScraperInput) -> ScraperResult:
        tree, _, attrs = scraper_input

        items = []  # type: typing.List[ActItem]
        for content_node in tree.xpath('//div[@id="wb-cont"]'):
            item = ActItem(
                code=attrs['code'],
                title=attrs['title'],
                start=attrs['start'],
                end=attrs['end'],
                body=html.tostring(content_node).decode('utf-8')
            )
            items.append(item)
        return [], items

    def scrape(self, input_breadcrumb: Breadcrumb) -> ScraperResult:
        input_type = input_breadcrumb.attrs['type']
        tree, response_url, attrs = self.follow_breadcrumb(input_breadcrumb)

        return self.__functions[input_type]((tree, response_url, attrs))
