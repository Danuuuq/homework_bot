import logging
import os
import requests
import time

from dotenv import load_dotenv
from telebot import TeleBot

load_dotenv()


PRACTICUM_TOKEN = os.getenv('TOKEN_YA')
TELEGRAM_TOKEN = os.getenv('TOKEN_TG')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


class EmptyValueException(Exception):
    pass


class EndpointException(Exception):
    pass


def check_tokens():
    """Проверка доступности переменных."""
    for value in [
        ('PRACTICUM_TOKEN', PRACTICUM_TOKEN),
        ('TELEGRAM_TOKEN', TELEGRAM_TOKEN),
        ('TELEGRAM_CHAT_ID', TELEGRAM_CHAT_ID)
    ]:
        if value[1] is None:
            logger.critical(
                f'Отсутствует обязательная переменная окружения: {value[0]}. '
                'Программа принудительно остановлена.'
            )
            raise EmptyValueException(f'Отсутствует переменная {value[0]}')


def send_message(bot, message):
    """Отправка сообщения пользователю."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logger.error(f'Ошибка при отправке сообщения {error}')
    else:
        logger.debug(f'Бот отправил сообщение: "{message}"')


def get_api_answer(timestamp):
    """Запрос к эндпоинту API."""
    payloads = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payloads)
    except Exception:
        raise EndpointException(f'Эндпоинт {ENDPOINT} недоступен.')
    else:
        if response.status_code != 200:
            raise EndpointException(
                f'Эндпоинт {ENDPOINT} недоступен. '
                'Код ответа API: {response.status_code}'
            )
        return response.json()


def check_response(response):
    """Проверка полученного ответа от API."""
    try:
        response.get('homeworks')
    except TypeError:
        raise EndpointException('Это не словарь')
    except KeyError:
        code = response['code']
        raise EndpointException(
            f'От эндпоинта {ENDPOINT} пришел ответ: {code}'
        )
    else:
        return response.get('homeworks'), response.get('current_date')


def parse_status(homework):
    """Извлечение информации из ответа."""
    try:
        verdict = HOMEWORK_VERDICTS[homework['status']]
    except TypeError:
        raise EndpointException('Новых заданий не поступало')
    except KeyError as error:
        raise EndpointException(f'Получен неожиданный статус домашней работы: {error}')
    else:
        homework_name = homework['lesson_name']
    return f'Изменился статус проверки работы {homework_name}. {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(TELEGRAM_TOKEN)
    # timestamp = int(time.time())
    timestamp = 0
    while True:
        try:
            response = get_api_answer(timestamp)
            homework, timestamp = check_response(response)
            message = parse_status(homework)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)
        else:
            if message is None:
                continue
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
