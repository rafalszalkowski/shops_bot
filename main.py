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

CHAT_ID_RTX3080 = "-1001442476457"

SAVED_RESULT_PATH = os.path.join(os.getenv("OUTPUT_FOLDER", default="outputs"), "outputs.json")
LINKS_ORIGIN_PATH = "links_3080.txt"
LINKS_LATER_PATH = os.path.join(os.getenv("OUTPUT_FOLDER", default="outputs"), "links_3080.txt")
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36'}

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)-15s %(levelname)-8s %(message)s")

counter = 0


def get_lines(tree, search):
    return [line for line in tree.text_content().split("\n") if search in line]


class PageParser(abc.ABC):
    def __init__(self, domain):
        self.domain = domain

    def is_this_page(self, link):
        return self.domain in link

    @abc.abstractmethod
    def parse(self, tree):
        pass


class MediaExpertParser(PageParser):
    def __init__(self):
        super().__init__("mediaexpert.pl")

    def parse(self, tree):
        available = "Produkt chwilowo" not in tree.text_content()
        price_lines = get_lines(tree, "ecomm_pvalue:")
        if not available or not price_lines:
            return None
        price = price_lines[0][len(' ecomm_pvalue: \''):-2]
        return price


class XKomParser(PageParser):
    def __init__(self):
        super().__init__("x-kom.pl")

    def parse(self, tree):
        if tree.xpath('//text()="Powiadom o dostępności"') or "Wycofany" in tree.text_content():
            return None
        elems = tree.xpath('//div[@class="u7xnnm-4 jFbqvs"]/text()')
        return elems[0] if elems else None


class SferisParser(PageParser):
    def __init__(self):
        super().__init__("sferis.pl")

    def parse(self, tree):
        if tree.xpath('//text()="Produkt chwilowo niedostępny"'):
            return None
        elems = tree.xpath('//div[@class="prices multi"]/span/text()')
        return elems[0] if elems else None


class KomputronikParser(PageParser):
    def __init__(self):
        super().__init__("komputronik.pl")

    def parse(self, tree):
        if "unavailable" in tree.text_content():
            return None
        elems = tree.xpath('//span[@class="price"]/span[@class="proper"]/text()[1]')
        return str(elems[0]).strip() if elems else None


class MoreleParser(PageParser):
    def __init__(self):
        super().__init__("morele.net")

    def parse(self, tree):
        if "PRODUKT NIEDOSTĘPNY" in tree.text_content():
            return None
        elems = tree.xpath('//div[@class="product-price"]/text()[1]')
        return str(elems[0]).strip() if elems else None


class ProlineParser(PageParser):
    def __init__(self):
        super().__init__("proline.pl")

    def parse(self, tree):
        if "Brak towaru" in tree.text_content():
            return None
        elems = tree.xpath('(//div[@class="cell-round-title"]//b[@class="cena_b"])[1]/span/text()')
        return str(elems[0]).strip() if elems else None


class NbbParser(PageParser):
    def __init__(self):
        super().__init__("notebooksbilliger.de")

    def parse(self, tree):
        if "Dieses Produkt ist leider ausverkauft." in tree.text_content():
            return None
        elems = tree.xpath(
            '//div[@class="right_column pdw_rc"]//form[@name="cart_quantity"]//span[@class="product-price__regular js-product-price"]/text()')
        return str(elems[0]).strip() if elems else None


class Komtek24(PageParser):
    def __init__(self):
        super().__init__("komtek24.pl")

    def parse(self, tree):
        if tree.xpath('//fieldset[@class="availability-notifier-container"]//span[text()="powiadom o dostępności"]'):
            return None
        elems = tree.xpath('//em[@class="main-price"]/text()')
        return str(elems[0]).strip() if elems else None


class FoxKomputer(PageParser):
    def __init__(self):
        super().__init__("foxkomputer.pl")

    def parse(self, tree):
        if "Ten produkt jest niedostępny." in tree.text_content():
            return None
        elems = tree.xpath('//em[@class="main-price"]/text()')
        return str(elems[0]).strip() if elems else None


class RtvEuro(PageParser):
    def __init__(self):
        super().__init__("www.euro.com.pl")

    def parse(self, tree):
        if get_lines(tree, "unavailableAtTheMoment: true,"):
            return None
        price_lines = get_lines(tree, "price: ")
        return price_lines[0][10:-2] if price_lines else None


PARSERS = [MediaExpertParser(), XKomParser(), SferisParser(), KomputronikParser(), MoreleParser(), ProlineParser(),
           NbbParser(), Komtek24(), FoxKomputer(), RtvEuro()]


def _is_supported(link):
    return bool([parser for parser in PARSERS if parser.is_this_page(link)])


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
    telegram_sender.send(CHAT_ID_RTX3080, message)


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
