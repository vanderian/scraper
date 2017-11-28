import os
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from lxml import html


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


def one_page_links(url):
    page = requests.get(url)
    tree = html.fromstring(page.content)
    links = set(tree.xpath('//a/@href'))
    urls = [x for x in set(links) if str(x).startswith(main_url)]
    site = [main_url + x[1:] for x in set(links) if str(x)[0] == '/' and str(x)[-1] == '/']
    urls.extend(site)
    print(urls)
    return list(set(urls))


def download_image(img_url):
    img_request = requests.request('get', img_url)

    img_content = img_request.content
    with open(os.path.join(path, img_url.split('/')[-1]), 'wb') as f:
        byte_image = bytes(img_content)
        f.write(byte_image)


if __name__ == '__main__':
    main_url = "https://exponea.com/"
    path = init_store()
    one_page_links(main_url)
    # for image in images:
    #     download_image(image, path)
    # print(images)
