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

SAVED_RESULT_PATH = os.path.join(os.getenv("OUTPUT_FOLDER"), "outputs.json")
LINKS_ORIGIN_PATH = "links.txt"
LINKS_LATER_PATH = os.path.join(os.getenv("OUTPUT_FOLDER"), "links.txt")
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36'}
SUPPORTED = {"www.mediaexpert.pl", "www.x-kom.pl"}

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)-15s %(levelname)-8s %(message)s")

counter = 0


def _media_expert_parse(tree):
    elems = tree.xpath('//div[@data-label="Cena regularna"]//span[@class="a-price_price"]/text()')
    return elems[0] if elems else None


def _xkom_parse(tree):
    if tree.xpath('//text()="Powiadom o dostępności"'):
        return None
    elems = tree.xpath('//div[@class="u7xnnm-4 iVazGO"]/text()')
    return elems[0] if elems else None


def _is_supported(link):
    return bool({link.split("/")[2]} & SUPPORTED)


def process_link(link):
    page = requests.get(link, allow_redirects=True, headers=HEADERS)
    tree = html.fromstring(page.content)
    return _media_expert_parse(tree) if "mediaexpert.pl" in link else _xkom_parse(tree)


def _save_result(current_results):
    json_object = json.dumps(current_results, indent=4)
    with open(SAVED_RESULT_PATH, "w") as outfile:
        outfile.write(json_object)


def _send_alert(current_results: dict):
    message = "\n".join([k + " Cena:" + v for (k, v) in current_results.items()])
    telegram_sender.send(CHAT_ID, message)


def job(previous_results, current_results):
    global counter
    logging.info(f"I'm working in loop: {counter}")
    counter += 1
    result = dict()
    links = _get_links()
    for link in links:
        if _is_supported(link):
            price = process_link(link)
            logging.info(f"Fetched for {link} price {price}")
            if price:
                result[link] = price
        else:
            logging.info(f"Link not supported:{link}")
        time.sleep(3)

    current_results.clear()
    current_results.update(result)

    _send_and_save_results_if_difference(current_results, previous_results)


def _send_and_save_results_if_difference(current_results, previous_results):
    if previous_results != current_results:
        previous_results.clear()
        previous_results.update(current_results)
        if current_results:
            _send_alert(current_results)
        _save_result(current_results)
    elif not os.path.isfile(SAVED_RESULT_PATH):
        _save_result(current_results)


def _get_links():
    links_path = LINKS_LATER_PATH if os.path.isfile(LINKS_LATER_PATH) else LINKS_ORIGIN_PATH
    if not os.path.isfile(LINKS_LATER_PATH):
        copyfile(LINKS_ORIGIN_PATH, LINKS_LATER_PATH)

    with open(links_path, "r") as links_f:
        return links_f.read().splitlines()


def _read_saved_results():
    if not os.path.isfile(SAVED_RESULT_PATH):
        return dict()

    with open(SAVED_RESULT_PATH, "r") as f:
        return json.load(f)


if __name__ == '__main__':
    logging.info("Starting program")
    previous = _read_saved_results()
    current = previous.copy()
    schedule.every(int(os.getenv("REFRESH_MINUTES"))).minutes.do(job, previous, current)
    while True:
        schedule.run_pending()
        time.sleep(1)
