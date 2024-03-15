import re
from concurrent.futures import ThreadPoolExecutor


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
        pass

    @staticmethod
    def _scrape_news_data(news_url):
        pass


def main():
    pass


if __name__ == '__main__':
    main()
