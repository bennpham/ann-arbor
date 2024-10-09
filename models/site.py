"""
Site Model

Relationships
- has_many pages

Fields
- url
"""
from datetime import datetime, timezone
import os
from os.path import join as pathjoin
from urllib.parse import urljoin, urlsplit

import requests
from scrapy.crawler import CrawlerProcess
import tldextract
from scrapy.linkextractors import IGNORED_EXTENSIONS

from config.app import AUDITS_DIR
from models.axe_audit import AxeAudit
from models.page import Page
from spiders.sitemap_spider import SitemapSpider


class Site(object):
    USER_AGENT = 'Ann Arbor Spider'

    def __init__(self, domain_or_url, **options):
        # Options
        # Defaults to using templates
        self.group_by_templates = options.get('templates', True)
        self.audit_type = options.get('audit_type')

        self.pages = []
        self.violations = []
        self.last_scanned_at = None
        self.started_at = datetime.now(timezone.utc)
        self.ended_at = None

        self.tld_extract = tldextract.extract(domain_or_url)
        self.scheme = self.extract_scheme(domain_or_url)
        self.port = self.extract_port(domain_or_url)

        if self.scheme:
            self.url = domain_or_url
        else:
            self.scheme = self.get_scheme_by_request()
            self.url = self.base_url

        os.makedirs(self.audit_dir, exist_ok=True)

    #
    # Static Methods
    #
    @staticmethod
    def from_domain_or_url(domain_or_url, **options):
        return Site(domain_or_url, **options)

    #
    # Properties
    #
    @property
    def fqdn(self):
        """fqdn = fully qualified domain name (or full absolute domain name).
        Example: www.example.com.
        For additional info: https://en.wikipedia.org/wiki/Fully_qualified_domain_name
        """
        # tldextract doesn't recognize localhost so we treat it as a special case.
        if self.domain == 'localhost':
            return self.domain
        return self.tld_extract.fqdn

    @property
    def slug(self):
        return self.fqdn.replace('.', '-')

    @property
    def domain(self):
        return self.tld_extract.domain

    @property
    def subdomain(self):
        return self.tld_extract.subdomain

    @property
    def tld(self):
        return self.tld_extract.suffix

    @property
    def base_url(self):
        schemed_fqdn = '%s://%s' % (self.scheme, self.fqdn)

        if self.port:
            schemed_fqdn = '%s:%s' % (schemed_fqdn, self.port)

        return schemed_fqdn

    @property
    def https_url(self):
        return 'https://%s' % (self.fqdn)

    @property
    def http_url(self):
        return 'http://%s' % (self.fqdn)

    @property
    def audit_dir(self):
        return pathjoin(AUDITS_DIR, self.slug)

    @property
    def sitemap_path(self):
        return pathjoin(self.audit_dir, 'sitemap.txt')

    @property
    def runtime(self):
        if not self.ended_at:
            self.ended_at = datetime.now(timezone.utc)
        return self.ended_at - self.started_at

    #
    # Instance Methods
    #
    def audit(self):
        AxeAudit.validate_type(self.audit_type)
        urls = self.extract_site_page_urls_from_sitemap()

        for url in urls:
            page = Page(self, url)
            page.axe_audit(self.audit_type)
            self.pages.append(page)

        return AxeAudit.from_site(self)

    def extract_site_page_urls_from_sitemap(self):
        page_urls = []
        sitemap_path = self.generate_sitemap()

        with open(sitemap_path, 'r') as f:
            for line in f.read().split('\n'):
                if line.strip() and not line.strip().startswith('#'):
                    page_urls.append(line.strip())

        return page_urls

    def generate_sitemap(self):
        with open(self.sitemap_path, 'w') as sitemap_file:
            sitemap_file.write("### Sitemap Draft ###\n")

        self.map_pages_to_sitemap_file_with_spiders()
        self.clean_up_sitemap_file()
        return self.sitemap_path

    def map_pages_to_sitemap_file_with_spiders(self):
        """Generate sitemap file using scrapy spider and crawler process.
        """
        # This process of passing url taken from this Stack Overflow answer:
        # https://stackoverflow.com/questions/40846714/scrapy-python-how-to-pass-url-and-retrieve-url-for-scraping#answer-40846873
        process = CrawlerProcess({'USER_AGENT': self.USER_AGENT})

        # https://kirankoduru.github.io/python/running-scrapy-programmatically.html
        # Accepts a spider class and a list of arguments to pass to it when instantiating.
        process.crawl(SitemapSpider, self)

        # Script blocks here until all spiders are finished
        # https://doc.scrapy.org/en/latest/topics/practices.html#running-multiple-spiders-in-the-same-process
        process.start()
        return self

    def clean_up_sitemap_file(self):
        sitemap_urls = []

        with open(self.sitemap_path, 'r') as f:
            page_urls = [line.strip() for line in f.read().split('\n') if line]

        for url in page_urls:
            normalized_url = self.normalize_url(url)
            if self.is_valid_internal_url(normalized_url):
                sitemap_urls.append(normalized_url)

        sitemap_urls = sorted(list(set(sitemap_urls)))

        with open(self.sitemap_path, 'w') as sitemap_file:
            header_f = "#\n## Sitemap for {} generated {}\n###\n"
            header = header_f.format(self.fqdn, self.started_at.strftime('%F %T'))
            sitemap_file.write(header)
            sitemap_file.write("\n".join(sitemap_urls))

        return self.sitemap_path

    def extract_scheme(self, domain_or_url):
        scheme = urlsplit(domain_or_url).scheme
        return scheme if scheme else None

    def extract_port(self, domain_or_url):
        return urlsplit(domain_or_url).port

    def get_scheme_by_request(self):
        try:
            response = requests.get(self.https_url)
            if response.ok:
                return 'https'
            else:
                return 'http'
        except Exception as e:
            print("Request to {} failed: {}".format(self.https_url, e))
            return 'http'

    def normalize_url(self, url):
        """Normlize url as absolute url. For example, if base_url is https://foo.com,
        will transform url bars/new as follows:
        bars/new -> https://foo.com/bars/new
        """
        is_absolute_url = url.startswith('http://') or url.startswith('https://')
        starts_with_slash = url.startswith('/')

        # Remove trailing slash from base url.
        if url in ['/', '{}/'.format(self.base_url)]:
            url = self.base_url

        if not is_absolute_url and not starts_with_slash:
            url = '/{}'.format(url)

        if not is_absolute_url:
            url = urljoin(self.base_url, url)

        return url

    def is_valid_internal_url(self, normalized_url):
        # Concerning 'javascript:' href
        # https://stackoverflow.com/questions/7755088
        invalid_markers = ['mailto:', 'tel:', 'fax:', '#', 'javascript:']

        if any(marker in normalized_url for marker in invalid_markers):
            return False

        # Scrapy provides a list of file extensions that it will not follow.
        # This makes sure links with those extensions are not added to sitemap
        # https://github.com/scrapy/scrapy/blob/b85943/scrapy/linkextractors/__init__.py#L20-L39
        if any(normalized_url.endswith(extension) for extension in IGNORED_EXTENSIONS):
            return False

        return normalized_url.startswith(self.base_url)
