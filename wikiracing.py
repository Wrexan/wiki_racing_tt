import re
import time
from typing import List
from utils.db_controller import DBController
from utils.scrapper import Scrapper

requests_per_minute = 100
links_per_page = 200


class WikiRacer:
    def __init__(self):
        self.connection_params = {"host": "localhost",
                                  "database": "cash_db",
                                  "user": "postgres",
                                  "port": 5433,
                                  "password": "123"}
        self.site_to_parse = 'https://uk.wikipedia.org'
        self.uri_to_parse = '/wiki/'
        self.href_mask = re.compile(rf'^{self.uri_to_parse}*')
        self.table_name = 'pages'
        self.db = DBController(connection_params=self.connection_params)
        self.scrapper = Scrapper(requests_per_minute=requests_per_minute)
        self.max_deepness = 5
        self.finish_page_name: str = ''
        self.tree_cache: dict[int: dict[str: list[str, ...]]] = {}
        self.path_cache: dict[int: str] = {}
        self.sources = {0: 'DB', 1: 'WB'}
        self.current_source = 1

        self.current_deepness = 0
        self.page_counter = 0
        self.start_time = 0
        self.result_found = False

    def find_path(self, start: str, finish: str) -> List[str]:
        self.page_counter = 0
        self.path_cache = {}
        self.result_found = False
        self.start_time = time.time()

        # self.tree_cache = {1: {start: [second, third]}, 2: {second: [fourth, fifth], third: [sixth, seventh]}}
        self.tree_cache = {0: {None: [(1, start)]}}
        self.finish_page_name = finish

        self.db.create_connection()
        if not self.db.connection:
            return []

        self.db.create_page_names_table(table_name=self.table_name)
        self.db.create_m2m_relations_table(table_name=self.table_name)

        for step in range(self.max_deepness):
            self.current_deepness = step
            self.find_finish_path()

            if self.result_found:
                break
        result = list(self.path_cache.values())
        if self.result_found:
            print(f'RESULT: {result} TIME: {round(time.time() - self.start_time, 2)}')
        else:
            print(f'NOT FOUND. LAST RESULT = {result}')

        self.db.cursor.close()
        self.db.connection.close()
        return result

    def find_finish_path(self):

        if self.result_found:
            return
        for inner_deepness in range(self.current_deepness):
            for page, links in self.tree_cache[inner_deepness].items():
                if page:
                    self.path_cache[inner_deepness] = page[1]

                for link in links:
                    self.page_counter += 1
                    print(f"\r{self.sources[self.current_source]}"
                          f"{self.current_deepness}-Parsed: "
                          f"{self.page_counter}", end="")

                    links_on_page = self.get_links_from_db_or_parser(link)
                    if not links_on_page:
                        continue

                    # add branches to wide
                    if not self.tree_cache.get(inner_deepness + 1):
                        self.tree_cache[inner_deepness + 1] = {}
                    self.tree_cache[inner_deepness + 1][link] = links_on_page

                    # do the link is finish?
                    for next_link in links_on_page:
                        if next_link[1] == self.finish_page_name:
                            self.path_cache[inner_deepness+1] = link[1]
                            self.path_cache[inner_deepness+2] = self.finish_page_name
                            self.result_found = True
                            print('')
                            return

    def get_links_from_db_or_parser(self, current_page_title):
        links_of_cached_title: list = self.db.get_title_links_if_cached(self.table_name, current_page_title[1])

        if links_of_cached_title:
            self.current_source = 0
            return links_of_cached_title

        current_uri = f'{self.uri_to_parse}{current_page_title[1]}'
        pages = self.scrapper.scrap_for_linked_pages(
            url=f'{self.site_to_parse}{current_uri}',
            href_mask=self.href_mask,
            limit=links_per_page)
        if pages:
            cached_id = self.db.cache_pages_relations(self.table_name, current_page_title[1], pages)
            self.current_source = 1
            return self.db.get_title_links(self.table_name, cached_id)


if __name__ == '__main__':
    game = WikiRacer()
    game.find_path('Дружба', 'Рим')
    game.find_path('Мітохондріальна ДНК', 'Вітамін K')
    game.find_path('Марка (грошова одиниця)', 'Китайський календар')
    game.find_path('Фестиваль', 'Пілястра')
    game.find_path('Дружина (військо)', '6 жовтня')

    print('\n')
    print(f'Most popular: {game.db.get_most_popular_titles(game.table_name, amount=5)}')
    print(f'Most recursive: {game.db.get_titles_with_most_links(game.table_name, amount=5)}')
    title = "Дружба"
    print(f'Average 2ng deep links for "{title}": '
          f'{game.db.get_average_link_number_for_deep_2(game.table_name, title=title)[0]}')
