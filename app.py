"""
ANN ARBOR
Copyright (c) FormulaFolios
Main application entry point:
    python app.py
"""
from cement import App, Controller
from cement import ex as expose
from models.site import Site
from models.page import Page


class Base(Controller):
    class Meta:
        label = 'base'

    # Audit full site by templates: python app.py audit --crawl httpbin.org
    # Audit full site by pages: python app.py audit --crawl --no-templates httpbin.org
    # Audit single page: python app.py audit httpbin.org
    # Audit page (can be modified for site using above syntax) by design errors only:
        # python appy.py audit httpbin.org --audit_type design
    # By code errors only, excludes design:
        # python app.py audit httpbin.org --audit_type code
    @expose(
        help="Audit a page or full site.",
        arguments=[
            (['domain_or_url'], dict(action='store', nargs=1, help='domain or url')),
            (['--audit_type'], dict(action='store',
                                    help='specify design or code for which type of report to run')),
            (['--crawl'], dict(action='store_true', help='crawl all links from target')),
            (['--no-templates'], dict(action='store_true',
                                      help='group violations by page rather than templates'))
        ]
    )
    def audit(self):
        # Command-line options
        domain_or_url = self.app.pargs.domain_or_url[0]
        audit_type = self.app.pargs.audit_type
        use_templates = not self.app.pargs.no_templates

        site = Site.from_domain_or_url(domain_or_url, audit_type=audit_type,
                                       templates=use_templates)

        if self.app.pargs.crawl:
            audit = site.audit()
        else:
            audit = Page.audit(site, audit_type=audit_type)

        audit.write_violations_to_csv()
        print(audit.summary)

    # python app.py sitemap httpbin.org
    @expose(
        help="Generate a sitemap for given url or domain.",
        arguments=[(['domain_or_url'], dict(action='store', nargs=1, help='domain or url'))]
    )
    def sitemap(self):
        site = Site.from_domain_or_url(self.app.pargs.domain_or_url[0])
        sitemap_path = site.generate_sitemap()
        print("Generated sitemap: {}\nRuntime: {}".format(sitemap_path, site.runtime))

    @expose(
        help="Test Cement framework and CLI.",
        arguments=[
            (['-f', '--foo'], dict(action='store', help='the notorious foo')),

            # https://github.com/datafolklabs/cement/issues/256
            (['target'], dict(action='store', nargs=1)),
            (['extras'], dict(action='store', nargs='*'))
        ]
    )
    def test(self):
        self.app.args.print_help()
        print('You have called test.')
        print('foo: {}'.format(self.app.pargs.foo))
        print('target: {}'.format(self.app.pargs.target))
        print('extras: {}'.format(self.app.pargs.extras))


class AnnArbor(App):
    class Meta:
        label = 'ann_arbor'
        handlers = [Base]


if __name__ == "__main__":
    with AnnArbor() as app:
        app.run()
