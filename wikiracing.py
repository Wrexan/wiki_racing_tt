import re
import time
from typing import List

import psycopg2
import requests
from bs4 import BeautifulSoup

requests_per_minute = 100
links_per_page = 200


class WikiRacer:
    def __init__(self):
        self.delay_between_requests: float = 1 / (requests_per_minute / 60)
        self.last_request_time: float = time.time()
        self.site_to_parse = 'https://uk.wikipedia.org'
        self.uri_to_parse = '/wiki/'
        self.approved_href = re.compile(r'/wiki/*')
        self.conn = None
        try:
            self.conn = psycopg2.connect(
                host="localhost",
                database="cash_db",
                user="postgres",
                port=5433,
                password="123")
        except psycopg2.OperationalError as err:
            print(f'{err=}')
        self.cur = self.conn.cursor()
        self.cur.execute('SELECT version()')
        db_version = self.cur.fetchone()
        print(db_version)
        print(f'{self.conn=}')

    def find_path(self, start: str, finish: str) -> List[str]:
        links: list = self.get_parsed_links(current_page_name=start, finish_page_name=finish)
        # links: list = []
        # for link_number in range(links_per_page):
        #     links.append(self.get_parsed_links(start=start, finish=finish))
        print(f'{links=}')
        return links

    def get_parsed_links(self, current_page_name: str, finish_page_name: str) -> list:
        self.make_delay_before_next_request()
        r = requests.get(f'{self.site_to_parse}{self.uri_to_parse}{current_page_name}')
        soup = BeautifulSoup(r.text, 'html.parser')

        page_names = self.scrap_page_for_linked_page_names(soup=soup,
                                                           current_page_name=current_page_name,
                                                           finish_page_name=finish_page_name)

        for page_name in page_names:
            found = self.get_parsed_links(page_name, finish_page_name)
            if found:
                ...

        return page_names

    def scrap_page_for_linked_page_names(self,
                                         soup: BeautifulSoup,
                                         current_page_name: str,
                                         finish_page_name: str) -> list:
        page_names = []
        links = soup.find('body') \
            .find('div', id='bodyContent') \
            .find('div', id='mw-content-text') \
            .find_all('a', href=self.approved_href, class_=None, limit=links_per_page)

        for link in links:
            title: str = link.get('title')
            if title.lower() == finish_page_name.lower():
                print('FOUND')
                return [current_page_name, title]
            page_names.append(link.get('title'))
            # print(link.get('title'))
        return page_names

    def make_delay_before_next_request(self) -> None:
        # current time
        current_time = time.time()
        # calculate time left until next allowed request
        delay = self.last_request_time + self.delay_between_requests - current_time
        # updating time of the next request
        self.last_request_time = current_time + delay
        # make delay for the time left until next allowed request
        if delay > 0:
            # print(f'{delay=}')
            time.sleep(delay)


if __name__ == '__main__':
    game = WikiRacer()
    # game.find_path('Дружба', 'Рим')
