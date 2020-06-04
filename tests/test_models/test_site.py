import requests_mock

from models.site import Site
from tests import helper


class SiteTest(helper.AppTestCase):
    @requests_mock.mock()
    def test_expects_new_site_from_domain(self, webmock):
        # Arrange
        domain = 'sub.domain.com'
        webmock.get(requests_mock.ANY, text='ok')

        # Act
        site = Site(domain)

        # Assert
        self.assertIsInstance(site, Site)
        self.assertEqual('https', site.scheme)
        self.assertEqual('sub', site.subdomain)
        self.assertEqual('domain', site.domain)
        self.assertEqual('com', site.tld)
        self.assertEqual('sub.domain.com', site.fqdn)
        self.assertEqual('https://sub.domain.com', site.url)

    def test_expects_new_site_from_url(self):
        # Arrange
        url = 'http://sub.domain.com/path?q=foo'

        # Act
        site = Site(url)

        # Assert
        self.assertEqual(url, site.url)
        self.assertEqual('http', site.scheme)
        self.assertEqual('http://sub.domain.com', site.base_url)

    @requests_mock.mock()
    def test_expects_to_normalize_urls(self, webmock):
        # Arrange
        domain = 'sub.domain.com'
        site = Site.from_domain_or_url(domain)
        webmock.get(requests_mock.ANY, text='ok')

        test_cases = [
            # link,                     expected_url
            ['http://sub.domain.com/',  'http://sub.domain.com'],
            ['http://sub.domain.com',   'http://sub.domain.com'],
            ['/',                       'http://sub.domain.com'],
            ['/foo',                    'http://sub.domain.com/foo'],
            ['foo',                     'http://sub.domain.com/foo'],
            ['foo/bar',                 'http://sub.domain.com/foo/bar'],
            ['https://google.com',      'https://google.com'],
            ['https://google.com/',     'https://google.com/'],
            ['http://localhost/',       'http://localhost/'],
            ['http://localhost:3000/',  'http://localhost:3000/']
        ]

        # Act / Assert
        for url, expected_url in test_cases:
            normalized_url = site.normalize_url(url)
            self.assertEqual(expected_url, normalized_url)

    @requests_mock.mock()
    def test_expects_to_validate_internal_urls(self, webmock):
        # Arrange
        webmock.get(requests_mock.ANY, text='ok')
        domain = 'sub.domain.com'
        site = Site.from_domain_or_url(domain)

        test_cases = [
            # url,                                                  is_valid
            ['https://sub.domain.com/',                             True],
            ['https://sub.domain.com/foo',                          True],
            ['https://sub.domain.com/foo?q=foo',                    True],
            ['https://domain.com/',                                 False],
            ['foo/bar',                                             False],
            ['https://google.com',                                  False],
            ['https://google.com/',                                 False],
            ['https://sub.domain.com/mailto:anon@domain.com',       False],
            ['https://sub.domain.com/tel:555-555-5555',             False],
            ['https://sub.domain.com/fax:555-555-5555',             False],
            ['https://sub.domain.com/foo#header',                   False],
            ['https://sub.domain.com/javascript: openMarker(1)',    False],
            ['https://sub.domain.com/foo.jpg',                      False],
            ['https://sub.domain.com/foo.mp3',                      False],
            ['https://sub.domain.com/foo.mov',                      False],
            ['https://sub.domain.com/foo.pdf',                      False]
        ]

        # Act / Assert
        for url, expected in test_cases:
            is_valid = site.is_valid_internal_url(url)
            self.assertEqual(expected, is_valid, url)

    def test_expects_site_for_a_localhost_url(self):
        # Arrange
        url = 'http://localhost:3000/'

        # Act
        site = Site.from_domain_or_url(url)

        # Assert
        self.assertIsInstance(site, Site)
        self.assertEqual('http', site.scheme)
        self.assertEqual('', site.subdomain)
        self.assertEqual('localhost', site.domain)
        self.assertEqual('', site.tld)
        self.assertEqual('localhost', site.fqdn)
        self.assertEqual('http://localhost:3000/', site.url)
        self.assertEqual('http://localhost:3000', site.base_url)
