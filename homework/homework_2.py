"""
Источник https://magnit.ru/promo/?geo=moskva
Необходимо собрать структуры товаров по акции и сохранить их в MongoDB

пример структуры и типы обязательно хранить поля даты как объекты datetime
{
    "url": str,
    "promo_name": str,
    "product_name": str,
    "old_price": float,
    "new_price": float,
    "image_url": str,
    "date_from": "DATETIME",
    "date_to": "DATETIME"
}
"""

import requests
import bs4
from urllib.parse import urljoin
import time
import pymongo
import re
import datetime


class MagnitParse:
    def __init__(self, start_url, mongo_url, db_name):
        self.start_url = start_url
        client = pymongo.MongoClient(mongo_url)
        if db_name in client.list_database_names():
            client.drop_database(db_name)
        self.db = client[db_name]

    def get_response(self, url, *args, **kwargs):
        for _ in range(5):
            response = requests.get(url, *args, **kwargs)
            if response.status_code == 200:
                return response
            time.sleep(1)
        raise ValueError('URL DIE')

    def get_soup(self, url, *args, **kwargs) -> bs4.BeautifulSoup:
        soup = bs4.BeautifulSoup(self.get_response(url, *args, **kwargs).text, 'lxml')
        return soup

    @property
    def template(self):
        ru_months_list = {
            'января': 1,
            'февраля': 2,
            'марта': 3,
            'апреля': 4,
            'мая': 5,
            'июня': 6,
            'июля': 7,
            'августа': 8,
            'сентября': 9,
            'октября': 10,
            'ноября': 11,
            'декабря': 12,
        }

        def date_converter(date: str):
            date = date.replace('с ', '').replace('до ', '')
            day = date.split(' ')[0]
            month = ru_months_list[date.split(' ')[1]]
            year = datetime.date.today().year
            return datetime.datetime.strptime(f'{year} {month} {day}', '%Y %m %d')

        data_template = {
            'url': lambda a: urljoin(self.start_url, a.attrs.get('href', '/')),
            'promo_name': lambda a: a.find('div', attrs={'class': 'card-sale__header'}).text,
            'product_name': lambda a: a.find('div', attrs={'class': 'card-sale__title'}).text,
            'old_price': lambda a: float(
                re.sub(r'[^0-9%]+', r'', a.find('div', attrs={'class': 'label__price_old'}).text)
            ) / 100,
            'new_price': lambda a: float(
                re.sub(r'[^0-9%]+', r'', a.find('div', attrs={'class': 'label__price_new'}).text)
            ) / 100,
            'image_url': lambda a: urljoin(self.start_url, a.find('picture').find('img').attrs.get('data-src', '/')),
            'date_from': lambda a: date_converter(
                a.find('div', attrs={'class': 'card-sale__date'}).find_all('p')[0].text
            ),
            'date_to': lambda a: date_converter(
                a.find('div', attrs={'class': 'card-sale__date'}).find_all('p')[1].text
            )
        }
        return data_template

    def run(self):
        for item in self._parse(self.get_soup(self.start_url)):
            self.save(item)

    def _parse(self, soup):
        product_a = soup.find_all('a', attrs={'class': 'card-sale card-sale_catalogue'})
        for product_tag in product_a:
            product_data = {}
            for key, func in self.template.items():
                try:
                    product_data[key] = func(product_tag)
                except AttributeError:
                    pass
                except ValueError:
                    pass
            yield product_data

    def save(self, data):
        collection = self.db['magnit']
        collection.insert_one(data)


if __name__ == '__main__':
    url = 'https://magnit.ru/promo/?geo=moskva'
    mongo_url = 'mongodb://localhost:27017'
    db_homework_2_name = 'db_homework_2'
    parser = MagnitParse(url, mongo_url, db_homework_2_name)
    parser.run()