from scrapy.spiders import Spider
from scrapy.http import Request


class SitemapSpider(Spider):
    name = 'SitemapSpider'

    def __init__(self, site, *args, **kwargs):
        self.site = site
        self.start_urls = [self.base_url]
        self.unique_links = [self.base_url]
        super(SitemapSpider, self).__init__(*args, **kwargs)

    @property
    def base_url(self):
        return self.site.base_url

    #
    # Instance Methods
    #
    def parse(self, response):
        """Parses each page for link href and recursively parses each of those pages.
        Syntax based on this article:
        https://kalamuna.atlassian.net/wiki/spaces/KALA/pages/50069580
        """
        for extracted_link in response.xpath('//a/@href').extract():
            url = self.site.normalize_url(extracted_link)
            if self.site.is_valid_internal_url(url) and url not in self.unique_links:
                self.write_to_sitemap(url)
                yield Request(url, callback=self.parse)

        return True

    def write_to_sitemap(self, url):
        self.unique_links.append(url)
        with open(self.site.sitemap_path, 'a') as sitemap_file:
            sitemap_file.write("{}\n".format(url))
        return True
