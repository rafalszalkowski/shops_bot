import os

import schedule
import time
from lxml import html
import requests
import json
import telegram_sender

CHAT_ID = "-1001353392493"

SAVED_RESULT_PATH = os.path.join(os.getenv("OUTPUT_FOLDER"), "outputs.json")
LINKS_ORIGIN_PATH = "links.txt"
LINKS_LATER_PATH = os.path.join(os.getenv("OUTPUT_FOLDER"), "links.txt")
counter = 0
SUPPORTED = {"www.mediaexpert.pl", "www.x-kom.pl"}


def _media_expert_parse(tree):
    elems = tree.xpath('//div[@data-label="Cena regularna"]//span[@class="a-price_price"]/text()')
    return elems[0] if elems else None


def _xkom_parse(tree):
    pass  # TODO


def _is_supported(link):
    return bool({link.split("/")[2]} & SUPPORTED)


def process_link(link):
    page = requests.get(link, allow_redirects=True)
    tree = html.fromstring(page.content)
    return _media_expert_parse(tree)


def _save_result(current_results):
    json_object = json.dumps(current_results, indent=4)
    with open(SAVED_RESULT_PATH, "w") as outfile:
        outfile.write(json_object)


def _send_alert(current_results: dict):
    message = "\n".join([k.split("/")[-1] + " Cena:" + v for (k, v) in current_results.items()])
    telegram_sender.send(CHAT_ID, message)  # TODO


def job(previous_results, current_results):
    print("I'm working in loop:", counter)
    result = dict()
    links = _get_links()
    for link in links:
        if _is_supported(link):
            price = process_link(link)
            if price:
                result[link] = price
        else:
            print(f"Link not supported:{link}")
        time.sleep(1)

    _send_and_save_results_if_difference(current_results, previous_results)


def _send_and_save_results_if_difference(current_results, previous_results):
    if previous_results != current_results:
        _save_result(current_results)
        previous_results.clear()
        previous_results.update(current_results)
        _send_alert(current_results)


def _get_links():
    links_path = LINKS_LATER_PATH if os.path.isfile(LINKS_LATER_PATH) else LINKS_ORIGIN_PATH
    with open(links_path, "r") as links_f:
        return links_f.readlines()


def _read_saved_results():
    if os.path.isfile(SAVED_RESULT_PATH):
        return dict()

    with open(SAVED_RESULT_PATH, "r") as f:
        return json.load(f)


if __name__ == '__main__':
    print("Starting program")
    previous = _read_saved_results()
    current = previous.copy()
    schedule.every(int(os.getenv("REFRESH_MINUTES"))).minutes.do(job, previous, current)
    while True:
        schedule.run_pending()
        time.sleep(1)
