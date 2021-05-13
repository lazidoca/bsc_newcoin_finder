import json
import os
import traceback
from itertools import cycle
from random import choice, uniform
from time import sleep

import requests
from pydash import get as _
from selectolax.parser import HTMLParser

MIN_HOLDERS = 10
MAX_HOLDERS = 100

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
]


def random_ua():
    return choice(USER_AGENTS)


def file2list(filename):
    result = []
    if os.path.isfile(filename):
        with open(filename, encoding='utf-8') as f:
            return f.read().splitlines()
    return []


def load_proxy():
    proxies = set()
    if os.path.exists('./proxy.txt'):
        with open('./proxy.txt', 'r') as f:
            for line in f:
                px = line.strip().split(':')
                proxies.add(f'http://{px[2]}:{px[3]}@{px[0]}:{px[1]}')
    return proxies


proxies = cycle(load_proxy())
coins = set(file2list('coins.txt'))


def get_text(selector: str, soup: HTMLParser):
    try:
        t = (soup.css_first(selector) if selector else soup).text(
            separator=' ', strip=True).replace('\xa0', ' ').replace(
                '\t', ' ').replace('\r', ' ').replace('\n', ' ').strip()
        while '  ' in t:
            t = t.replace('  ', ' ')
        return t
    except:
        return ''


def rand_sleep(start, end):
    sleep(uniform(start, end))


def to_int(s):
    try:
        return int(s.replace(',', '').replace(' ', '').strip())
    except:
        return 0


def sync_fetch(url: str, session=None, headers=None):
    tried = 0
    while tried < 5:
        try:
            proxy = next(proxies, None)
            print(f'Getting {url}')
            return (session or requests).get(
                url,
                headers=headers if headers else {'User-Agent': random_ua()},
                timeout=30,
                proxies={
                    'http': proxy,
                    'https': proxy
                } if proxy else None)

        except KeyboardInterrupt:
            raise KeyboardInterrupt('Abort')
        except:
            traceback.print_exc()
            tried += 1
            sleep(1)


def get_next_elements(selector: str, next_selector, text, soup: HTMLParser):
    try:
        elements = []
        for el in soup.css(selector):
            t = el.text().replace('\xa0', ' ').strip()
            if text == t:
                start = False
                for cnode in el.parent.iter():
                    if cnode == el:
                        start = True
                    elif start:
                        elements.append(cnode)
        return elements
    except:
        return None


def get_attr(selector: str, attr: str, soup: HTMLParser):
    try:
        return (soup.css_first(selector) if selector else soup).attributes.get(
            attr, '').replace('\xa0', ' ').strip()
    except:
        return ''


def sync_bs(url: str, session=None):
    r = sync_fetch(url, session)
    soup = HTMLParser(r.text if r else '')
    return soup


def main():
    while True:
        try:
            soup = sync_bs('https://bscscan.com/tokentxns')
            for el in soup.css('#content td a'):
                href = get_attr(None, 'href', el)

                if '/token/' in href and '/images/main/empty-token.png' in get_attr(
                        'img', 'src', el):
                    url = f'https://bscscan.com{href}'
                    poocoin_url = f'http://poocoin.app/tokens/{href.split("/token/")[-1]}'
                    if url not in coins:
                        s = sync_bs(url)
                        t = get_text(None, s)
                        if 'LPs' in t or '-LP' in t or 'BLP' in t:
                            continue
                        els = get_next_elements('div', 'div', 'Holders:', s)
                        if els:
                            for node in els:
                                text = get_text(None, node)
                                if 'addresses' in text:
                                    holders = to_int(
                                        text.split('addresses')[0])

                                    print(holders, text)
                                    if MIN_HOLDERS < holders < MAX_HOLDERS:
                                        webbrowser.open(url)
                                        webbrowser.open(poocoin_url)
                                    break
                    if holders > MIN_HOLDERS:
                        coins.add(url)
            rand_sleep(1, 3)
        except KeyboardInterrupt:
            return
        except:
            traceback.print_exc()
            sleep(1)


if __name__ == '__main__':
    try:
        main()
    finally:
        with open('coins.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(coins))
