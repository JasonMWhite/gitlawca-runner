import datetime
import os
from scraper.cloud_scraper import acts_scraper


def test_parse_main_page() -> None:
    fixture_filename = os.path.join(os.path.dirname(__file__), '..', 'justice', 'fixtures', 'acts_home.html')
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs={'type': 'main_page'})

    scraper = acts_scraper.ActsScraper()
    breadcrumbs, items = scraper.scrape(input_breadcrumb)
    assert items == []
    assert len(breadcrumbs) == 2
    assert all([crumb.attrs['type'] == 'letter_page' for crumb in breadcrumbs])

    destinations = sorted([crumb.url.split(os.sep)[-1] for crumb in breadcrumbs])
    assert destinations == ['A.html', 'B.html']


def test_parse_letter_page() -> None:
    fixture_filename = os.path.join(os.path.dirname(__file__), '..', 'justice', 'fixtures', 'A.html')
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs={'type': 'letter_page'})

    scraper = acts_scraper.ActsScraper()
    breadcrumbs, items = scraper.scrape(input_breadcrumb)

    assert items == []
    assert len(breadcrumbs) == 2
    assert all([crumb.attrs['type'] == 'act_main' for crumb in breadcrumbs])

    destinations = sorted([crumb.url for crumb in breadcrumbs])
    assert destinations[0].endswith('A-1.5/index.html')
    assert destinations[1].endswith('A-1/index.html')

    codes = sorted([crumb.attrs['code'] for crumb in breadcrumbs])
    assert codes == ['A-1', 'A-1.5']

    titles = sorted([crumb.attrs['title'] for crumb in breadcrumbs])
    assert titles == ['Access to Information Act', 'Administrative Tribunals Support Service of Canada Act']


def test_parse_act_main() -> None:
    fixture_filename = os.path.join(os.path.dirname(__file__), '..', 'justice', 'fixtures', 'A-1/index.html')
    attrs = {'code': 'A-1', 'title': 'Access to Information Act', 'type': 'act_main'}
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs=attrs)

    scraper = acts_scraper.ActsScraper()
    breadcrumbs, items = scraper.scrape(input_breadcrumb)

    assert items == []
    assert len(breadcrumbs) == 1
    assert breadcrumbs[0].url.endswith('A-1/PITIndex.html')
    assert breadcrumbs[0].attrs['code'] == 'A-1'
    assert breadcrumbs[0].attrs['title'] == 'Access to Information Act'
    assert breadcrumbs[0].attrs['type'] == 'act_version'
    assert 'timestamp' in breadcrumbs[0].attrs
