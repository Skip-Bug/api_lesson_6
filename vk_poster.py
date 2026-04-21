"""Модуль для публикации комиксов xkcd в ВКонтакте."""
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from comic_loader import get_random_comic
from utils import download_image


def get_upload_url(token, group_id, v):
    """Получает URL для загрузки фото на стену.

    Args:
        token (str): Токен доступа VK.
        group_id (str): ID группы.
        v (str): Версия API.

    Returns:
        str: URL для загрузки фото.
    """
    response = requests.get(
        'https://api.vk.com/method/photos.getWallUploadServer',
        params={'access_token': token, 'v': v, 'group_id': group_id},
        timeout=30
    )
    response.raise_for_status()
    return response.json()['response']['upload_url']


def upload_photo(image_path, upload_url):
    """Загружает фото на сервер VK.

    Args:
        image_path (Path): Путь к изображению.
        upload_url (str): URL для загрузки.

    Returns:
        dict: Данные загруженного фото.
    """
    with open(image_path, 'rb') as f:
        response = requests.post(
            upload_url,
            files={'photo': f},
            timeout=60
        )
        response.raise_for_status()
        return response.json()


def save_photo(token, group_id, v, upload_data):
    """Сохраняет загруженное фото в альбом группы.

    VK API требует сохранить фото после загрузки.

    Args:
        token (str): Токен доступа VK.
        group_id (str): ID группы.
        v (str): Версия API.
        upload_data (dict): Данные от upload_photo.

    Returns:
        dict: Сохранённое фото.
    """
    params = {
        'access_token': token,
        'v': v,
        'group_id': group_id,
        'photo': upload_data['photo'],
        'server': upload_data['server'],
        'hash': upload_data['hash']
    }
    response = requests.get(
        'https://api.vk.com/method/photos.saveWallPhoto',
        params=params,
        timeout=30
    )
    response.raise_for_status()
    return response.json()['response'][0]


def create_post(token, group_id, v, saved_photo, message):
    """Публикует пост с фото на стене группы.

    Args:
        token (str): Токен доступа VK.
        group_id (str): ID группы.
        v (str): Версия API.
        saved_photo (dict): Данные сохранённого фото.
        message (str): Текст поста.

    Returns:
        int: ID опубликованного поста.
    """
    attachment = f"photo{saved_photo['owner_id']}_{saved_photo['id']}"
    params = {
        'access_token': token,
        'v': v,
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'message': message,
        'attachments': attachment
    }
    response = requests.get(
        'https://api.vk.com/method/wall.post',
        params=params,
        timeout=30
    )
    response.raise_for_status()
    return response.json()['response']['post_id']


def main():
    """Запускает публикацию комикса в VK.

    Читает токен и ID группы из .env, определяет какой комикс публиковать,
    скачивает изображение и публикует на стене группы.
    """
    load_dotenv()
    token = os.getenv('VK_KEY')
    group_id = os.getenv('GROUP_ID')
    v = '5.131'

    if not token or not group_id:
        print('Ошибка: VK_KEY или GROUP_ID не найдены в .env')
        return

    try:
        comic_info = get_random_comic()
        print(f'Публикуем случайный комикс #{comic_info["num"]}')
    except requests.exceptions.RequestException as e:
        print(f'Ошибка получения комикса: {e}')
        return

    image_path = None
    try:
        image_path = download_image(comic_info['img'])
        print(f'Комикс сохранён: {image_path}')

        upload_url = get_upload_url(token=token, group_id=group_id, v=v)
        upload_data = upload_photo(
            image_path=image_path,
            upload_url=upload_url
        )
        saved_photo = save_photo(
            token=token,
            group_id=group_id,
            v=v,
            upload_data=upload_data
        )
        post_id = create_post(
            token=token,
            group_id=group_id,
            v=v,
            saved_photo=saved_photo,
            message=comic_info.get('alt', '')
        )

        print(f'Пост опубликован! ID: {post_id}')
    except requests.exceptions.RequestException as e:
        print(f'Ошибка сети: {e}')

    finally:
        if image_path:
            Path(image_path).unlink(missing_ok=True)
            print(f'Файл {image_path} удалён.')


if __name__ == '__main__':
    main()
