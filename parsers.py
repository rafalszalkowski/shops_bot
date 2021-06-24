import abc


def get_lines(tree, search):
    return [line for line in tree.text_content().split("\n") if search in line]


class PageParser(abc.ABC):

    def __init__(self, domain):
        self.domain = domain

    def is_this_page(self, link):
        return self.domain in link

    def __hash__(self):
        return hash(self.domain)

    def __eq__(self, other):
        return self.domain == other.domain

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
        return [line for line in price_lines[0].split(",") if "ecomm_pvalue:" in line][0][len(' ecomm_pvalue: \''):-2]


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


class Apollo(PageParser):
    def __init__(self):
        super().__init__("apollo.pl")

    def parse(self, tree):
        if "Niedostępny" in tree.text_content():
            return None

        elems = tree.xpath('//span[@class="js-cena"]/text()')
        return str(elems[0]).strip() if elems else None
