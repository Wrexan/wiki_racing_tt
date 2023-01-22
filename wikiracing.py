import re
from typing import List
from utils.db_controller import DBController
from utils.scrapper import Scrapper

requests_per_minute = 100
links_per_page = 20


class WikiRacer:
    def __init__(self):
        self.site_to_parse = 'https://uk.wikipedia.org'
        self.uri_to_parse = '/wiki/'
        # self.ignored_title_mask = (re.compile(r'^Спеціальна:*'), re.compile(r'^Вікіпедія:*'))
        self.href_mask = re.compile(rf'^{self.uri_to_parse}*')
        self.table_name = 'pages'
        self.db = DBController()
        self.scrapper = Scrapper(requests_per_minute=requests_per_minute)
        self.current_branch: list = []
        self.current_deepness = 0
        self.max_deepness = 3
        self.finish_page_name: str = ''
        self.tree_cache: {int: list} = {}

        self.SEARCH = 0
        self.RESULT_FOUNDED = 1
        self.FINISHED = 2
        self.status = self.SEARCH

    def find_path(self, start: str, finish: str) -> List[str]:
        self.current_branch.append(start)
        self.tree_cache[self.current_deepness] = [(start,)]
        # self.current_deepness = 2
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
            self.get_parsed_links(page=(start,))

        if self.status == self.RESULT_FOUNDED:
            print(f'FOUND RESULT = {self.current_branch}')
        else:
            print(f'NOT FOUND. LAST RESULT = {self.current_branch}')

        self.db.cursor.close()
        self.db.connection.close()
        # print(f'{links=}')
        # return links

    def get_parsed_links(self, page: tuple, in_cycle: bool = False):

        if self.status == self.FINISHED:
            return

        self.current_branch[-1] = page[0]

        # getting current page from branch
        pages = self.get_pages(current_page_name=page[0])
        # print(f'{pages=}')

        overstep = 1 if not in_cycle else 2
        if not self.tree_cache.get(self.current_deepness+overstep):
            print(f'extending')
            self.tree_cache[self.current_deepness+overstep] = []
        self.tree_cache[self.current_deepness+overstep].extend(pages)

        # print(f'TREE={self.tree_cache.get(self.current_deepness)}')
        print(f'-BRANCH={self.current_branch}')
        print(f'-TREE={self.tree_cache}')
        # print(f'-PAGES={pages}\n')

        for page_to_check in pages:
            if page_to_check == self.finish_page_name:
                print(f'FOUND {page_to_check=}')
                print(f'{self.current_branch},{self.finish_page_name}')
                self.current_branch.append(self.finish_page_name)
                self.status = self.RESULT_FOUNDED

        # returning only after full page scan
        if self.status == self.RESULT_FOUNDED:
            self.status = self.FINISHED
            return

        if not in_cycle:
            self.current_branch.append(None)
            # print(f'{self.tree_cache[self.current_deepness]=}')
            for next_page in self.tree_cache[self.current_deepness+1]:
                print(f'{next_page=}')
                self.get_parsed_links(page=next_page, in_cycle=True)

        # if self.current_deepness > self.max_deepness:
        #     self.status = self.FINISHED
        #     return

        # self.current_deepness += 1


        # print(f'-ALL={self.tree_cache}\n')
        # for next_page in self.tree_cache[self.current_deepness-1]:
        #     self.get_parsed_links(page=next_page, go_deeper=True)

        # if not self.dependencies_tree_cache.get(self.current_deepness):
        #     print(f'extending')
        #     self.dependencies_tree_cache[self.current_deepness] = []
        # self.dependencies_tree_cache[self.current_deepness].extend(pages)

        # if go_deeper:
        #     print(f'{"=" * self.current_deepness}> going deeper')
        #     self.current_branch.append(None)
        #
        #     self.current_deepness += 1
        #     for link in pages:
        #         self.current_branch[-1] = link[0]
        #         pages = pages or self.get_pages(current_page_name=self.current_branch[-1])
        #         self.get_parsed_links(pages=pages, go_deeper=False)
        #
        #     if self.current_deepness > self.max_deepness:
        #         self.status = self.FINISHED
        #         return

            # self.dependencies_tree_cache[self.current_deepness] = []
            #
            # self.current_pages_branch.append(None)
            #
            # print(f'{self.dependencies_tree_cache=}')
            # for branch in self.dependencies_tree_cache[self.current_deepness - 1]:
            #     print(f'{branch[0]=}')
            #     self.current_pages_branch[-1] = branch[0]
            #     self.get_parsed_links(go_deeper=True)
        return

    def get_pages(self, current_page_name):
        cached_id = self.db.get_page_id_if_cached(self.table_name, current_page_name)
        if cached_id:
            pages = self.db.get_related_pages(self.table_name, cached_id)
            print(f'{self.current_deepness}-DBS: ', end='')
        else:
            current_uri = f'{self.uri_to_parse}{current_page_name}'
            pages = self.scrapper.scrap_for_linked_pages(
                url=f'{self.site_to_parse}{current_uri}',
                href_mask=self.href_mask,
                limit=links_per_page)

            self.db.cache_pages_relations(self.table_name, (current_page_name,), pages)
            print(f'{self.current_deepness}-URL: ', end='')
        return pages

    # def get_parsed_links2(self, go_deeper: bool = True):
    #     if self.status == self.FINISHED:
    #         return
    #     # getting current page from branch
    #     current_page_name = self.current_pages_branch[-1]
    #     current_uri = f'{self.uri_to_parse}{current_page_name}'
    #
    #     cached_id = self.db.get_page_id_if_cached(self.table_name, current_page_name)
    #     if cached_id:
    #         pages = self.db.get_related_pages(self.table_name, cached_id)
    #         print('DBS: ', end='')
    #     else:
    #         pages = self.scrapper.scrap_for_linked_pages(
    #             url=f'{self.site_to_parse}{current_uri}',
    #             href_mask=self.href_mask,
    #             limit=links_per_page)
    #
    #         self.db.cache_pages_relations(self.table_name, (current_page_name,), pages)
    #         print('URL: ', end='')
    #
    #     print(f'{self.current_pages_branch=}')
    #     # print(f'{pages=}')
    #
    #     for page in pages:
    #         if page == self.finish_page_name:
    #             print(f'FOUND {page=}')
    #             print(f'{self.current_pages_branch},{self.finish_page_name}')
    #             self.current_pages_branch.append(self.finish_page_name)
    #             self.status = self.RESULT_FOUNDED
    #
    #     # returning only after full page scan
    #     if self.status == self.RESULT_FOUNDED:
    #         self.status = self.FINISHED
    #         return
    #
    #     if go_deeper:
    #         print(f'{"=" * self.current_deepness}> going deeper')
    #         self.current_pages_branch.append(None)
    #         for link in pages:
    #             self.current_pages_branch[-1] = link[0]
    #             self.get_parsed_links(go_deeper=False)
    #
    #         if self.current_deepness <= self.max_deepness:
    #             self.current_deepness += 1
    #             self.dependencies_tree_cache[self.current_deepness] = pages
    #
    #             print(f'{self.dependencies_tree_cache=}')
    #             for branch in self.dependencies_tree_cache[self.current_deepness]:
    #                 print(f'{branch[0]=}')
    #                 self.current_pages_branch[-1] = branch[0]
    #                 self.current_pages_branch.append(None)
    #                 self.get_parsed_links(go_deeper=False)
    #
    #             self.get_parsed_links(go_deeper=True)
    #
    #     return


if __name__ == '__main__':
    game = WikiRacer()
    game.find_path('Дружба', 'Рим')
