"""Модуль с общими функциями для загрузки изображений."""
from os.path import split, splitext
from urllib.parse import unquote, urlsplit

import requests
from pathlib import Path


def ensure_folder(path):
    """Создаёт папку, если её нет.

    Args:
        path (str или Path): Путь к папке.

    Returns:
        Path: Объект Path для созданной/существующей папки.
    """
    folder_path = Path(path)
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path


def get_filename(url):
    """Извлекает имя и расширение файла из URL.

    Args:
        url (str): Адрес картинки в интернете.

    Returns:
        tuple: Кортеж (имя_файла, расширение).
    """
    path_url, filename = split(unquote(urlsplit(url).path))
    name_image, extension = splitext(filename)
    if not extension:
        extension = '.jpeg'
    return name_image, extension


def download_image(url, path=None, headers=None):
    """Сохраняет картинку по URL.

    Возвращает путь к сохранённому файлу. Если path=None, сохраняет в корень.

    Args:
        url (str): Адрес картинки в интернете.
        path (str, optional): Папка для сохранения. Если None — в корень.
        headers (dict, optional): Заголовки HTTP (если None,
            используется стандартный User-Agent).

    Returns:
        Path: Путь к сохранённому файлу.
    """
    if path:
        folder_path = ensure_folder(path)
    else:
        folder_path = Path('.')

    if headers is None:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/145.0.0.0 Safari/537.36'
            )
        }

    name_from_url, extension = get_filename(url)
    final_name = name_from_url if name_from_url else 'noname'

    full_path = folder_path / f'{final_name}{extension}'

    response = requests.get(url, headers=headers, timeout=60)
    response.raise_for_status()
    full_path.write_bytes(response.content)
    return full_path
