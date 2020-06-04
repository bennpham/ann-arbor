import json
from models.site import Site
from models.page import Page
from models.axe_audit import AxePageAudit
from models.violation import Violation
from tests.helper import AppTestCase
from tests import helper


class ViolationTest(AppTestCase):
    def test_expects_violation_instance(self):
        # Arrange
        domain = 'sub.domain.com'
        site = Site.from_domain_or_url(domain)
        page = Page(site)
        source = 'test'
        identifier = 'test-error'
        severity = 'low'

        # Act
        violation = Violation(
            page=page,
            source=source,
            identifier=identifier,
            severity=severity
        )

        # Assert
        self.assertIsInstance(violation, Violation)
        self.assertEqual(page, violation.page)
        self.assertEqual(source, violation.source)
        self.assertEqual(identifier, violation.identifier)
        self.assertEqual(severity, violation.severity)

    def test_expects_violation_string_to_have_correct_information(self):
        # Arrange
        domain = 'sub.domain.com'
        site = Site.from_domain_or_url(domain)
        page = Page(site)
        source = 'test'
        identifier = 'test-error'
        severity = 'low'
        expected_output = 'test reported a low test-error error on http://sub.domain.com'

        # Act
        violation = Violation(
            page=page,
            source=source,
            identifier=identifier,
            severity=severity
        )

        # Same as __str__ magic method in Violation
        violation_str = str(violation)

        # Assert
        self.assertEqual(expected_output, violation_str)

    def test_expects_to_filter_by_audit_type(self):
        # Arrange
        domain = 'sub.domain.com'
        site = Site.from_domain_or_url(domain)
        page = Page(site)
        test_axe_report_path = helper.fixture_file_path('httpbin-org-page-all-violations.json')

        with open(test_axe_report_path, "r") as f:
            data = json.loads(f.read())

        axe_errors = data["violations"]

        test_cases = [
            # audit_type   expected_violations_length
            ("design",     2),
            ("code",       3),
            (None,         5)
        ]

        for audit_type, expected_violations_length in test_cases:
            audit = AxePageAudit(page, audit_type)
            sorted_violations = []

            # Act
            for error in axe_errors:
                sorted_violations += Violation.s_from_audit_axe_error(audit, error)

            # Assert
            self.assertEqual(expected_violations_length, len(sorted_violations))
