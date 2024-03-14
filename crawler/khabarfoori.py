import re


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


def main():
    pass


if __name__ == '__main__':
    main()
