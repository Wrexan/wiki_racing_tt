from bs4 import BeautifulSoup
from re import Pattern


def scrap_for_linked_pages(soup: BeautifulSoup,
                           href_mask: Pattern,
                           limit: int) -> list:
    links = {}
    raw_links = soup.find('body') \
        .find('div', id='bodyContent') \
        .find('div', id='mw-content-text') \
        .find_all('a', href=href_mask, class_=None, limit=limit)

    for link in raw_links:
        links[link.get('title')] = (link.get('href'))
    print(links)
    return links
