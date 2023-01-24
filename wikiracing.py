import re
import time
from typing import List
from utils.db_controller import DBController
from utils.scrapper import Scrapper

requests_per_minute = 100
links_per_page = 200


class WikiRacer:
    def __init__(self):
        self.site_to_parse = 'https://uk.wikipedia.org'
        self.uri_to_parse = '/wiki/'
        self.href_mask = re.compile(rf'^{self.uri_to_parse}*')
        self.table_name = 'pages'
        self.db = DBController()
        self.scrapper = Scrapper(requests_per_minute=requests_per_minute)
        self.result_branch: list = []
        self.current_deepness = 0
        self.max_deepness = 5
        self.finish_page_name: str = ''
        self.tree_cache: dict[int: dict[str: list[str, ...]]] = {}
        self.sources = {0: 'DB-', 1: 'WB-'}
        self.current_source = 1
        self.page_counter = 0
        self.start_time = 0

        self.result_found = False

    def find_path(self, start: str, finish: str) -> List[str]:
        self.start_time = time.time()

        # self.tree_cache = {1: {start: [second, third]}, 2: {second: [fourth, fifth], third: [sixth, seventh]}}
        self.tree_cache = {self.current_deepness: {None: [(1, start)]}}
        self.finish_page_name = finish

        self.db.create_connection(
            host="localhost",
            database="cash_db",
            user="postgres",
            port=5433,
            password="123")
        if not self.db.connection:
            return []

        self.db.create_page_names_table(table_name=self.table_name)
        self.db.create_m2m_relations_table(table_name=self.table_name)

        for step in range(self.max_deepness):
            self.current_deepness = step
            self.get_parsed_links()

            if self.result_found:
                print(f'RESULT: {self.result_branch} TIME: {round(time.time() - self.start_time, 2)}')
                break
        else:
            print(f'NOT FOUND. LAST RESULT = {self.result_branch}')

        self.db.cursor.close()
        self.db.connection.close()
        # return links

    def get_parsed_links(self):

        if self.result_found:
            return
        for inner_deepness in range(self.current_deepness + 1):
            print(f'{self.tree_cache=}')
            print(f'{inner_deepness=}')
            for page, links in self.tree_cache[inner_deepness].items():
                for link in links:
                    self.page_counter += 1
                    print(f"\r{self.sources[self.current_source]}"
                          f"{self.current_deepness}-Parsed: "
                          f"{self.page_counter}", end="")
                    print(f'{link=} ')

                    pages = self.get_links_from_db_or_parser(link)
                    # {1: {start: [second, third]}, 2: {second: [fourth, fifth], third: [sixth, seventh]}}
                    if not self.tree_cache.get(inner_deepness+1):
                        self.tree_cache[inner_deepness+1] = {}
                    self.tree_cache[inner_deepness+1][link] = pages

                    # do the link is finish?
                    if link[1] == self.finish_page_name:
                        self.result_branch.append(self.finish_page_name)
                        page_to_check = link
                        for revers_deepness in range(inner_deepness, 0, -1):
                            # print(f'+++{revers_deepness=} {page_to_check=}')
                            for backward_page, backward_links in self.tree_cache[revers_deepness].items():
                                if page_to_check in backward_links:
                                    page_to_check = backward_page
                                    self.result_branch.append(page_to_check[1])
                        self.result_branch.reverse()
                        self.result_found = True
                        print('')
                        return

    def get_links_from_db_or_parser(self, current_page):
        # cached = self.db.is_link_cashed(self.table_name, current_page[0])
        # cached_id = self.db.get_page(self.table_name, current_page[1])
        cached_id: tuple = self.db.get_link_if_cached(self.table_name, current_page[1])
        if cached_id:
            # print(f'{cached_id=} {current_page=}')
            pages = self.db.get_related_pages(self.table_name, cached_id[0])
            self.current_source = 0
        else:
            current_uri = f'{self.uri_to_parse}{current_page[1]}'
            pages = self.scrapper.scrap_for_linked_pages(
                url=f'{self.site_to_parse}{current_uri}',
                href_mask=self.href_mask,
                limit=links_per_page)

            if pages:
                self.db.cache_pages_relations(self.table_name, current_page[1], pages)
            self.current_source = 1
        return pages


if __name__ == '__main__':
    game = WikiRacer()
    game.find_path('Дружба', 'Рим')
    # game.find_path('Мітохондріальна ДНК', 'Вітамін K')
    # game.find_path('Марка (грошова одиниця)', 'Китайський календар')
    # game.find_path('Фестиваль', 'Пілястра')
    # game.find_path('Дружина (військо)', '6 жовтня')
    # game.find_path('Географія Бутану', 'Федеральний округ')

    # game.find_path('Дружба', 'Столиця')
    # game.find_path('Бактерії', 'Китайський календар')
