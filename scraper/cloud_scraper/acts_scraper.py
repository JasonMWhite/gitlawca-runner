import datetime
import typing
from urllib import parse
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


ScraperResult = typing.Tuple[typing.Sequence[Breadcrumb], typing.Sequence[ActItem]]  # pylint:disable=invalid-name


def parse_main_page(input_breadcrumb: Breadcrumb) -> ScraperResult:
    sess = requests.Session()
    sess.mount('file://', FileAdapter())

    response = sess.get(input_breadcrumb.url)
    tree = HTML(response.content)

    responses = []  # type: typing.List[Breadcrumb]

    for link in tree.xpath('//div[@id="alphaList"]//a[@class="btn btn-default"]'):
        assert isinstance(response.url, str)
        next_uri = parse.urljoin(response.url, link.attrib['href'])
        result = Breadcrumb(url=next_uri,
                            attrs={'timestamp': datetime.datetime.now().isoformat(), 'type': 'letter_page'})
        responses.append(result)
    return responses, []
