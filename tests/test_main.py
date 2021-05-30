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
        "https://www.morele.net/karta-graficzna-msi-geforce-gtx-1650-d6-ventus-xs-oc-v2-4gb-gddr6"
        "-gtx-1650-d6-ventus-xs-ocv2-5945480/")
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
