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
                               limit: int) -> tuple:
        self.make_delay_before_next_request()
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = []
        raw_links = soup.find('body') \
            .find('div', id='bodyContent') \
            .find('div', class_='mw-parser-output') \
            .find_all('a', href=href_mask, class_=None, limit=limit)

        for link in raw_links:
            links.append((link.get('title'),))
            # links.append((link.get('title'), unquote(link.get('href'))))
        return *links,

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
