"""Модуль с общими функциями для загрузки изображений."""
from os.path import split, splitext
from urllib.parse import unquote, urlsplit

import requests
from pathlib import Path


def add_common_args(parser):
    """Добавляет общие аргументы для скриптов загрузки изображений.

    Args:
        parser (ArgumentParser): Парсер для добавления аргументов.

    Returns:
        ArgumentParser: Парсер с добавленными аргументами.
    """
    parser.add_argument(
        '-n',
        '--name',
        help=(
            'Имя файла (без расширения). '
            'По умолчанию извлекается из URL'
        )
    )
    parser.add_argument(
        '-p',
        '--path',
        default='images',
        help='Папка для сохранения (по умолчанию images)'
    )
    return parser


def get_filename(url):
    """Извлекает имя и расширение файла из URL.

    Args:
        url (str): Адрес картинки в интернете.

    Returns:
        tuple: Кортеж (имя_файла, расширение).
    """
    path, filename = split(unquote(urlsplit(url).path))
    name_image, extension = splitext(filename)
    if not extension:
        extension = '.jpeg'
    return name_image, extension


def ensure_list(some_links):
    """Приводит значение к списку для универсальной итерации.

    Делает из любого количества ссылок, полученных от запроса, список.

    Args:
        some_links: Необработанные ответы от других функций.

    Returns:
        list: Список ссылок (даже если одна ссылка) или пустой список.
    """
    if some_links is None:
        return []
    if isinstance(some_links, list):
        return some_links
    return [some_links]


def download_image(
    url,
    name_image=None,
    path='images',
    number_image=None,
    headers=None
):
    """Сохраняет картинку по URL в указанную папку.

    Возвращает путь к сохранённому файлу.

    Args:
        url (str): Адрес картинки в интернете.
        name_image (str): Название изображения.
        path (str): Папка для сохранения (будет создана, если нет).
        number_image (int, optional): Номер изображения для сохранения
            (если изображение одно, то сохранится по названию, если
            их несколько, то название_1 и т.д.).
        headers (dict, optional): Заголовки HTTP (если None,
            используется стандартный User-Agent).

    Returns:
        Path: Путь к сохранённому файлу.
    """
    if headers is None:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/145.0.0.0 Safari/537.36'
            )
        }
    folder_path = Path(path)
    folder_path.mkdir(parents=True, exist_ok=True)

    name_from_url, extension = get_filename(url)

    if name_image:
        final_name = name_image
    elif name_from_url:
        final_name = name_from_url
    else:
        final_name = 'noname'

    if number_image is None:
        full_path = folder_path / f'{final_name}{extension}'
    else:
        full_path = folder_path / f'{final_name}_{number_image}{extension}'

    response = requests.get(url, headers=headers, timeout=60)
    response.raise_for_status()
    full_path.write_bytes(response.content)
    return full_path
