import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from functions import *
from database import *


if __name__ == '__main__':
    while True:
        msg, id_user = repeat_bot()
        if msg:
            greetings(id_user)
            current_id_user = check_db_user(id_user)
            if current_id_user == None:
                register_user(id_user)
                current_id_user = check_db_user(id_user)
            msg, id_user = repeat_bot()
            if msg == 'start':
                sex_opposite, city_title = get_user_info(id_user)
                if city_title == 0:
                    write_msg(id_user, 'Город где ищем? (пример: Москва ): ')
                    msg, id_user = repeat_bot()
                    city_title = msg
                city_id = get_city_identificator(city_title)
                write_msg(id_user, 'Минимальный возраст (от 18) для поиска: ')
                msg, id_user = repeat_bot()
                min_age = msg
                if int(min_age) < 18:
                    write_msg(id_user, 'Минимальный возраст - 18 лет!')
                    min_age = 18
                write_msg(id_user, 'Максимальный возраст (до 80) для поиска: ')
                msg, id_user = repeat_bot()
                max_age = msg
                if int(max_age) >= 100:
                    write_msg(id_user, 'Максимальный возраст - 80 лет!')
                    max_age = 80
                candidates = people_search(sex_opposite, city_id, min_age, max_age)
                for candidate in candidates:
                    prospect_id = int(candidate[0])
                    checked_prospect = check_db_prospect(prospect_id)
                    current_id_user = check_db_user(id_user)
                    if checked_prospect == None:
                        add_user(candidate[0], candidate[1], candidate[2], candidate[3], current_id_user.id)
                        link = candidate[3]
                        photos = get_candidate_photos(candidate[0])
                        write_msg_with_attachmt(id_user, link, photos)
                        write_msg(id_user, 'Продолжить поиск - 1\n'
                                           'Выход / Начать поиск сначала - 2')
                        msg, id_user = repeat_bot()
                        if msg == '1':
                            continue
                        elif msg == '2':
                            write_msg(id_user, 'Спасибо за использование бота!\n'
                                               'Для перезапуска поиска введите любой текст!')
                            break
                        else:
                            write_msg(id_user, 'Нажмите любую кнопку!')
                            break
                    else:
                        continue
                write_msg(id_user, 'Спасибо за просмотр!\n'
                                   'Введите любой текст для перезапуска бота!')
