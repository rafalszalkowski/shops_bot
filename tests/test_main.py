import pytest

from telegram_sender import send
from main import process_link


def test_media_empty():
    price = process_link(
        "https://www.mediaexpert.pl/komputery-i-tablety/podzespoly-komputerowe/karty-graficzne/"
        "karta-graficzna-pny-geforce-rtx-3080-epic-x-rgb-tf-xlr8-10gb-gaming-revel")
    assert price is None


def test_media_not_empty():
    price = process_link(
        "https://www.mediaexpert.pl/komputery-i-tablety/podzespoly-komputerowe/procesory/"
        "procesor-amd-ryzen-7-5800x-8-core-3-8ghz-am4-zen3")
    assert price is not None


def test_media_not_empty_correct_price():
    price = process_link(
        "https://www.mediaexpert.pl/komputery-i-tablety/podzespoly-komputerowe/"
        "karty-graficzne/karta-graficzna-msi-geforce-rtx-3080-ti-suprim-x-12gb")
    assert price is not None


def test_xkom_empty():
    price = process_link(
        "https://www.x-kom.pl/p/600904-karta-graficzna-nvidia-msi-geforce-rtx-3080-suprim-x-10gb-gddr6x.html")
    assert price is None


def test_xkom_not_empty():
    price = process_link(
        "https://www.x-kom.pl/p/592090-smartfon-telefon-apple-iphone-12-pro-128gb-graphite-5g.html")
    assert price is not None


def test_sferis_empty():
    price = process_link(
        "https://www.sferis.pl/karta-graficzna-gigabyte-gef-rtx-3080-vision-oc-10g-gv-n3080vision-oc-10gd-p684557")
    assert price is None


def test_sferis_not_empty():
    price = process_link(
        "https://www.sferis.pl/apple-macbook-air-2021-m1-8-core-cpu-7-core-gpu-133wqxga-retina-ips-8gb-ddr4-ssd256"
        "-tb3-alu-macos-big-sur-space-gray-mgn63ze-a-p697057")
    assert price is not None


def test_komputronik_empty():
    price = process_link(
        "https://www.komputronik.pl/product/704986/gigabyte-geforce-rtx-3080-aorus-xtreme-10g.html")
    assert price is None


def test_komputronik_not_empty():
    price = process_link("https://www.komputronik.pl/product/703590/apple-iphone-12-64gb-product-red.html")
    assert price is not None


def test_morele_empty():
    price = process_link(
        "https://www.morele.net/karta-graficzna-msi-geforce-rtx-3080-gaming-x-trio-10gb-gddr6x-rtx-3080"
        "-gaming-x-trio-10g-5943771/")
    assert price is None


def test_morele_not_empty():
    price = process_link(
        "https://www.morele.net/incore-sprezone-powietrze-do-usuwania-kurzu-600-ml-isc1280-274629/")
    assert price is not None


def test_proline_empty():
    price = process_link(
        "https://proline.pl/gigabyte-geforce-rtx-3080-aorus-xtreme-waterforce-wb"
        "-10gb-gddr6x-gv-n3080aorusx-wb-10gd-p8078249")
    assert price is None


def test_proline_not_empty():
    price = process_link(
        "https://proline.pl/gigabyte-geforce-rtx-3060-gaming-oc-12gb-gddr6-gv-n3060gaming-oc-12gd-p8077482")
    assert price is not None


def test_nbb_empty():
    price = process_link(
        "https://www.notebooksbilliger.de/nvidia+geforce+rtx+3080+founders+edition+714792")
    assert price is None


def test_nbbp_not_empty():
    price = process_link(
        "https://www.notebooksbilliger.de/hp+250+g7+15s88es+662188")
    assert price is not None


def test_nbbp_not_empty_without_promo():
    price = process_link(
        "https://www.notebooksbilliger.de/notebooks/acer+notebooks/acer+aspire+5+a515+44g+r8ab+651870")
    assert price is not None


def test_komtek24_not_empty():
    price = process_link(
        "https://komtek24.pl/karta-graficzna-asus-rtx-3080-rog-strix")
    assert price is not None


def test_komtek24_empty():
    price = process_link(
        "https://komtek24.pl/karta-graficzna-asus-rtx-3080-gaming-tuf-10gb-gddr6x")
    assert price is None


def test_foxkomputer_not_empty():
    price = process_link(
        "https://foxkomputer.pl/pl/p/Karta-graficzna-Gigabyte-RTX-3080-Ti-VISION-OC-12GB-GDDR6X/17103")
    assert price is not None


def test_foxkomputer_empty():
    price = process_link(
        "https://foxkomputer.pl/pl/p/Karta-graficzna-MSI-GeForce-RTX-3080-SUPRIM-X-10G-GDDR6X-OEM/15118")
    assert price is None


def test_euro_not_empty():
    price = process_link(
        "https://www.euro.com.pl/karty-graficzne/gigabyte-karta-gragiczna-gigabyte-rtx-3080-eagle.bhtml")
    assert price is not None


def test_euro_empty():
    price = process_link(
        "https://www.euro.com.pl/karty-graficzne/msi-karta-gragiczna-msi-rtx-3080-gaming-x-tr.bhtml")
    assert price is None


@pytest.mark.skip("Integration test")
def test_send_telegram():
    send("-1001442476457", "test")
