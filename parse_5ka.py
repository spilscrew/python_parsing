import time
import json
from pathlib import Path
import requests

url = 'https://5ka.ru/special_offers/'
url_api = 'https://5ka.ru/api/v2/special_offers/'
params = {
    'records_per_page': 12
}

response: requests.Response = requests.get(url)

if response.status_code == 200:
    html_file = Path(__file__).parent.joinpath('5ka.html')
    html_file.write_text(response.text, encoding='UTF-8')


response_store: requests.Response = requests.get(url_api, params=params)

if response_store.status_code == 200:
    html_file = Path(__file__).parent.joinpath('5ka.json')
    html_file.write_text(response_store.text, encoding='UTF-8')


class Parse5ka:
    params = {
        'records_per_page': 12
    }

    def __init__(self, start_url: str, result_path: Path):
        self.start_url = start_url
        self.result_path = result_path

    def _get_response(self, url, *args, **kwargs) -> requests.Response:
        while True:
            response = requests.get(url, *args, **kwargs)
            if response.status_code == 200:
                return response
            time.sleep(1)

    def run(self):
        for product in self._parse(self.start_url):
            self._save(product)

    def _parse(self, url):
        while url:
            response = self._get_response(url, params=self.params)
            data = response.json()
            url = data.get('next')
            for product in data.get('results', []):
                yield product

    def _save(self, data):
        file_path = self.result_path.joinpath(f"{data['id']}.json")
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding='UTF-8')


if __name__ == '__main__':
    file_path = Path(__file__).parent.joinpath('products')
    if not file_path.exists():
        file_path.mkdir()
    parser = Parse5ka(url_api, file_path)
    parser.run()