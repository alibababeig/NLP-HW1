import re
from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin


class KhabarFooriUrlHandler:
    def __init__(self):
        self._base_url = 'https://www.khabarfoori.com/%D8%A8%D8%AE%D8%B4-%D8%A7%D8%AE%D8%A8%D8%A7%D8%B1-2'
        self._url = self._base_url

    def __iter__(self):
        return self

    def __next__(self):
        cur_url = self._url
        res = re.search(r'\?page=([0-9]+)/?$', self._url)
        page_num = 1 if res is None else int(res.group(1))
        page_num += 1
        self._url = f'{self._base_url}?page={page_num}'
        return cur_url


class KhabarFooriCrawler:
    def __init__(self, lists_urls=None, n_workers=5):
        self._urls = lists_urls if lists_urls is not None else iter(
            KhabarFooriUrlHandler())
        self._n_workers = n_workers
        self._pool = ThreadPoolExecutor(n_workers)

    def get_latest_news(self, n_news):
        all_news_data = []
        news_urls = []
        while len(all_news_data) < n_news:
            # Scrape news urls from a news list and add them to `news_urls`
            while len(news_urls) < self._n_workers:
                news_list_url = next(self._urls)
                news_urls += self._scrape_news_urls(news_list_url)

            # Spawn workers to scrape news data
            results = self._pool.map(KhabarFooriCrawler._scrape_news_data,
                                     news_urls[:self._n_workers])

            # Remove used urls from `news_urls`
            news_urls = news_urls[self._n_workers:]

            # Wait for all workers to finish, by converting generator to list
            results = list(results)
            all_news_data += results

    @staticmethod
    def _scrape_news_urls(list_url):
        urls = []
        try:
            # Request the html page conatining news list
            res = requests.get(list_url)
            soup = BeautifulSoup(res.content, "html.parser")

            # Find the actual news list in the page
            ul = soup\
                .find(name='body')\
                .find(name='main')\
                .find(name='div', class_='main_wrapper pad8')\
                .find(name='div', class_='row_landing_inner container')\
                .find(name='div', class_='right_side container')\
                .find(name='div', class_='column_1')\
                .find(name='div', class_='container front_b mt20')\
                .find(name='ul', class_='box container')

            # Extract (relative) url for each of the news in the list
            relative_urls = [li.find(name='a', class_='res').get('href')
                             for li in ul.find_all('li')]

            # Convert relative urls to absolute urls
            urls = [urljoin('https://www.khabarfoori.com/', rel_url)
                    for rel_url in relative_urls]

        except Exception as e:
            print(f'ERROR! `{type(e).__name__}` in '
                  f'{KhabarFooriCrawler._scrape_news_urls.__name__}: '
                  f'`{str(e)}`')

        finally:
            return urls

    @staticmethod
    def _scrape_news_data(news_url):
        pass


def main():
    url_handler = iter(KhabarFooriUrlHandler())

    for _ in range(1):
        next(url_handler)
    list_url = next(url_handler)
    print(list_url)

    news_urls = KhabarFooriCrawler._scrape_news_urls(list_url)
    print(len(news_urls))
    print(news_urls)


if __name__ == '__main__':
    main()
