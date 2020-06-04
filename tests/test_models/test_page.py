from os.path import join as pathjoin
from unittest.mock import patch

import requests_mock

from config.app import AUDITS_DIR
from models.axe_audit import AxePageAudit
from models.page import Page
from models.site import Site
from tests import helper


class PageTest(helper.AppTestCase):
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
    def test_expects_page_instance(self):
        # Arrange
        domain = 'sub.domain.com'
        site = Site.from_domain_or_url(domain)

        # Act
        page = Page(site)

        # Assert
        self.assertIsInstance(page, Page)
        self.assertEqual(page.site, site)
        self.assertIn(domain, page.url)

    @requests_mock.mock()
    def test_expect_successful_page_audit(self, webmock):
        # Arrange
        domain = 'httpbin.org'
        test_axe_report_path = helper.fixture_file_path('httpbin-org-page-all-violations.json')
        webmock.get(requests_mock.ANY, text='ok')
        site = Site.from_domain_or_url(domain)
        page = Page(site)
        audit_type = None

        # Assume
        self.assertIsNone(page.audit)
        self.assertPathExists(test_axe_report_path)

        # Act
        # Mock the AxeAudit generate_report method to return our test fixture file
        # path when page.axe_audit called.
        with patch.object(AxePageAudit, 'generate_report') as mocked_method:
            mocked_method.return_value = test_axe_report_path
            page.axe_audit(audit_type)

        # Assert
        self.assertIsNotNone(page.audit)
        self.assertEqual(page.site, site)
        self.assertIn(domain, page.url)
        self.assertEqual(5, len(page.audit.violations))
        self.assertEqual(5, len(page.audit.errors))
        self.assertEqual(0, len(page.audit.warnings))

    def test_expects_paths(self):
        # Arrange
        test_cases = [
            # url, expected_path
            ('https://sub.domain.com', ''),
            ('https://sub.domain.com/', ''),
            ('https://sub.domain.com/path', 'path'),
            ('https://sub.domain.com/path/', 'path'),
            ('https://sub.domain.com/path/subpath/', 'path/subpath'),
        ]

        # Act / Assert
        for url, expected_path in test_cases:
            # Act
            site = Site.from_domain_or_url(url)
            page = Page(site)

            # Assert
            self.assertEqual(expected_path, page.path, url)
            self.assertEqual(url, page.url)

    def test_expects_templates(self):
        # Arrange
        url = 'https://sub.domain.com/path/subpath/subsubpath/index.html'
        site = Site.from_domain_or_url(url)
        page = Page(site)
        expected_templates = [
            'path/subpath/subsubpath/index.html',
            'path/subpath/subsubpath',
            'path/subpath',
            'path'
        ]

        # Act
        templates = page.templates

        # Assert
        self.assertEqual(expected_templates, templates)

    def test_expects_template(self):
        # Arrange
        test_cases = [
            # url, expected_subtemplate
            ('https://sub.domain.com/path/subpath/subsubpath/index.html', 'path'),
            ('https://sub.domain.com/path/subpath/', 'path'),
            ('https://sub.domain.com/path/', 'path'),
            ('https://sub.domain.com/path', 'path'),
            ('https://sub.domain.com/', None)
        ]

        # Act / Assert
        for url, expected_template in test_cases:
            # Act
            site = Site.from_domain_or_url(url)
            page = Page(site)

            # Assert
            self.assertEqual(expected_template, page.template, url)

    def test_expects_subtemplate(self):
        # Arrange
        test_cases = [
            # url, expected_subtemplate
            ('https://sub.domain.com/path/subpath/subsubpath/index.html', 'path/subpath'),
            ('https://sub.domain.com/path/subpath/', 'path/subpath'),
            ('https://sub.domain.com/path/subpath', 'path/subpath'),
            ('https://sub.domain.com/path/', None),
            ('https://sub.domain.com/', None)
        ]

        # Act / Assert
        for url, expected_subtemplate in test_cases:
            # Act
            site = Site.from_domain_or_url(url)
            page = Page(site)

            # Assert
            self.assertEqual(expected_subtemplate, page.subtemplate, url)
