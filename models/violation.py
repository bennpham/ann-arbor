"""
Violation
A web accessibility violation

Relationships
- belongs_to page

Fields
- page_url
- source
- kind  [error, warning]
- identifier
- severity
- help_url
- html
- failure
"""


class Violation(object):
    @staticmethod
    def s_from_audit_axe_error(audit, axe_error):
        violations = []
        for node in axe_error['nodes']:
            violation = Violation.from_axe_violation_node(axe_error, node, audit.page)
            if audit.type is None or audit.type == violation.type:
                violations.append(violation)
        return violations

    @staticmethod
    def s_from_audit_axe_warning(audit, axe_warning):
        """
        Warnings are possible violations that require review.  From documentation:
        The incomplete array (also referred to as the "review items") indicates which nodes
        could neither be determined to definitively pass or definitively fail.
        https://www.deque.com/axe/documentation/
        """
        violations = []
        for node in axe_warning['nodes']:
            violation = Violation.from_axe_violation_node(axe_warning, node, audit.page)
            if audit.type is None or audit.type == violation.type:
                violation.kind = 'warning'
                violations.append(violation)
        return violations

    @staticmethod
    def from_axe_violation_node(axe_violation, node, page):
        violation = Violation(page=page, source='axe', identifier=axe_violation['id'],
                              severity=node['impact'])
        violation.help = axe_violation['help']
        violation.help_url = axe_violation['helpUrl']
        violation.html = node['html']
        violation.failure = node.get('failureSummary')
        violation.type = 'design' if violation.identifier == 'color-contrast' else 'code'
        return violation

    def __init__(self, **options):
        self.page = options.get('page')
        self.source = options.get('source')
        self.identifier = options.get('identifier')
        self.severity = options.get('severity')
        self.kind = 'error'

    def is_error(self):
        return self.kind == 'error'

    def is_warning(self):
        return self.kind == 'warning'

    # Magic Methods
    def __repr__(self):
        F = '<Violation source={} kind={} identifier={} severity={}>'
        return F.format(self.source, self.kind, self.identifier, self.severity)

    def __str__(self):
        """Why __str__ and not __repr__? See https://stackoverflow.com/a/2626364/9381758.
        """
        F = '{} reported a {} {} {} on {}'
        return F.format(self.source, self.severity, self.identifier, self.kind, self.page.url)
