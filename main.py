import abc
import json
import logging
import os
import sys
import time
from shutil import copyfile

import requests
import schedule
from lxml import html

import telegram_sender

CHAT_ID = "-1001353392493"

SAVED_RESULT_PATH = os.path.join(os.getenv("OUTPUT_FOLDER", default="outputs"), "outputs.json")
LINKS_ORIGIN_PATH = "links.txt"
LINKS_LATER_PATH = os.path.join(os.getenv("OUTPUT_FOLDER", default="outputs"), "links.txt")
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36'}
SUPPORTED = {"www.mediaexpert.pl", "www.x-kom.pl"}

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)-15s %(levelname)-8s %(message)s")

counter = 0


class PageParser(abc.ABC):

    @abc.abstractmethod
    def is_this_page(self, link):
        pass

    @abc.abstractmethod
    def parse(self, tree):
        pass


class MediaExpertParser(PageParser):
    def is_this_page(self, link):
        return "mediaexpert.pl" in link

    def parse(self, tree):
        elems = tree.xpath('//sticky//div[@data-price]')
        available = "Produkt chwilowo" not in tree.text_content() and elems and 'data-price' in elems[0].attrib
        return "{:,.2f} PLN".format(float(elems[0].attrib['data-price']) / 100.) if available else None


class XKomParser(PageParser):
    def is_this_page(self, link):
        return "x-kom.pl" in link

    def parse(self, tree):
        if tree.xpath('//text()="Powiadom o dostępności"') or "Wycofany" in tree.text_content():
            return None
        elems = tree.xpath('//div[@class="u7xnnm-4 jFbqvs"]/text()')
        return elems[0] if elems else None


class SferisParser(PageParser):
    def is_this_page(self, link):
        return "sferis.pl" in link

    def parse(self, tree):
        if tree.xpath('//text()="Produkt chwilowo niedostępny"'):
            return None
        elems = tree.xpath('//div[@class="prices multi"]/span/text()')
        return elems[0] if elems else None


class KomputronikParser(PageParser):
    def is_this_page(self, link):
        return "komputronik.pl" in link

    def parse(self, tree):
        if "unavailable" in tree.text_content():
            return None
        elems = tree.xpath('//span[@class="price"]/span[@class="proper"]/text()[1]')
        return str(elems[0]).strip() if elems else None


class MoreleParser(PageParser):
    def is_this_page(self, link):
        return "morele.net" in link

    def parse(self, tree):
        if "PRODUKT NIEDOSTĘPNY" in tree.text_content():
            return None
        elems = tree.xpath('//div[@class="product-price"]/text()[1]')
        return str(elems[0]).strip() if elems else None


PARSERS = [MediaExpertParser(), XKomParser(), SferisParser(), KomputronikParser(), MoreleParser()]


def _is_supported(link):
    return bool({link.split("/")[2]} & SUPPORTED)


def process_link(link):
    page = requests.get(link, allow_redirects=True, headers=HEADERS)
    tree = html.fromstring(page.content)
    parsers_for_link = [parser for parser in PARSERS if parser.is_this_page(link)]
    assert len(parsers_for_link) == 1
    price = parsers_for_link[0].parse(tree)
    return str(price) if price else None


def _save_result(current_results):
    json_object = json.dumps(current_results, indent=4)
    with open(SAVED_RESULT_PATH, "w") as outfile:
        outfile.write(json_object)


def _send_alert(current_results: dict):
    message = "\n".join([k + " Cena:" + v for (k, v) in current_results.items()])
    telegram_sender.send(CHAT_ID, message)


def job(previous_results, current_results, next_request_seconds):
    global counter
    logging.info(f"I'm working in loop: {counter}")
    counter += 1
    result = {}
    links = _get_links()
    for link in links:
        if _is_supported(link):
            price = process_link(link)
            logging.info(f"Fetched for {link} price {price}")
            if price:
                result[link] = price
            time.sleep(next_request_seconds)
        else:
            logging.info(f"Link not supported:{link}")

    current_results.clear()
    current_results.update(result)

    _send_and_save_results_if_difference(current_results, previous_results)


def _send_and_save_results_if_difference(current_results, previous_results):
    different_dict = {k: v for k, v in current_results.items() if
                      (k in previous_results and v != previous_results[k]) or k not in previous_results}
    if previous_results != different_dict:
        # previous_results.clear()
        previous_results.update(different_dict)
        if different_dict:
            _send_alert(different_dict)
        _save_result(previous_results)
    elif not os.path.isfile(SAVED_RESULT_PATH):
        _save_result(current_results)


def _get_links():
    links_path = LINKS_LATER_PATH if os.path.isfile(LINKS_LATER_PATH) else LINKS_ORIGIN_PATH
    if not os.path.isfile(LINKS_LATER_PATH):
        copyfile(LINKS_ORIGIN_PATH, LINKS_LATER_PATH)

    with open(links_path, "r") as links_f:
        lines = links_f.read().splitlines()
        return [line.strip() for line in lines if line.strip() and line.strip()[0] != "#"]


def _read_saved_results():
    if not os.path.isfile(SAVED_RESULT_PATH):
        return {}

    with open(SAVED_RESULT_PATH, "r") as f:
        return json.load(f)


if __name__ == '__main__':
    logging.info("Starting program")
    previous = _read_saved_results()
    current = previous.copy()
    schedule.every(int(os.getenv("REFRESH_MINUTES", default=10))). \
        minutes.do(job, previous, current, int(os.getenv("NEXT_QUERY_SECONDS", default=15)))
    while True:
        schedule.run_pending()
        time.sleep(1)
