import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from shutil import copyfile

import requests
import schedule
from lxml import html

import telegram_sender
from parsers import MediaExpertParser, XKomParser, SferisParser, KomputronikParser, MoreleParser, ProlineParser, \
    NbbParser, Komtek24, FoxKomputer, RtvEuro, Apollo

CHAT_ID_RTX3080 = "-1001442476457"

SAVED_RESULT_PATH = os.path.join(os.getenv("OUTPUT_FOLDER", default="outputs"), "outputs.json")
LINKS_ORIGIN_PATH = "links_3080.txt"
LINKS_LATER_PATH = os.path.join(os.getenv("OUTPUT_FOLDER", default="outputs"), "links_3080.txt")
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36'}

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)-15s %(levelname)-8s %(message)s")

counter = 0

PARSERS = [MediaExpertParser(), XKomParser(), SferisParser(), KomputronikParser(), MoreleParser(), ProlineParser(),
           NbbParser(), Komtek24(), FoxKomputer(), RtvEuro(), Apollo()]


def _is_supported(link):
    return bool([parser for parser in PARSERS if parser.is_this_page(link)])


def process_link(link, parser_for_link=None):
    if parser_for_link is None:
        parser_for_link = [parser for parser in PARSERS if parser.is_this_page(link)][0]
    try:
        page = requests.get(link, allow_redirects=True, headers=HEADERS)
        tree = html.fromstring(page.content)
        price = parser_for_link.parse(tree)
        return str(price) if price else None
    except:
        return None


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
    parsers_queue = _get_parsers_queue()

    with ThreadPoolExecutor(max_workers=len(parsers_queue)) as executor:
        parser_results = executor.map(_process_per_parser,
                                      zip(parsers_queue.items(), [next_request_seconds] * len(parsers_queue)))
        for parser_result in parser_results:
            result.update(parser_result)

    current_results.clear()
    current_results.update(result)

    _send_and_save_results_if_difference(current_results, previous_results)


def _process_per_parser(params) -> dict:
    result = dict()
    (parser, links), next_request_seconds = params
    for link in links:
        price = process_link(link, parser)
        logging.info(f"Fetched for {link} price {price}")
        if price:
            result[link] = price
        time.sleep(next_request_seconds)
    return result


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


def _get_parsers_queue():
    links = _get_links()

    parsers_queue = dict()
    for parser in PARSERS:
        parsers_queue[parser] = list()

    for link in links:
        found = False
        for parser, parser_links in parsers_queue.items():

            if parser.is_this_page(link):
                parsers_queue[parser].append(link)
                found = True

        if not found:
            logging.error(f"Not supported link: {link}")

    return parsers_queue


if __name__ == '__main__':
    logging.info("Starting program")
    previous = _read_saved_results()
    current = previous.copy()
    schedule.every(int(os.getenv("REFRESH_MINUTES", default=10))). \
        minutes.do(job, previous, current, int(os.getenv("NEXT_QUERY_SECONDS", default=15)))
    while True:
        schedule.run_pending()
        time.sleep(1)
