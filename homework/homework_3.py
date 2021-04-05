"""
Источник https://geekbrains.ru/posts/
Необходимо обойти все записи в блоге и извлеч из них информацию следующих полей:

url страницы материала
Заголовок материала
Первое изображение материала (Ссылка)
Дата публикации (в формате datetime)
имя автора материала
ссылка на страницу автора материала
комментарии в виде (автор комментария и текст комментария)
список тегов
реализовать SQL структуру хранения данных c следующими таблицами

Post
Comment
Writer
Tag
Организовать реляционные связи между таблицами

При сборе данных учесть, что полученый из данных автор уже может быть в БД и значит необходимо это заблаговременно проверить.
Не забываем закрывать сессию по завершению работы с ней
"""

import typing
import requests
import bs4
from urllib.parse import urljoin
from homework.database import db
import dateutil.parser


class GbBlogParse:
    def __init__(self, start_url, database: db.Database):
        self.db = database
        self.start_url = start_url
        self.done_urls = set()
        self.tasks = []

    def get_task(self, url: str, callback: typing.Callable) -> typing.Callable:
        def task():
            soup = self._get_soup(url)
            return callback(url, soup)
        return task

    def _get_response(self, url, *args, **kwargs) -> requests.Response:
        #TODO: Обработать статус кода и ошибки
        response = requests.get(url, *args, **kwargs)
        return response

    def _get_soup(self, url, *args, **kwargs):
        soup = bs4.BeautifulSoup(self._get_response(url, *args, **kwargs).text, 'lxml')
        return soup

    def parse_post(self, url, soup):
        author_tag = soup.find('div', attrs={'itemprop': 'author'})
        post_image = soup.find('div', attrs={'class': 'blogpost-content'}).find('img')
        comments_table_id = soup.find('comments').attrs.get('commentable-id')
        comments_data = self._get_response(
            'https://gb.ru/api/v2/comments',
            {
                'commentable_type': 'Post',
                'commentable_id': int(comments_table_id),
                'order': 'desc'
            }).json()
        data = {
            'post_data': {
                'title': soup.find('h1', attrs={'class': 'blogpost-title'}).text,
                'url': url,
                'image': post_image.attrs.get('src') if post_image else None,
                'created_at': dateutil.parser.isoparse(
                    soup.find('time', attrs={'itemprop': 'datePublished'}).attrs.get('datetime')
                )
            },
            'author_data': {
                'url': urljoin(url, author_tag.parent.attrs.get('href')),
                'name': author_tag.text
            },
            'tags_data': [{'url': urljoin(url, tag_a.attrs.get('href')), 'name': tag_a.text}
                          for tag_a in soup.find_all('a', attrs={'class': 'small'})],
            'comments_data': {
                'url': '',
                'name': '',
                'text': ''
            }
        }
        return data

    def parse_feed(self, url, soup):
        ul = soup.find('ul', attrs={'class': 'gb__pagination'})
        pag_urls = set(
            urljoin(url, url_a.attrs.get('href'))
                       for url_a in ul.find_all('a') if url_a.attrs.get('href')
        )
        for pag_url in pag_urls:
            if pag_url not in self.done_urls:
                task = self.get_task(pag_url, self.parse_feed)
                self.done_urls.add(pag_url)
                self.tasks.append(task)
        post_urls = set(
            urljoin(url, url_a.attrs.get('href'))
                       for url_a in soup.find_all('a', attrs={'class': 'post-item__title'}) if url_a.attrs.get('href')
        )
        for post_url in post_urls:
            if post_url not in self.done_urls:
                task = self.get_task(post_url, self.parse_post)
                self.done_urls.add(post_url)
                self.tasks.append(task)

    def run(self):
        task = self.get_task(self.start_url, self.parse_feed)
        self.tasks.append(task)
        self.done_urls.add(self.start_url)

        for task in self.tasks:
            task_result = task()
            if task_result:
                self.save(task_result)

    def save(self, data):
        self.db.create_post(data)


if __name__ == '__main__':
    database = db.Database('sqlite:///db_homework_blog.db')
    parser = GbBlogParse('https://geekbrains.ru/posts', database)
    parser.run()
