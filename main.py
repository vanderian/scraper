import argparse
import os
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from lxml import html
from urllib3.util import url


class Scraper(object):
    urls = set()
    done = set()

    def __init__(self):
        self.urls = set()
        self.done = set()

    def get_input(self):
        parser = argparse.ArgumentParser(description='crawls website tree and downloads images')
        parser.add_argument('base_url', nargs=1, help="base URL of website to scrape")
        args = parser.parse_args()
        self.urls = {args.base_url[0]}

    @staticmethod
    def one_page_links(page_url):
        host = url.parse_url(page_url)
        host_prefix = host.scheme + "://" + host.hostname

        # todo error load page response != 200
        page = requests.get(page_url)
        if page.status_code != 200:
            print("page error %s" % page_url)
            return set()
        else:
            tree = html.fromstring(page.content)
            links = set(tree.xpath('//a/@href'))
            urls = [x for x in links if str(x).startswith(host_prefix) and str(x)[-1] == '/']
            site_urls = [host_prefix + x for x in set(links) if str(x)[0] == '/' and str(x)[-1] == '/']
            urls.extend(site_urls)
            return set(urls)

    def get_links(self):
        if not self.urls:
            return self.done

        for page in self.urls.copy():
            print("on page: %s" % page)
            links = Scraper.one_page_links(page)
            self.done.add(page)
            self.urls.remove(page)
            self.urls |= links - self.done

        # todo there must be a nicer way to write this
        print("\n")
        print("urls to crawl:")
        print(self.urls)
        print("urls done:")
        print(self.done)
        print("\n")
        return self.get_links()


def init_store():
    directory = os.path.join(os.getcwd(), "images")
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def one_page_images(url):
    page = requests.get(url)
    tree = html.fromstring(page.content)
    img = tree.xpath('//img/@src')
    images = [urljoin(url, img_url) for img_url in img]
    return list(set(images))


def download_image(img_url):
    img_request = requests.request('get', img_url)

    img_content = img_request.content
    with open(os.path.join(path, img_url.split('/')[-1]), 'wb') as f:
        byte_image = bytes(img_content)
        f.write(byte_image)


if __name__ == '__main__':
    scraper = Scraper()
    scraper.get_input()
    scraper.get_links()
