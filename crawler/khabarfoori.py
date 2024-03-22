import json
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
        all_news_data = {}
        try:
            news_urls = []
            while len(all_news_data) < n_news:
                cur_needed_news = min(
                    self._n_workers, n_news - len(all_news_data))
                # Scrape news urls from a news list and add them to `news_urls`
                while len(news_urls) < cur_needed_news:
                    news_list_url = next(self._urls)
                    news_urls += self._scrape_news_urls(news_list_url)

                # Spawn workers to scrape news data
                results = self._pool.map(KhabarFooriCrawler._scrape_news_data,
                                         news_urls[:cur_needed_news])

                # Remove used urls from `news_urls`
                news_urls = news_urls[cur_needed_news:]

                # Wait for all workers to finish, by converting generator to list
                results = list(results)
                for res in results:
                    if res is not None:
                        news_id, news_data = res
                        all_news_data[news_id] = news_data

                print(f'Number of scraped news = {len(all_news_data)}')

        except KeyboardInterrupt:
            print('User interrupt received. Terminating the process...')

        finally:
            return all_news_data

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

            print(f'Successfully got news urls from `{list_url}`')

        except Exception as e:
            print(f'ERROR! `{type(e).__name__}` in '
                  f'{KhabarFooriCrawler._scrape_news_urls.__name__}: '
                  f'`{str(e)}`')

        finally:
            return urls

    @staticmethod
    def _scrape_news_data(news_url):
        try:
            # Request the html page conatining news data
            res = requests.get(news_url)
            soup = BeautifulSoup(res.content, "html.parser")

            # Extract important parts of the news from the page
            article = soup\
                .find(name='body')\
                .find(name='main')\
                .find(name='div', class_='main_wrapper pad8')\
                .find(name='div', class_='row_landing_inner container')\
                .find(name='div', class_='right_side container')\
                .find(name='div', class_='column_1')\
                .find(name='article', class_='news_page_article container')

            header = article\
                .find(name='header', class_='article_header mt20 box container')

            news_categories = header\
                .find(name='div', class_='breadcrumb_cnt')\
                .find(name='ul', class_='bread_crump')\
                .find_all(name='li')[1:]
            news_categories = [li.find(name='span', class_='').text.strip()
                               for li in news_categories]

            news_datetime = header\
                .find(name='div', class_='breadcrumb_cnt')\
                .find(name='time').get('datetime')

            news_title = header\
                .find(name='h1', class_='title')\
                .text.strip()

            news_lead = header\
                .find(name='p', class_='lead')\
                .text.strip()

            news_id = article\
                .find(name='div', class_='article_content mt20 box container')\
                .find(name='div', class_='print_cnt')\
                .find(name='div', class_='noprint print_icon')\
                .find(name='span', class_='news_id')\
                .find_all(string=True, recursive=False)
            news_id = int(''.join(news_id).strip())

            news_text = article\
                .find(name='div', class_='article_content mt20 box container')\
                .find(name='div', id='main_ck_editor')\
                .text.strip()

            news_tags = article\
                .find(name='div', class_='article_content mt20 box container')\
                .find(name='div', class_='news_tags noprint container')\
                .find_all(name='a')
            news_tags = [a.text.strip() for a in news_tags]

            # print(f'Successfully scraped news data from `{news_url}`')

            return news_id, {
                'title': news_title,
                'lead': news_lead,
                'text': news_text,
                'tags': news_tags,
                'category': news_categories,
                'datetime': news_datetime,
                'url': news_url,
            }

        except Exception as e:
            print(f'ERROR! `{type(e).__name__}` in '
                  f'{KhabarFooriCrawler._scrape_news_data.__name__}: '
                  f'`{str(e)}`')
            return None, None


def main():
    crawler = KhabarFooriCrawler(n_workers=50)
    news = crawler.get_latest_news(n_news=750)
    with open('./news.json', 'w') as f:
        json.dump(news, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main()
