import argparse
import os
import requests
from dotenv import load_dotenv

from comic_loader import get_comic_xkcd, get_latest_comic_num, get_random_comic
from utils import download_image


def create_parser():
    parser = argparse.ArgumentParser(
        description='Публикует комикс xkcd в группе ВКонтакте'
    )
    parser.add_argument(
        '-x', '--xkcd',
        type=int,
        default=None,
        help='Номер комикса. Если не указан — последний, 0 — случайный.'
    )
    parser.add_argument(
        '-p', '--path',
        default='images',
        help='Папка для сохранения (по умолчанию images)'
    )
    return parser


def vk_request(method, params, token, v):
    params['access_token'] = token
    params['v'] = v
    resp = requests.get(f'https://api.vk.com/method/{method}', params=params)
    data = resp.json()
    if 'error' in data:
        raise Exception(f"VK API error: {data['error']['error_msg']}")
    return data['response']


def post_photo_to_wall(image_path, message, token, group_id, v):
    upload_server = vk_request('photos.getWallUploadServer', {
                               'group_id': group_id}, token, v)
    upload_url = upload_server['upload_url']

    with open(image_path, 'rb') as f:
        upload_data = requests.post(upload_url, files={'photo': f}).json()

    saved = vk_request('photos.saveWallPhoto', {
        'group_id': group_id,
        'photo': upload_data['photo'],
        'server': upload_data['server'],
        'hash': upload_data['hash']
    }, token, v)[0]

    attachment = f"photo{saved['owner_id']}_{saved['id']}"
    post = vk_request('wall.post', {
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'message': message,
        'attachments': attachment
    }, token, v)
    return post['post_id']

def publish_comic(comic_info, images_folder, token, group_id, v):
    """Скачивает и публикует комикс в VK."""
    image_url = comic_info['img']
    caption = comic_info.get('alt', '')
    image_path = download_image(image_url, path=images_folder)
    print(f"Комикс сохранён: {image_path}")
    post_id = post_photo_to_wall(image_path, caption, token, group_id, v)
    print(f"Пост опубликован! ID: {post_id}")

def main():
    load_dotenv()
    token = os.getenv('VK_KEY')
    group_id = os.getenv('GROUP_ID')
    v = '5.131'

    if not token or not group_id:
        print('Ошибка: VK_KEY или GROUP_ID не найдены в .env')
        return

    parser = create_parser()
    args = parser.parse_args()

    images_folder = args.path
    os.makedirs(images_folder, exist_ok=True)

    try:
        if args.xkcd is None:
            comic_num = get_latest_comic_num()
            comic_info = get_comic_xkcd(comic_num)
            print(f"Публикуем последний комикс #{comic_num}")
        elif args.xkcd == 0:
            comic_info = get_random_comic()
            comic_num = comic_info['num']
            print(f"Публикуем случайный комикс #{comic_num}")
        else:
            comic_num = args.xkcd
            comic_info = get_comic_xkcd(comic_num)
            print(f"Публикуем комикс #{comic_num}")
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == '__main__':
    main()
