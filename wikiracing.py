import re
import time
from typing import List

import psycopg2
import requests
from bs4 import BeautifulSoup

from utils.db_controller import create_page_names_table, create_page_relations_table
from utils.scrapper import scrap_for_linked_pages

requests_per_minute = 100
links_per_page = 20


class WikiRacer:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.connection: psycopg2.connection
        self.cursor: psycopg2.cursor
        self.delay_between_requests: float = 1 / (requests_per_minute / 60)
        self.last_request_time: float = time.time()
        self.site_to_parse = 'https://uk.wikipedia.org'
        self.uri_to_parse = '/wiki/'
        self.href_mask = re.compile(rf'{self.uri_to_parse}*')

    def find_path(self, start: str, finish: str) -> List[str]:

        # self.connection = self.create_connection()
        # if not self.connection:
        #     return []
        # self.cursor = self.connection.cursor()
        # create_page_names_table(conn_source=self, table_name='pages')
        # create_page_relations_table(conn_source=self, page_table_name='pages')

        links: list = self.get_parsed_links(current_page_name=start, finish_page_name=finish)
        # links: list = []
        # for link_number in range(links_per_page):
        #     links.append(self.get_parsed_links(start=start, finish=finish))
        # self.cursor.close()
        # self.connection.close()
        # print(f'{links=}')
        # return links

    @staticmethod
    def create_connection():
        connection = None
        try:
            connection = psycopg2.connect(
                host="localhost",
                database="cash_db",
                user="postgres",
                port=5433,
                password="123")
        except Exception as err:
            print(f'Error: {err}')
        return connection

    def get_parsed_links(self, current_page_name: str, finish_page_name: str) -> list:
        self.make_delay_before_next_request()
        r = requests.get(f'{self.site_to_parse}{self.uri_to_parse}{current_page_name}')
        soup = BeautifulSoup(r.text, 'html.parser')
        links = scrap_for_linked_pages(soup=soup,
                                       href_mask=self.href_mask,
                                       limit=links_per_page)

        for link in links:

        #     found = self.get_parsed_links(page_name, finish_page_name)
        #     if found:
        #         print('FOUND')
        # if title.lower() == finish_page_name.lower():
        #     print('FOUND')
        # return [current_page_name, title]

        return links

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


if __name__ == '__main__':
    game = WikiRacer()
    game.find_path('Дружба', 'Рим')
