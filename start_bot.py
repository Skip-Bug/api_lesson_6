"""Модуль для запуска Telegram-бота с комиксами xkcd."""
import argparse
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import BadRequest, NetworkError, TimedOut, Unauthorized

from comic_loader import get_comic_xkcd, get_latest_comic_num, get_random_comic
from utils import download_image


def send_bot(bot, channel_id, image_path, caption='Привет от Бота!'):
    """Отправляет изображение в Telegram канал.

    Args:
        bot (Bot): Экземпляр Telegram Bot.
        channel_id (str): ID канала.
        image_path (Path): Путь к изображению.
        caption (str): Текст поста.

    Raises:
        Telegram errors: При проблемах с отправкой.
    """
    with open(image_path, 'rb') as image_file:
        bot.send_photo(
            chat_id=channel_id,
            photo=image_file,
            caption=caption
        )


def create_parser():
    """Создаёт парсер аргументов для бота.

    Returns:
        ArgumentParser: Парсер с аргументом -x.
    """
    parser = argparse.ArgumentParser(
        description='Отправляет комикс в Telegram канал'
    )
    parser.add_argument(
        '-x',
        '--xkcd',
        type=int,
        help='Номер комикса (пусто - последний, 0 - случайный)'
    )
    return parser


def main():
    """Отправляет один комикс в Telegram канал.

    Читает токен и ID канала из .env, определяет какой комикс публиковать,
    скачивает изображение, отправляет в канал и удаляет файл.
    """
    load_dotenv()

    channel_id = os.getenv('TG_CHANNEL_ID')
    token = os.getenv('TG_BOT_TOKEN')

    if not channel_id:
        print('Канал не обнаружен')
        return
    if not token:
        print('Токен не найден в .env')
        return

    parser = create_parser()
    args = parser.parse_args()

    bot = Bot(token=token)

    try:
        if args.xkcd is None:
            comic_num = get_latest_comic_num()
            comic_info = get_comic_xkcd(comic_num)
            print(f'Публикуем последний комикс #{comic_num}')
        elif args.xkcd == 0:
            comic_info = get_random_comic()
            comic_num = comic_info['num']
            print(f'Публикуем случайный комикс #{comic_num}')
        else:
            comic_info = get_comic_xkcd(args.xkcd)
            comic_num = args.xkcd
            print(f'Публикуем комикс #{comic_num}')
    except requests.exceptions.RequestException as e:
        print(f'Ошибка сети при скачивании комикса: {e}')
        return
    image_path = None

    try:
        image_path = download_image(comic_info['img'])
        print(f'Комикс сохранён: {image_path}')

        send_bot(bot, channel_id, image_path, comic_info.get('alt', ''))
        print('Комикс отправлен.')
    except (requests.exceptions.RequestException,
            BadRequest, NetworkError, TimedOut, Unauthorized) as e:
        print(f'Ошибка: {e}')
    finally:
        if image_path:
            Path(image_path).unlink(missing_ok=True)
            print(f'Файл {image_path} удалён.')


if __name__ == '__main__':
    main()
