import requests_mock
from os.path import join as pathjoin

from config.app import AUDITS_DIR
from models.site import Site
from spiders.sitemap_spider import SitemapSpider
from tests import helper


class SitemapSpiderTest(helper.AppTestCase):
    #
    # Fixtures
    #
    def setUp(self):
        test_dir = pathjoin(AUDITS_DIR, "sub-domain-com")
        helper.delete_directory(test_dir)

    def tearDown(self):
        test_dir = pathjoin(AUDITS_DIR, "sub-domain-com")
        helper.delete_directory(test_dir)

    #
    # Tests
    #
    @requests_mock.mock()
    def test_expects_spider_instance(self, webmock):
        # Arrange
        domain = 'sub.domain.com'
        site = Site.from_domain_or_url(domain)
        webmock.get(requests_mock.ANY, text='ok')

        # Act
        spider = SitemapSpider(site)

        # Assert
        self.assertIsInstance(spider, SitemapSpider)
        self.assertEqual(site, spider.site)
        self.assertIn(site.base_url, spider.base_url)
