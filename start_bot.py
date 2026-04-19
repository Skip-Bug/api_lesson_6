"""Модуль для запуска Telegram-бота с комиксами xkcd."""
import argparse
import os
from pathlib import Path
import sys
import time

from dotenv import load_dotenv
import requests
from telegram import Bot
from telegram.error import BadRequest, NetworkError, TimedOut, Unauthorized

from comic_loader import get_comic_xkcd, get_latest_comic_num, get_random_comic
from utils import download_image


def send_bot(bot, channel_id, image_path, caption='Привет от Бота!'):
    """Постит изображение в телеграм канале.

    Args:
        bot (Bot): Экземпляр Telegram Bot.
        channel_id (str): ID канала.
        image_path (Path): Путь к изображению.
        caption (str): Текст поста (по умолчанию 'Привет от Бота!').

    Returns:
        bool: True если успешно, False если ошибка.
    """
    try:
        with open(image_path, 'rb') as image_file:
            bot.send_photo(
                chat_id=channel_id,
                photo=image_file,
                caption=caption
            )
        print(f'Отправлено: {os.path.basename(image_path)}')
        return True
    except FileNotFoundError:
        print(f'Файл не найден: {image_path}')
        return False
    except (TimedOut, NetworkError) as error:
        print(f'Ошибка сети: {error}')
        return False
    except BadRequest as error:
        print(f'Ошибка запроса: {error}')
        return False
    except Unauthorized:
        print('Бот заблокирован в канале!')
        return False


def create_parser():
    """Создаёт парсер аргументов для бота.

    Returns:
        ArgumentParser: Парсер с аргументами -x, -s, -p.
    """
    parser = argparse.ArgumentParser(
        description='Запускает бота с задержкой публикаций'
    )
    parser.add_argument(
        '-x',
        '--xkcd',
        type=int,
        help='Номер комикса (пусто - последний, 0 - случайный)'
    )
    parser.add_argument(
        '-s',
        '--sleep',
        type=int,
        default=14400,
        help='Задержка публикаций (по умолчанию 4 часа)'
    )
    parser.add_argument(
        '-p',
        '--path',
        default='images',
        help='Папка для сохранения (по умолчанию images)'
    )
    return parser


def main():
    """Запускает Telegram-бота для публикации комиксов xkcd.

    Читает токен и ID канала из .env, определяет какой комикс публиковать
    (по умолчанию последний, 0 — случайный, число — конкретный),
    скачивает изображение и отправляет в канал.
    Затем переходит к бесконечному циклу с задержкой.
    Ctrl+C останавливает бота.
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

    images_folder = args.path
    sleep_seconds = args.sleep

    os.makedirs(images_folder, exist_ok=True)

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
        sys.exit(f'Ошибка сети при скачивании комикса: {e}')

    try:
        image_path = download_image(comic_info['img'], path=images_folder)
        print(f'Комикс сохранён: {image_path}')
        if send_bot(bot, channel_id, image_path, comic_info.get('alt', '')):
            # удаляем после успешной отправки
            Path(image_path).unlink(missing_ok=True)
            print(f'Файл {image_path} удалён.')
        else:
            print('Не удалось отправить первый комикс.')
    except requests.exceptions.RequestException as e:
        print(f'Ошибка при обработке первого комикса: {e}')
        return

    try:
        while True:
            next_comic_info = get_random_comic()
            next_image_path = download_image(
                next_comic_info['img'],
                path=images_folder
            )
            print(f'Публикуем комикс #{next_comic_info["num"]}')

            if send_bot(
                bot,
                channel_id,
                next_image_path,
                next_comic_info.get('alt', '')
            ):
                Path(next_image_path).unlink(missing_ok=True)
                print(f'Файл {next_image_path} удалён.')
            else:
                print('Не удалось отправить комикс.')
            time.sleep(sleep_seconds)

    except KeyboardInterrupt:
        print('\nБот остановлен пользователем.')
        bot.send_message(
            chat_id=channel_id,
            text='Бот завершил работу'
        )


if __name__ == '__main__':
    main()
