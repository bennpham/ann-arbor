"""
Page Model

Relationships
- belongs_to site
- has_one audit

Fields
- url
"""
from urllib.parse import urlparse
from models.axe_audit import AxeAudit


class Page(object):
    def __init__(self, site, url=None):
        self.site = site
        self.url = url if url else site.url
        self.audit = None

    #
    # Static Methods
    #
    @staticmethod
    def audit(site, **options):
        page = Page(site)
        audit_type = options.get("audit_type")
        AxeAudit.validate_type(audit_type)

        return AxeAudit.from_page(page, audit_type)

    #
    # Properties
    #
    @property
    def violations(self):
        if not self.audit:
            return []
        return self.audit.violations

    @property
    def path(self):
        url_path = urlparse(self.url).path

        if url_path.startswith('/'):
            url_path = url_path[1:]
        if url_path.endswith('/'):
            url_path = url_path[:-1]

        return url_path

    @property
    def templates(self):
        # Segments of the URL path are assumed to be templates. This can be used to group
        # pages.
        templates = [self.path] if self.path != '' else []
        path = self.path

        while path != '':
            path, _, _ = path.rpartition('/')
            if path != '':
                templates.append(path)

        return templates

    @property
    def template(self):
        if self.templates:
            return self.templates[-1]

    @property
    def subtemplate(self):
        if len(self.templates) > 1:
            return self.templates[-2]

    #
    # Instance Methods
    #
    def axe_audit(self, audit_type):
        self.audit = AxeAudit.from_page(self, audit_type)
        return self
