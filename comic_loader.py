"""Модуль для скачивания комиксов с xkcd.com."""
import argparse
import random

import requests

from utils import add_common_args, download_image


def create_parser():
    """Создаёт парсер аргументов для comic_loader.

    Returns:
        ArgumentParser: Парсер с аргументами -x, -n, -p.
    """
    parser = argparse.ArgumentParser(
        description='Скачивает комиксы с xkcd.com'
    )
    parser.add_argument(
        '-x',
        '--xkcd',
        type=int,
        default=None,
        help='Номер комикса. Если не указан — последний, 0 — случайный.'
    )
    add_common_args(parser)
    return parser


def get_comic_xkcd(xkcd_num):
    """Получает информацию о комиксе с xkcd.com.

    Args:
        xkcd_num (int): Номер комикса.

    Returns:
        dict: Данные комикса (title, alt, img, num и др.).

    Raises:
        requests.exceptions.HTTPError: Если комикс не найден.
    """
    url = f'https://xkcd.com/{xkcd_num}/info.0.json'
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def get_latest_comic_num():
    """Возвращает номер последнего комикса на xkcd.

    Returns:
        int: Номер последнего комикса.
    """
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()['num']


def get_random_comic():
    """Возвращает данные случайного комикса.

    Returns:
        dict: Данные случайного комикса.
    """
    max_num = get_latest_comic_num()
    random_num = random.randint(1, max_num)
    return get_comic_xkcd(random_num)


def main():
    """Запускает скачивание комикса с xkcd.com.

    Читает аргументы командной строки, определяет какой комикс скачать
    (по умолчанию последний, 0 — случайный, число — конкретный),
    скачивает изображение и сохраняет в папку.
    """
    parser = create_parser()
    args = parser.parse_args()

    name_image = args.name.strip().lower() if args.name else None
    path = args.path.strip() if args.path else 'images/'

    try:
        if args.xkcd is None:
            latest_num = get_latest_comic_num()
            comic_info = get_comic_xkcd(latest_num)
            print(f'Скачиваем последний комикс №{latest_num}')
        elif args.xkcd == 0:
            comic_info = get_random_comic()
            print(f'Скачиваем случайный комикс №{comic_info["num"]}')
        else:
            comic_info = get_comic_xkcd(args.xkcd)
            print(f'Скачиваем комикс №{args.xkcd}')
    except requests.exceptions.RequestException as error:
        print(f'Ошибка запроса к xkcd.com: {error}')
        return

    comic_link = comic_info.get('img')
    if not comic_link:
        print('Комикс не найден (отсутствует ссылка на изображение).')
        return

    try:
        saved_path = download_image(comic_link, name_image, path)
        print(f'Файл сохранён: {saved_path}')
        print(f'{comic_info["alt"]}')
    except requests.exceptions.ReadTimeout:
        print('Превышено время ожидания...')
    except requests.exceptions.ConnectionError as error:
        print(error, 'Ошибка соединения')
    except requests.exceptions.HTTPError as error:
        print(f'Ошибка HTTP: {error.response.status_code}')


if __name__ == '__main__':
    main()
