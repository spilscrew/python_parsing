"""
Источник: https://5ka.ru/special_offers/

Задача организовать сбор данных,
необходимо иметь метод сохранения данных в .json файлы

результат: Данные скачиваются с источника, при вызове метода/функции сохранения в файл скачанные данные сохраняются в
Json вайлы, для каждой категории товаров должен быть создан отдельный файл и содержать товары исключительно
соответсвующие данной категории.

пример структуры данных для файла:
нейминг ключей можно делать отличным от примера

{
"name": "имя категории",
"code": "Код соответсвующий категории (используется в запросах)",
"products": [{PRODUCT}, {PRODUCT}........] # список словарей товаров соответсвующих данной категории
}
"""

import time
import json
from pathlib import Path
import requests


class Parse5ka:
    def __init__(self, start_url: str, params: dict, result_path: Path, file_name: str,
                 template: dict,
                 data_insert_to: str):
        self.start_url = start_url
        self.result_path = result_path
        self.params = params
        self.template = template
        self.file_name = file_name
        self.data_insert_to = data_insert_to

    def _get_response(self, url, *args, **kwargs) -> requests.Response:
        while True:
            response = requests.get(url, *args, **kwargs)
            if response.status_code == 200:
                return response
            time.sleep(1)

    def run(self):
        self._save(self._parse(self.start_url))

    def _parse(self, url):
        results = []
        while url:
            response = self._get_response(url, params=self.params)
            data = response.json()
            url = data.get('next')
            results = results + data.get('results')
        return results

    def _save(self, data):
        if self.template and self.data_insert_to:
            self.template[self.data_insert_to] = data
            data = self.template
        file_path = self.result_path.joinpath(f"{self.file_name}.json")
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding='UTF-8')


class Parse5ka_get_categories:
    def __init__(self, url: str):
        self.url = url

    def run(self) -> requests.Response:
        response = requests.get(self.url)
        if response.status_code == 200:
            return response


if __name__ == '__main__':
    url_categories = 'https://5ka.ru/api/v2/categories/'
    url_api = 'https://5ka.ru/api/v2/special_offers/'

    categories = Parse5ka_get_categories(url_categories).run().json()
    file_path = Path(__file__).parent.joinpath('categories')
    if not file_path.exists():
        file_path.mkdir()

    url_params = {
        'records_per_page': 20,
        'categories': int
    }

    for category in categories:
        url_params['categories'] = category['parent_group_code']

        write_template = {
            'name': category['parent_group_name'],
            'code': category['parent_group_code'],
            'products': []
        }

        parser = Parse5ka(start_url=url_api,
                          params=url_params,
                          result_path=file_path,
                          file_name=f"{'category_' + category['parent_group_code']}",
                          template=write_template,
                          data_insert_to='products')
        parser.run()
