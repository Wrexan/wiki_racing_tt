import time

import requests
from bs4 import BeautifulSoup
from re import Pattern


class Scrapper:
    def __init__(self, requests_per_minute: int = 60):
        self.delay_between_requests: float = 1 / (requests_per_minute / 60)
        self.last_request_time: float = time.time()
        self.soup = None
        # self.page_dom_path = ('body',
        #                       ('div', {'id': 'bodyContent'}),
        #                       ('div', {'class': 'mw-parser-output'}))
        # self.dom_disassemble_template = self.parse_dom_template()

    def scrap_for_linked_pages(self,
                               url: str,
                               href_mask: Pattern,
                               limit: int) -> list:
        self.make_delay_before_next_request()
        r = requests.get(url)
        self.soup = BeautifulSoup(r.text, 'html.parser')
        links = []

        raw_html = self.soup.find('body')
        if not raw_html:
            # print(f'Scrapper error: URL have no body: {url}')
            return links

        raw_html = raw_html.find('div', id='bodyContent')
        if not raw_html:
            # print(f'Scrapper error: URL have no id="bodyContent": {url}')
            return links

        raw_html = raw_html.find('div', class_='mw-parser-output')
        if not raw_html:
            # print(f'Scrapper error: URL have no class_="mw-parser-output": {url}')
            return links

        raw_links = raw_html.find_all('a', href=href_mask, class_=None, limit=limit)
        if not raw_links:
            # print(f'Scrapper error: URL have no links: {url}')
            return links

        for link in raw_links:
            links.append(link.get('title'))
        return links

    # def disassemble_dom(self, url):
    #     ...
    #
    # def parse_dom_template(self, page_dom_path):
    #     dom_disassemble_template = []
    #     for page_elem in page_dom_path:
    #         if isinstance(page_elem, str):
    #             dom_disassemble_template.append(self.find_page_elem())
    #
    #     return
    #
    # def find_page_elem(self, name):
    #     return self.soup.find(name)

    def make_delay_before_next_request(self) -> None:
        # current time
        current_time = time.time()
        # calculate time left until next allowed request
        delay = self.last_request_time + self.delay_between_requests - current_time
        # updating time of the next request
        self.last_request_time = current_time + delay
        # make delay for the time left until next allowed request
        if delay > 0:
            time.sleep(delay)
        else:
            print(f'LAG: {-delay=} sec')
