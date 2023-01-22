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

        self.result_found = False

    def find_path(self, start: str, finish: str) -> List[str]:
        start_time = time.time()

        # self.tree_cache = {1: {start: [second, third]}, 2: {second: [fourth, fifth], third: [sixth, seventh]}}
        self.tree_cache = {self.current_deepness: {None: [start]}}
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
                print(f'RESULT = {self.result_branch} TIME: {time.time() - start_time}')
                break
        else:
            print(f'NOT FOUND. LAST RESULT = {self.result_branch}')

        self.db.cursor.close()
        self.db.connection.close()
        # print(f'{links=}')
        # return links

    def get_parsed_links(self):

        if self.result_found:
            return

        for inner_deepness in range(self.current_deepness + 1):
            for page, links in self.tree_cache[inner_deepness].items():
                for link in links:
                    # print(f'{link=} ')

                    pages = self.get_links_from_db_or_parser(link)
                    # {1: {start: [second, third]}, 2: {second: [fourth, fifth], third: [sixth, seventh]}}
                    if not self.tree_cache.get(inner_deepness+1):
                        self.tree_cache[inner_deepness+1] = {}
                    self.tree_cache[inner_deepness+1][link] = pages

                    # print(f'TREE={self.tree_cache.get(self.current_deepness)}')
                    # print(f'-BRANCH={self.current_branch}')
                    # print(f'-TREE={self.tree_cache}')
                    # print(f'-PAGES={pages}\n')

                    # if not self.result_found:
                    #     for page_to_check in pages:
                    #         if page_to_check == self.finish_page_name:
                    #             print(f'FOUND {page_to_check}')
                    #
                    #             self.result_branch.append(self.finish_page_name)
                    #             for revers_deepness in range(inner_deepness+1, 0, -1):
                    #                 print(f'+++{revers_deepness=} {page_to_check=}')
                    #                 for backward_page, backward_links in self.tree_cache[revers_deepness].items():
                    #                     if page_to_check in backward_links:
                    #                         page_to_check = backward_page
                    #                         self.result_branch.append(page_to_check)
                    #             self.result_branch.reverse()
                    #             self.result_found = True
                    #             break

                    if link == self.finish_page_name:
                        self.result_branch.append(self.finish_page_name)
                        page_to_check = link
                        for revers_deepness in range(inner_deepness, 0, -1):
                            # print(f'+++{revers_deepness=} {page_to_check=}')
                            for backward_page, backward_links in self.tree_cache[revers_deepness].items():
                                if page_to_check in backward_links:
                                    page_to_check = backward_page
                                    self.result_branch.append(page_to_check)
                        self.result_branch.reverse()
                        self.result_found = True
                        break

                if self.result_found:
                    break

            if self.result_found:
                break
        return

    def get_links_from_db_or_parser(self, current_page):
        cached_id = self.db.get_page_id_if_cached(self.table_name, current_page)
        if cached_id:
            pages = self.db.get_related_pages(self.table_name, cached_id)
            print(f'{self.current_deepness}-DBS: ', end='')
        else:
            current_uri = f'{self.uri_to_parse}{current_page}'
            pages = self.scrapper.scrap_for_linked_pages(
                url=f'{self.site_to_parse}{current_uri}',
                href_mask=self.href_mask,
                limit=links_per_page)

            self.db.cache_pages_relations(self.table_name, current_page, pages)
            print(f'{self.current_deepness}-URL: ', end='')
        return pages


if __name__ == '__main__':
    game = WikiRacer()
    game.find_path('Дружба', 'Рим')
    # game.find_path('Дружба', 'Столиця')
    # game.find_path('Дружба', 'Федеральний округ')
    # game.find_path('Географія Бутану', 'Федеральний округ')
