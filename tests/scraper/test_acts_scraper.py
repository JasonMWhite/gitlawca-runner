import datetime
import os

from scraper import acts_scraper


def get_fixture(*rel_path: str) -> str:
    return os.path.join(os.path.dirname(__file__), 'fixtures', *rel_path)


def test_parse_main_page() -> None:
    fixture_filename = get_fixture('acts_home.html')
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs={'type': 'main_page'})

    scraper = acts_scraper.ActsScraper()
    result = scraper.scrape(input_breadcrumb)
    assert result
    breadcrumbs, items = result
    assert items == []
    assert len(breadcrumbs) == 2
    assert all([crumb.attrs['type'] == 'letter_page' for crumb in breadcrumbs])
    assert all([crumb.attrs['timestamp'] for crumb in breadcrumbs])

    destinations = sorted([crumb.url.split(os.sep)[-1] for crumb in breadcrumbs])
    assert destinations == ['A.html', 'B.html']


def test_parse_main_page_skip_old() -> None:
    fixture_filename = get_fixture('acts_home.html')
    attrs = {'type': 'main_page', 'timestamp': datetime.datetime(2016, 1, 1).isoformat()}
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs=attrs)

    scraper = acts_scraper.ActsScraper()
    result = scraper.scrape(input_breadcrumb)
    assert result
    breadcrumbs, items = result
    assert breadcrumbs == []
    assert items == []


def test_parse_letter_page() -> None:
    fixture_filename = get_fixture('A.html')
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs={'type': 'letter_page'})

    scraper = acts_scraper.ActsScraper()
    result = scraper.scrape(input_breadcrumb)
    assert result
    breadcrumbs, items = result

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


def test_parse_letter_page_skip_old() -> None:
    fixture_filename = get_fixture('A.html')
    attrs = {'type': 'letter_page', 'timestamp': datetime.datetime(2016, 1, 1).isoformat()}
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs=attrs)

    scraper = acts_scraper.ActsScraper()
    result = scraper.scrape(input_breadcrumb)
    assert result
    breadcrumbs, items = result
    assert breadcrumbs == []
    assert items == []


def test_parse_act_main() -> None:
    fixture_filename = get_fixture('A-1', 'index.html')
    attrs = {'code': 'A-1', 'title': 'Access to Information Act', 'type': 'act_main'}
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs=attrs)

    scraper = acts_scraper.ActsScraper()
    result = scraper.scrape(input_breadcrumb)
    assert result
    breadcrumbs, items = result

    assert items == []
    assert len(breadcrumbs) == 1
    assert breadcrumbs[0].url.endswith('A-1/PITIndex.html')
    assert breadcrumbs[0].attrs['code'] == 'A-1'
    assert breadcrumbs[0].attrs['title'] == 'Access to Information Act'
    assert breadcrumbs[0].attrs['type'] == 'act_versions'
    assert 'timestamp' in breadcrumbs[0].attrs


def test_parse_act_main_skip_old() -> None:
    fixture_filename = get_fixture('A-1', 'index.html')
    attrs = {
        'code': 'A-1',
        'title': 'Access to Information Act',
        'type': 'act_main',
        'timestamp': datetime.datetime(2016, 1, 1).isoformat()
    }
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs=attrs)

    scraper = acts_scraper.ActsScraper()
    result = scraper.scrape(input_breadcrumb)
    assert result
    breadcrumbs, items = result
    assert breadcrumbs == []
    assert items == []


def test_parse_act_versions() -> None:
    fixture_filename = get_fixture('A-1', 'PITIndex.html')
    attrs = {'code': 'A-1', 'title': 'Access to Information Act', 'type': 'act_versions'}
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs=attrs)

    scraper = acts_scraper.ActsScraper()
    result = scraper.scrape(input_breadcrumb)
    assert result
    breadcrumbs, items = result

    assert items == []
    breadcrumbs = sorted(breadcrumbs, key=lambda b: b.url)
    assert len(breadcrumbs) == 3
    assert breadcrumbs[0].url.endswith('A-1/20150709/P1TT3xt3.html')
    assert breadcrumbs[1].url.endswith('A-1/20150730/P1TT3xt3.html')
    assert breadcrumbs[2].url.endswith('A-1/20160405/P1TT3xt3.html')
    assert all([crumb.attrs['code'] == 'A-1' for crumb in breadcrumbs])
    assert all([crumb.attrs['title'] == 'Access to Information Act' for crumb in breadcrumbs])
    assert all([crumb.attrs['type'] == 'act_item' for crumb in breadcrumbs])
    assert [crumb.attrs['start'] for crumb in breadcrumbs] == [
        '2015-07-09', '2015-07-30', '2016-04-05'
    ]
    assert [crumb.attrs['end'] for crumb in breadcrumbs] == [
        '2015-07-29', '2016-04-04', ''
    ]


def test_parse_act_versions_skip_old() -> None:
    fixture_filename = get_fixture('A-1', 'PITIndex.html')
    attrs = {
        'code': 'A-1',
        'title': 'Access to Information Act',
        'type': 'act_versions',
        'timestamp': datetime.datetime(2016, 1, 1).isoformat()
    }
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs=attrs)

    scraper = acts_scraper.ActsScraper()
    result = scraper.scrape(input_breadcrumb)
    assert result
    breadcrumbs, items = result
    assert breadcrumbs == []
    assert items == []


def test_parse_act_item() -> None:
    fixture_filename = get_fixture('A-1', '20150709', 'P1TT3xt3.html')
    attrs = {
        'code': 'A-1',
        'title': 'Access to Information Act',
        'type': 'act_item',
        'start': '2015-07-09',
        'end': '2015-07-29'
    }
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs=attrs)

    scraper = acts_scraper.ActsScraper()
    result = scraper.scrape(input_breadcrumb)
    assert result
    breadcrumbs, items = result
    assert breadcrumbs == []
    assert len(items) == 1
    item = items[0]

    assert item.code == 'A-1'
    assert item.title == 'Access to Information Act'
    assert item.start == '2015-07-09'
    assert item.end == '2015-07-29'
    assert len(item.body) > 1000
    assert isinstance(item.body, str)


def test_parse_act_item_skip_old() -> None:
    fixture_filename = get_fixture('A-1', '20150709', 'P1TT3xt3.html')
    attrs = {
        'code': 'A-1',
        'title': 'Access to Information Act',
        'type': 'act_item',
        'start': '2015-07-09',
        'end': '2015-07-29',
        'timestamp': datetime.datetime(2016, 1, 1).isoformat()
    }
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename, attrs=attrs)

    scraper = acts_scraper.ActsScraper()
    result = scraper.scrape(input_breadcrumb)
    assert result
    breadcrumbs, items = result

    assert breadcrumbs == []
    assert items == []
