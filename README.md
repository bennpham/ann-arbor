# Ann Arbor

Ann Arbor is a command-line tool which uses [axe automated testing](https://www.deque.com/axe/) to find accessibility violations.  It can be used to audit a single page or a full site when supplied with a url or domain.  It is important to note that automated tests will not find all accessibility violations in your site, and manual testing is still necessary to find all violations.

Ann Arbor will also show which templates of your site have the most errors, allowing an auditor to prioritize what pages to start with in an audit.


## Environment
- Python = 3.12.5


## Setup
This setup guide uses Pyenv as the python version manager and uses Chromedriver for auditing.  To set up Ann Arbor using these instructions, you will want to install Pyenv and Chromedriver before getting started:

- [Install Pyenv](https://github.com/pyenv/pyenv#installation)
- [Install Chromedriver](https://chromedriver.chromium.org/getting-started)

- Use pyenv to install Python 3.12.x

      pyenv install 3.12.x

- Clone repository:

      git clone git@github.com:formulafolios/ann-arbor.git
      cd ann-arbor

- Set local Python version:

      pyenv local 3.12.0

- Install dependencies:

      pip install -r requirements.txt


## Usage

At this time, Ann Arbor will not crawl password protected sites and will only crawl sites with subdomains if those subdomains are specified.  For example, if you want to crawl example.com, which has a subdomain of www, you will not get an accurate report by running a crawl or report on example.com alone.  If you have multiple subdomains (i.e. www and news), you will need to run multiple reports to cover all pages.  Always check the generated sitemap to make sure all pages you believe should be in the report are listed.

Most commands will create a new file and will print the filepath for where that file is located.  Repeat commands (for example, if a report is run for the same page twice) will overwrite the existing file.  Audits will be generated as CSVs.

In the examples below, httpbin.org is used as a stand in for a domain.  Domains and urls can both be used in these commands, just replace httpbin.org with your own domain or url.  For site-wide reports, use a starting url, usually the home page.

For information on application usage you can type:

    python app.py


### Generate a Sitemap
To see a list of pages in your site, you can run:

    python app.py sitemap httpbin.org

This will generate a sitemap file with a list of urls.


### Audit a Full Website
The default for a site audit is to generate a summary that will list the top 10 templates with errors.  For example, an audit summary might show that example.com/blog has the most violations, followed by example.com/news, followed by example.com/events, and so on through the top ten.  It will then show you the subtemplates with the most violations.  This can be useful in determining where efforts should be focused.  If preferred, the audit summary can be organized by page instead.

- Organize by template (url path):

      python app.py audit --crawl httpbin.org

- Organize by page:

      python app.py audit --crawl --no-templates httpbin.org


### Audit a Single Page

    python app.py audit httpbin.org


### Choose a Report Type

Reports can further be broken down.  Because color contrast can often be a large part of an audit, we have provided the opportunity to run an audit without color contrast and to run a report with only color contrast.  Both of these commands can have `--crawl` added in if you would like to run a report on a full site rather than a single page.

- To audit a page for color contrast violations only:

      python app.py audit httpbin.org --audit_type design

- To audit a page for all violations except color contrast:

      python app.py audit httpbin.org --audit_type code


## Testing
To run tests:

    pytest

To run a single test:

    pytest tests/test_models/test_site.py


## Acknowledgements
Special thanks go to [unleashalicia](https://github.com/unleashalicia) who, as Site Accessibility Engineer at FormulaFolios, wrote most of the code for Ann Arbor when it was an internal project used to analyze the accessibility of web applications and then prepared it for publication as our first open source project.

Additional thanks are due to all the developers who contributed to this project while it was an internal project at FormulaFolios. In open sourcing the project, we reinitialized the source code repository. This was done to reset the commit history and wipe out any sensitive information that may have been inadvertently committed to the repository. Unfortunately, it also erased record of these developers' contributions.


## Licensing
- Ann Arbor is released under the MIT license.  Please see [our license](LICENSE.txt) for more information.
- Dependencies may be subject to their own licenses.  Dependencies are listed in [requirements.txt](requirements.txt).  For dependency licenses, please visit the repositories or documentation for each dependency.


## How to Contribute
We welcome collaboration!  Please check out [our contribution guidelines](CONTRIBUTING.md) and [code of coduct](CODE_OF_CONDUCT.md) to get started.

In addition, please remember that accessibility is a journey, not a destination.  We are here to support everyone on their journey toward more accessible content.  There is no accessibility knowledge prerequesite.  Whether you've been working toward an accessible internet for decades or this README is the first you've heard of accessibility, we welcome feedback and questions.
