"""Модуль для публикации комиксов xkcd в ВКонтакте."""
import argparse
import os
import sys

import requests
from dotenv import load_dotenv

from comic_loader import get_comic_xkcd, get_latest_comic_num, get_random_comic
from utils import download_image


def create_parser():
    """Создаёт парсер аргументов для vk_poster.

    Returns:
        ArgumentParser: Парсер с аргументами -x и -p.
    """
    parser = argparse.ArgumentParser(description='Публикует комикс xkcd в VK')
    parser.add_argument(
        '-x',
        '--xkcd',
        type=int,
        help='Номер (пусто - последний, 0 - случайный)'
    )
    parser.add_argument(
        '-p',
        '--path',
        default='images',
        help='Папка для комиксов'
    )
    return parser


def vk_api_request(method, params, token, v):
    """Запрос к VK API.

    При ошибке сети или невалидном ключе завершает программу.

    Args:
        method (str): Метод API.
        params (dict): Параметры запроса.
        token (str): Токен доступа VK.
        v (str): Версия API.

    Returns:
        dict: Ответ от API (response).

    Raises:
        SystemExit: При сетевой ошибке или ошибке VK API.
    """
    params.update({'access_token': token, 'v': v})
    try:
        resp = requests.get(
            f'https://api.vk.com/method/{method}',
            params=params,
            timeout=30
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        sys.exit(f'Сетевая ошибка VK: {e}')

    data = resp.json()
    if 'error' in data:
        code = data['error']['error_code']
        msg = data['error']['error_msg']
        if code == 5:
            sys.exit(
                'Ошибка VK: неверный access_token. Проверьте VK_KEY в .env'
            )
        sys.exit(f'Ошибка VK API {code}: {msg}')
    return data['response']


def post_photo_to_wall(image_path, message, token, group_id, v):
    """Загружает фото на стену группы и публикует пост.

    Args:
        image_path (Path): Путь к изображению.
        message (str): Текст поста.
        token (str): Токен доступа VK.
        group_id (str): ID группы.
        v (str): Версия API.

    Returns:
        int: ID опубликованного поста.
    """
    upload_server = vk_api_request(
        'photos.getWallUploadServer',
        {'group_id': group_id},
        token,
        v
    )
    upload_url = upload_server['upload_url']

    with open(image_path, 'rb') as f:
        upload_data = requests.post(
            upload_url,
            files={'photo': f},
            timeout=60
        ).json()

    saved = vk_api_request(
        'photos.saveWallPhoto',
        {
            'group_id': group_id,
            'photo': upload_data['photo'],
            'server': upload_data['server'],
            'hash': upload_data['hash']
        },
        token,
        v
    )[0]

    attachment = f"photo{saved['owner_id']}_{saved['id']}"
    post = vk_api_request(
        'wall.post',
        {
            'owner_id': f'-{group_id}',
            'from_group': 1,
            'message': message,
            'attachments': attachment
        },
        token,
        v
    )
    return post['post_id']


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
        sys.exit('Ошибка: VK_KEY или GROUP_ID не найдены в .env')

    args = create_parser().parse_args()
    os.makedirs(args.path, exist_ok=True)

    if args.xkcd is None:
        comic_num = get_latest_comic_num()
        comic_info = get_comic_xkcd(comic_num)
        print(f'Публикуем последний комикс #{comic_num}')
    elif args.xkcd == 0:
        comic_info = get_random_comic()
        print(f'Публикуем случайный комикс #{comic_info["num"]}')
    else:
        comic_info = get_comic_xkcd(args.xkcd)
        print(f'Публикуем комикс #{args.xkcd}')

    image_path = download_image(comic_info['img'], path=args.path)
    print(f'Комикс сохранён: {image_path}')

    post_id = post_photo_to_wall(
        image_path,
        comic_info.get('alt', ''),
        token,
        group_id,
        v
    )
    print(f'Пост опубликован! ID: {post_id}')


if __name__ == '__main__':
    main()
