"""
AxeAudit Model

Relationships
- belongs_to page
- has_many violations

Fields
- created_at
"""
from datetime import datetime, timezone
import json
import os
from os.path import join as pathjoin
import string
import csv
import logging

from selenium.webdriver.remote.remote_connection import LOGGER as webdriver_logger
from selenium import webdriver
from selenium.webdriver import chrome
from axe_selenium_python import Axe
from webdriver_manager.chrome import ChromeDriverManager

from config.app import AUDITS_DIR
from models.violation import Violation


class InvalidAuditType(Exception):
    pass


class AxeAudit(object):
    @staticmethod
    def from_page(page, audit_type):
        audit = AxePageAudit(page, audit_type)
        audit.now()
        return audit

    @staticmethod
    def from_site(site):
        audit = AxeSiteAudit(site)
        return audit

    @staticmethod
    def validate_type(audit_type):
        valid_types = [None, "design", "code"]
        if audit_type not in valid_types:
            error_str = 'Invalid type: {}. Must be from the following: {}'.format(audit_type,
                                                                                  valid_types)
            raise InvalidAuditType(error_str)

    @staticmethod
    def write_to_violation_csv(violations_csv_path, violations):
        with open(violations_csv_path, mode='w') as csv_file:
            fieldnames = ['page_url', 'source', 'identifier', 'severity', 'kind', 'help',
                          'help_url', 'html', 'failure']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()
            for violation in violations:
                violation_data = {
                        'page_url': violation.page.url,
                        'source': violation.source,
                        'identifier': violation.identifier,
                        'severity': violation.severity,
                        'kind': violation.kind,
                        'help': violation.help,
                        'help_url': violation.help_url,
                        'html': violation.html,
                        'failure': violation.failure
                    }
                writer.writerow(violation_data)
        return violations_csv_path

    #
    # Properties
    #
    @property
    def errors(self):
        return [v for v in self.violations if v.is_error()]

    @property
    def warnings(self):
        return [v for v in self.violations if v.is_warning()]

    @property
    def summary(self):
        return self.summarize()

    @property
    def violations_path(self):
        return self.csv_path()

    #
    # Instance Methods
    #
    def write_violations_to_csv(self):
        path = self.violations_path
        return AxeAudit.write_to_violation_csv(path, self.violations)


class AxeSiteAudit(AxeAudit):
    def __init__(self, site):
        self.site = site
        self.type = site.audit_type
        self.created_at = datetime.now(timezone.utc)

    #
    # Properties
    #
    @property
    def violations(self):
        page_violations = []
        for page in self.site.pages:
            page_violations += page.violations
        return page_violations

    #
    # Instance Methods
    #
    def pages_sorted_by_violations(self):
        return sorted(self.site.pages, key=lambda p: len(p.violations), reverse=True)

    def templates_sorted_by_violations(self):
        template_groups = {}

        for page in self.site.pages:
            if not page.template:
                continue
            if page.template not in template_groups:
                template_groups[page.template] = 0
            template_groups[page.template] += len(page.violations)

        # Convert to a list of tuples for sorting: https://stackoverflow.com/a/1296049/9381758
        template_violations = list(template_groups.items())
        return sorted(template_violations, key=lambda tv: tv[1], reverse=True)

    def subtemplates_sorted_by_violations(self):
        subtemplate_groups = {}

        for page in self.site.pages:
            if not page.subtemplate:
                continue
            if page.subtemplate not in subtemplate_groups:
                subtemplate_groups[page.subtemplate] = 0
            subtemplate_groups[page.subtemplate] += len(page.violations)

        # Convert to a list of tuples for sorting: https://stackoverflow.com/a/1296049/9381758
        subtemplate_violations = list(subtemplate_groups.items())
        return sorted(subtemplate_violations, key=lambda tv: tv[1], reverse=True)

    def csv_path(self):
        site_path = pathjoin(AUDITS_DIR, self.site.slug, self.site.slug)
        audit_type = self.type
        audit_type = audit_type if audit_type is not None else "all"
        return "{}-site-{}-violations.csv".format(site_path, audit_type)

    def summarize(self):
        if self.site.group_by_templates:
            return self.summarize_by_templates()
        else:
            return self.summarize_by_pages()

    def summarize_by_templates(self):
        summary_f = r"""
aXe Site Audit Summary
----------------------
domain:         {}
pages:          {}
violations:     {}
\- errors:      {}
\- warnings:    {}

Top Templates by Violations:
{}

Top Subtemplates by Violations:
{}

created:        {}
runtime:        {}

Violations CSV: {}"""

        template_violations_groups = self.templates_sorted_by_violations()[:10]
        subtemplate_violations_groups = self.subtemplates_sorted_by_violations()[:10]

        return summary_f.format(self.site.fqdn,
                                len(self.site.pages),
                                len(self.violations),
                                len(self.errors),
                                len(self.warnings),
                                self.format_violation_groups(template_violations_groups),
                                self.format_violation_groups(subtemplate_violations_groups),
                                self.created_at.strftime('%F %T'),
                                self.site.runtime,
                                self.violations_path)

    def summarize_by_pages(self):
        summary_f = r"""
aXe Site Audit Summary
----------------------
domain:         {}
pages:          {}
violations:     {}
\- errors:      {}
\- warnings:    {}

Top Pages by Violations:
{}

created:        {}
runtime:        {}

Violations CSV: {}"""

        sorted_pages = self.pages_sorted_by_violations()[:10]
        top_page_groups = [(page.url, len(page.violations)) for page in sorted_pages]
        return summary_f.format(self.site.fqdn,
                                len(self.site.pages),
                                len(self.violations),
                                len(self.errors),
                                len(self.warnings),
                                self.format_violation_groups(top_page_groups),
                                self.created_at.strftime('%F %T'),
                                self.site.runtime,
                                self.violations_path)

    def format_violation_groups(self, groups):
        lines = []
        for group_label, violation_count in groups:
            formatted_line = '{}: {}'.format(group_label, violation_count)
            lines.append(formatted_line)

        return "\n".join(lines)

    #
    # Magic Methods
    #
    def __repr__(self):
        F = '<AxeSiteAudit fqdn={} pages={} errors={} warnings={}>'
        return F.format(self.site.fqdn, len(self.site.pages), len(self.errors), len(self.warnings))


class AxePageAudit(AxeAudit):
    def __init__(self, page, audit_type=None):
        self.page = page
        self.type = audit_type
        self.violations = []
        self.started_at = datetime.now(timezone.utc)
        self.ended_at = None
        os.makedirs(self.report_dir, exist_ok=True)

    #
    # Properties
    #
    @property
    def url(self):
        return self.page.url

    @property
    def report_dir(self):
        return self.page.site.audit_dir

    @property
    def runtime(self):
        if not self.ended_at:
            self.ended_at = datetime.now(timezone.utc)
        return self.ended_at - self.started_at

    #
    # Instance Methods
    #
    def now(self):
        json_path = self.generate_report()
        self.violations = self.parse_report(json_path)
        self.ended_at = datetime.now(timezone.utc)
        return self

    def report_file_name(self, file_type):
        # Source: https://stackoverflow.com/a/295146/1093087
        _, fname = self.url.split('://')
        valid_chars = "-_.%s%s" % (string.ascii_letters, string.digits)
        fname = ''.join(c for c in fname if c in valid_chars)
        fname = fname.replace('.', '-')
        audit_type = self.type
        audit_type = self.type if audit_type is not None else "all"
        full_file_name = "{}-page-{}-violations.{}".format(fname, audit_type, file_type)
        return full_file_name

    def generate_report(self):
        # Set logging to only warnings or above to cut down on console clutter
        # https://stackoverflow.com/q/11029717/#answer-11029841
        webdriver_logger.setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        # Run headless
        chrome_options = chrome.options.Options()
        chrome_options.add_argument("--headless")

        # Set up Axe with Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(self.url)
        axe = Axe(driver)

        # Inject axe-core javascript into page and run checks.
        axe.inject()
        results = axe.run()

        # Write results to file
        path = pathjoin(self.report_dir, self.report_file_name("json"))
        axe.write_results(results, path)
        driver.close()
        return path

    def parse_report(self, report_path):
        """
        Axe calls errors violations and warnings incomplete.
        For our usecase, violation is the umbrella term
        that contains both errors and warnings.
        """
        violations = []

        with open(report_path, "r") as f:
            data = json.loads(f.read())

        axe_errors = data["violations"]
        axe_warnings = data["incomplete"]

        for axe_error in axe_errors:
            violations += Violation.s_from_audit_axe_error(self, axe_error)

        for axe_warning in axe_warnings:
            violations += Violation.s_from_audit_axe_warning(self, axe_warning)

        return violations

    def csv_path(self):
        site_name = self.page.site.slug
        page_name = self.report_file_name("csv")
        return pathjoin(AUDITS_DIR, site_name, page_name)

    def summarize(self):
        summary_f = r"""
aXe Page Audit Summary
----------------------
url:          {}
violations:   {}
\- errors:    {}
\- warnings:  {}

runtime:      {}

Violations CSV: {}"""

        return summary_f.format(self.url, len(self.violations), len(self.errors),
                                len(self.warnings), self.runtime, self.violations_path)

    # Magic Methods
    def __repr__(self):
        F = '<AxePageAudit url={} errors={} warnings={} runtime={}>'
        return F.format(self.url, len(self.errors), len(self.warnings), self.runtime)
