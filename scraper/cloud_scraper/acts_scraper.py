import datetime
import typing
from urllib import parse
from lxml.etree import HTML  # type: ignore  # pylint: disable=no-name-in-module
import requests
from requests_file import FileAdapter


class Breadcrumb(typing.NamedTuple):
    url: str
    attrs: typing.Dict[str, typing.Any]


class ActItem(typing.NamedTuple):
    code: str
    title: str
    start: datetime.date
    end: datetime.date
    body: str


ScraperResult = typing.Tuple[typing.Sequence[Breadcrumb], typing.Sequence[ActItem]]  # pylint:disable=invalid-name


def parse_main_page(input_breadcrumb: Breadcrumb) -> ScraperResult:
    sess = requests.Session()
    sess.mount('file://', FileAdapter())

    response = sess.get(input_breadcrumb.url)
    tree = HTML(response.content)

    responses = []  # type: typing.List[Breadcrumb]

    for link in tree.xpath('//div[@id="alphaList"]//a[@class="btn btn-default"]'):
        assert isinstance(response.request.url, str)
        next_uri = parse.urljoin(response.request.url, link.attrib['href'])
        result = Breadcrumb(url=next_uri.encode('utf-8'),
                            attrs={'timestamp': datetime.datetime.now(), 'type': 'letter_page'})
        responses.append(result)
    return responses, []
