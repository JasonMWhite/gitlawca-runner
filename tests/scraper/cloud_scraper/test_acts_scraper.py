import os
from scraper.cloud_scraper import acts_scraper


def get_fixture(*rel_path: str) -> str:
    return os.path.join(os.path.dirname(__file__), '..', *rel_path)


def test_parse_main_page() -> None:
    fixture_filename = get_fixture('justice', 'fixtures', 'acts_home.html')
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs={'type': 'main_page'})

    scraper = acts_scraper.ActsScraper()
    breadcrumbs, items = scraper.scrape(input_breadcrumb)
    assert items == []
    assert len(breadcrumbs) == 2
    assert all([crumb.attrs['type'] == 'letter_page' for crumb in breadcrumbs])

    destinations = sorted([crumb.url.split(os.sep)[-1] for crumb in breadcrumbs])
    assert destinations == ['A.html', 'B.html']


def test_parse_letter_page() -> None:
    fixture_filename = get_fixture('justice', 'fixtures', 'A.html')
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
    fixture_filename = get_fixture('justice', 'fixtures', 'A-1/index.html')
    attrs = {'code': 'A-1', 'title': 'Access to Information Act', 'type': 'act_main'}
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs=attrs)

    scraper = acts_scraper.ActsScraper()
    breadcrumbs, items = scraper.scrape(input_breadcrumb)

    assert items == []
    assert len(breadcrumbs) == 1
    assert breadcrumbs[0].url.endswith('A-1/PITIndex.html')
    assert breadcrumbs[0].attrs['code'] == 'A-1'
    assert breadcrumbs[0].attrs['title'] == 'Access to Information Act'
    assert breadcrumbs[0].attrs['type'] == 'act_versions'
    assert 'timestamp' in breadcrumbs[0].attrs


def test_parse_act_versions() -> None:
    fixture_filename = get_fixture('justice', 'fixtures', 'A-1/PITIndex.html')
    attrs = {'code': 'A-1', 'title': 'Access to Information Act', 'type': 'act_versions'}
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs=attrs)

    scraper = acts_scraper.ActsScraper()
    breadcrumbs, items = scraper.scrape(input_breadcrumb)

    assert items == []
    breadcrumbs = sorted(breadcrumbs, key=lambda b: b.url)
    assert len(breadcrumbs) == 3
    assert breadcrumbs[0].url.endswith('A-1/20150709/P1TT3xt3.html')
    assert breadcrumbs[1].url.endswith('A-1/20150730/P1TT3xt3.html')
    assert breadcrumbs[2].url.endswith('A-1/20160405/P1TT3xt3.html')
    assert all([crumb.attrs['code'] == 'A-1' for crumb in breadcrumbs])
    assert all([crumb.attrs['title'] == 'Access to Information Act' for crumb in breadcrumbs])
    assert all([crumb.attrs['type'] == 'act_version' for crumb in breadcrumbs])
    assert [crumb.attrs['start'] for crumb in breadcrumbs] == [
        '2015-07-09', '2015-07-30', '2016-04-05'
    ]
    assert [crumb.attrs['end'] for crumb in breadcrumbs] == [
        '2015-07-29', '2016-04-04', ''
    ]
