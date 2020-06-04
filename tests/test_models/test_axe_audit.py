import requests_mock
import csv
from os.path import join as pathjoin

from config.app import AUDITS_DIR
from models.axe_audit import InvalidAuditType, AxeAudit, AxePageAudit, AxeSiteAudit
from models.page import Page
from models.site import Site
from models.violation import Violation
from tests import helper


class AxeAuditTest(helper.AppTestCase):
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
    def test_expects_new_axe_page_audit(self):
        # Arrange
        url = 'https://sub.domain.com'
        site = Site(url)
        page = Page(site)

        # Act
        page_audit = AxePageAudit(page)

        # Assert
        self.assertIsInstance(page_audit, AxePageAudit)
        self.assertEqual(url, page_audit.url)
        self.assertListEqual([], page_audit.violations)

    def test_expects_error_if_invalid_audit_type(self):
        # Arrange
        invalid_audit_types_to_test = ["desing", "cod", "foo"]

        for audit_type in invalid_audit_types_to_test:
            # Assert/Act
            with self.assertRaises(InvalidAuditType):
                AxeAudit.validate_type(audit_type)

    @requests_mock.mock()
    def test_expects_new_axe_site_audit(self, webmock):
        # Arrange
        webmock.get(requests_mock.ANY, text='ok')
        domain = 'sub.domain.com'
        site = Site(domain)

        # Act
        site_audit = AxeSiteAudit(site)

        # Assert
        self.assertIsInstance(site_audit, AxeSiteAudit)
        self.assertEqual(site, site_audit.site)
        self.assertListEqual([], site_audit.violations)

    @requests_mock.mock()
    def test_expects_violations_csv(self, webmock):
        # Assume
        test_dir = pathjoin(AUDITS_DIR, "sub-domain-com")
        self.assertPathDoesNotExist(test_dir)

        # Arrange
        domain = 'sub.domain.com'
        webmock.get(requests_mock.ANY, text='ok')
        site = Site(domain)
        audit = AxeSiteAudit(site)

        # Act
        csv_path = audit.write_violations_to_csv()

        # Assert
        expected_path = pathjoin(test_dir, "sub-domain-com-site-all-violations.csv")
        self.assertEqual(expected_path, csv_path)

    @requests_mock.mock()
    def test_expects_separated_reports(self, webmock):
        # Assume
        test_dir = pathjoin(AUDITS_DIR, "sub-domain-com")
        self.assertPathDoesNotExist(test_dir)

        # Arrange
        domain = 'sub.domain.com'
        webmock.get(requests_mock.ANY, text='ok')
        site = Site(domain)
        test_cases = [
            # audit_type, expected_report_designator
            ("design", "design"),
            ("code", "code"),
            (None, "all")
        ]

        for audit_type, expected_report_designator in test_cases:
            site.audit_type = audit_type
            audit = AxeSiteAudit(site)

            # Act
            csv_path = audit.write_violations_to_csv()

            # Assert
            filename_template = "sub-domain-com-site-{}-violations.csv"
            expected_filename = filename_template.format(expected_report_designator)
            expected_path = pathjoin(test_dir, expected_filename)
            self.assertEqual(expected_path, csv_path)

    @requests_mock.mock()
    def test_expects_violations_in_csv(self, webmock):
        # Arrange
        test_dir = pathjoin(AUDITS_DIR, "sub-domain-com")
        violations_csv_path = pathjoin(test_dir, "sub-domain-com.csv")
        webmock.get(requests_mock.ANY, text='ok')
        domain = 'sub.domain.com'
        site = Site(domain)
        page = Page(site)
        audit = AxeSiteAudit(site)
        source = 'test'
        identifier = 'test-error'
        severity = 'low'
        violation = Violation(
            page=page,
            source=source,
            identifier=identifier,
            severity=severity
        )
        violation.kind = "error"
        violation.help = "Error must be fixed"
        violation.help_url = "https://help.com"
        violation.html = "<p>Test</p>"
        violation.failure = "This is incorrect"

        # Act
        audit.write_to_violation_csv(violations_csv_path, [violation])
        with open(violations_csv_path, 'r') as file:
            csv_rows = list(csv.reader(file))
            row_count = len(csv_rows)

        # Assert
            self.assertEqual(row_count, 2)
            self.assertEqual(csv_rows[0][0], "page_url")
            self.assertEqual(csv_rows[1][8], violation.failure)
