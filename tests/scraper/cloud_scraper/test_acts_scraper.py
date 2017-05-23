import os
from scraper.cloud_scraper import acts_scraper


def test_parse_main_page() -> None:
    fixture_filename = os.path.join(os.path.dirname(__file__), '..', 'justice', 'fixtures', 'acts_home.html')
    input_breadcrumb = acts_scraper.Breadcrumb(url='file://' + fixture_filename)

    breadcrumbs, items = acts_scraper.parse_main_page(input_breadcrumb)
    assert items == []
    assert len(breadcrumbs) == 2
    assert [crumb.attrs['type'] == 'letter_page' for crumb in breadcrumbs]

    destinations = sorted([crumb.url.split(os.sep)[-1] for crumb in breadcrumbs])
    assert destinations == ['A.html', 'B.html']
