import argparse
import concurrent
import os
from concurrent.futures._base import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from itertools import repeat
from multiprocessing.pool import ThreadPool, Pool
from urllib.parse import urljoin

import requests
from lxml import html
from multiprocessing import cpu_count
from urllib3.util import url


class Scraper(object):
    urls = set()
    done = set()
    images = set()

    def __init__(self):
        self.urls = set()
        self.done = set()
        self.images = set()

    def get_input(self):
        parser = argparse.ArgumentParser(description='crawls website tree and downloads images')
        parser.add_argument('base_url', nargs=1, help="base URL of website to scrape")
        args = parser.parse_args()
        self.urls = {args.base_url[0]}

    @staticmethod
    def one_page_crawl(page_url):
        print("crawl on page: %s" % page_url)
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

            # todo extract and support other types
            img = tree.xpath('//img/@src')
            images = [urljoin(page_url, img_url) for img_url in img if str(img_url).startswith('http')]

            return set(urls), set(images)

    def get_links(self):
        if not self.urls:
            print("done, image links parsed: %d" % len(self.images))
            print(*self.images, sep='\n')
            return self.images

        with ThreadPoolExecutor(cpu_count()) as executor:
            future_to_page = {executor.submit(Scraper.one_page_crawl, page_url): page_url for page_url in self.urls}
            for future in as_completed(future_to_page):
                url_done = future_to_page[future]
                links, images = future.result()
                self.images |= images
                self.done.add(url_done)
                self.urls.remove(url_done)
                self.urls |= links - self.done

        print("\nurls to crawl: %s\nurls done: %s\n" % (self.urls, self.done))
        return self.get_links()


class Store(object):
    directory = None

    def __init__(self):
        self.directory = None

    # todo exceptions
    def init_store(self):
        directory = os.path.join(os.getcwd(), "images")
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.directory = directory

    # todo exceptions
    def download_images(self, image_urls):
        with ThreadPoolExecutor(cpu_count()) as executor:
            for _ in executor.map(Store.download_image, repeat(self.directory), image_urls):
                pass

    @staticmethod
    def download_image(folder, image_url):
        print('downloading %s' % image_url)
        img_request = requests.request('get', image_url)
        img_content = img_request.content
        with open(os.path.join(folder, image_url.split('/')[-1]), 'wb') as f:
            byte_image = bytes(img_content)
            f.write(byte_image)
            print("done")


if __name__ == '__main__':
    scraper = Scraper()
    store = Store()
    scraper.get_input()
    store.init_store()
    store.download_images(scraper.get_links())

