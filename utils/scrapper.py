import time

import requests
from bs4 import BeautifulSoup
from re import Pattern


class Scrapper:
    def __init__(self, requests_per_minute: int = 60):
        self.delay_between_requests: float = 1 / (requests_per_minute / 60)
        self.last_request_time: float = time.time()

    def scrap_for_linked_pages(self,
                               url: str,
                               href_mask: Pattern,
                               limit: int) -> list | None:
        self.make_delay_before_next_request()
        r = requests.get(url)
        if r.status_code != 200:
            print(f'Connection error for {url}: {r.status_code=}')
            return

        soup = BeautifulSoup(r.text, 'html.parser')
        links = []

        raw_html = soup.body.find('div', id='bodyContent')
        if not raw_html:
            return

        raw_html = raw_html.find('div', class_='mw-parser-output')
        if not raw_html:
            return

        raw_links = raw_html.find_all('a', href=href_mask, class_=None, limit=limit)
        if not raw_links:
            return

        for link in raw_links:
            link_title = link.get('title')
            link_href = link.get('href')
            if link_title and ':' not in link_href:
                links.append(link_title)
        return links

    def make_delay_before_next_request(self) -> None:
        # current time
        current_time = time.time()
        # calculate time left until next allowed request
        delay = self.last_request_time + self.delay_between_requests - current_time
        # make delay for the time left until next allowed request
        if delay > 0:
            time.sleep(delay)
        else:
            print(f' LAG: {round(delay, 2)} sec', end="")
            delay = 0

        # updating time of the next request
        self.last_request_time = current_time + delay
