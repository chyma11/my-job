import random
from random import randrange
import datetime
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from database import create_db, create_tables, insert_users, check_users


with open('bot_token.txt', 'r') as file:
    bot_token = file.readline()
with open('user_token.txt', 'r') as file:
    user_token = file.readline()


vk = vk_api.VkApi(token=bot_token)
vk2 = vk_api.VkApi(token=user_token)
longpoll = VkLongPoll(vk)


def get_user_info(user_id):
    # Записывает информацию в словарь о пользователе, который пишет боту, в случае с городом, берет id города
    user_info = {}
    response = vk.method('users.get', {'user_id': user_id,
                                               'v': 5.131,
                                               'fields': 'first_name, last_name, bdate, sex, city'})
    if response:
        for key, value in response[0].items():
            if key == 'city':
                user_info[key] = value['id']
            else:
                user_info[key] = value
    else:
        write_msg(user_id, 'Ошибка')
        return False
    return user_info


def check_missing_info(user_info):
    # Записывает в словарь ключи отсутсвующей информации
    info_missing = []
    for item in ['bdate', 'sex', 'city']:
        if not user_info.get(item):
            info_missing.append(item)
    if user_info.get('bdate'):
        if len(user_info['bdate'].split('.')) != 3:
            info_missing.append('bdate')
    return info_missing


def write_msg(user_id, message, attachment=' '):
    # Функция отправки сообщений
    vk.method('messages.send', {'user_id': user_id,
                                        'message': message,
                                        'random_id': randrange(10 ** 7),
                                        'attachment': attachment})


def get_additional_information(user_id, field):
    # Функция запрашивает у пользователя недостающую информацию
    # когда в дате рождения указан только день и месяц, то запрашивает полную дату
    dict = {
        'bdate': 'вашу дату рождения в формате ХХ.ХХ.ХХХХ',
        'city': 'ваш город'}
    write_msg(user_id, f'''Недостаточно о вас информации, введите следующие данные:\n{dict[field]}''')
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                if field == 'city':
                    return get_city(user_id, event.text)
                elif field == 'bdate':
                    if len(event.text.split('.')) != 3:
                        write_msg(user_id, 'Неверно указана дата рождения')
                        return False
                    return event.text


def get_city(user_id, city):
    # Функция запрашивает у пользователя название города, возвращает id города
    values = {
        'country_id': 1,
        'q': city,
        'count': 1
    }
    response = vk2.method('database.getCities', values=values)
    if response['items']:
        city_id = response['items'][0]['id']
        return city_id
    else:
        write_msg(user_id, 'Неверно указан город')
        return False


def get_age(date):
    # Функция высчитывает возраст пользователя по дате рождения
    return datetime.datetime.now().year - int(date[-4:])


def find_users(user_info):
    # Функция ищет пару по данным пользователя, пол берет противоположный, возраст +-3 года от возраста пользователя
    response = vk2.method('users.search', {
                                  'age_from': user_info['age'] - 3,
                                  'age_to': user_info['age'] + 3,
                                  'sex': 3 - user_info['sex'],
                                  'city': user_info['city'],
                                  'status': 6,
                                  'has_photo': 1,
                                  'count': 1000,
                                  'v': 5.131})
    if response:
        if response.get('items'):
            return response.get('items')
        write_msg(user_info['id'], 'Ошибка')
        return False



def random_users(users):
    # Функция выбирает случайного пользователя из найденых
    filter_success = False
    random_choice = {}
    while not filter_success:
        random_choice = random.choice(users)
        if get_photos(random_choice['id']) and not random_choice['is_closed'] and check_users(random_choice):
            filter_success = True
    return random_choice


def get_photos(user_id):
    # Функция возвращает по user_id 3 фотографии, сортирует по количеству лайков и комментариев
    try:
        response = vk2.method('photos.get', {'owner_id': user_id,
                                                     'album_id': 'profile',
                                                     'extended': '1',
                                                     'v': 5.131})
        if response.get('count'):
            if response.get('count') < 3:
                return False
            top_photos = sorted(response.get('items'), key=lambda x: x['likes']['count']
                                + x['comments']['count'], reverse=True)[:3]
            photo_data = {'user_id': top_photos[0]['owner_id'], 'photo_ids': []}
            for photo in top_photos:
                photo_data['photo_ids'].append(photo['id'])
            return photo_data
        return False
    except vk_api.exceptions.ApiError as error:
        print(error)

def main():
    create_db()
    create_tables()
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                user_info = get_user_info(event.user_id)
                if not user_info:
                    continue
                write_msg(event.user_id, f'''Привет, {user_info['first_name']}!
Вас приветствует бот Vkinder.''')
                info_missing = check_missing_info(user_info)
                while info_missing:
                    additional_info = get_additional_information(event.user_id, info_missing[0])
                    if not additional_info:
                        continue
                    user_info[info_missing[0]] = additional_info
                    info_missing.pop(0)
                user_info['age'] = get_age(user_info['bdate'])
                write_msg(event.user_id, 'Информации о вас достаточно, начинаем поиск пары')
                users_found = find_users(user_info)
                if not users_found:
                    write_msg(event.user_id, 'Пара не найдена')
                    continue
                command = 'да'
                while command.lower() == 'да':
                    random_user = random_users(users_found)
                    photo_data = get_photos(random_user['id'])
                    insert_users(random_user, photo_data)
                    write_msg(event.user_id,
                              f'''Возможная пара: {random_user['first_name']} {random_user['last_name']}
Ссылка на пользователя: vk.com/id{random_user['id']}
Фото:''',
                              attachment=f"photo{photo_data['user_id']}_{photo_data['photo_ids'][0]},"
                                         f"photo{photo_data['user_id']}_{photo_data['photo_ids'][1]},"
                                         f"photo{photo_data['user_id']}_{photo_data['photo_ids'][2]}")
                    write_msg(event.user_id, 'Чтобы показать дальше, напиши "да",\nЧтобы закончить поиск напиши что-нибудь другое ')
                    for new_event in longpoll.listen():
                        if new_event.type == VkEventType.MESSAGE_NEW:
                            if new_event.to_me:
                                command = new_event.text
                                break


if __name__ == '__main__':
    main()
