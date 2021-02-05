import os

import requests

URL = "https://api.telegram.org/bot"


def send(chat_id, message):
    token = os.getenv("TELEGRAM_TOKEN")
    url_req = f"{URL}{token}/sendMessage"
    r = requests.post(url_req, data={'chat_id': chat_id, "text": message})
    print("Post text:", r.text)
