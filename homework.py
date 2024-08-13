import logging
import os
import requests
import time

from dotenv import load_dotenv
from exceptions import EndpointException, EmptyValueException
from telebot import TeleBot

load_dotenv()

PRACTICUM_TOKEN = os.getenv('TOKEN_YA')
TELEGRAM_TOKEN = os.getenv('TOKEN_TG')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'httpss://practicum.yandex.ru/api/user_api/homework_statuses/'
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


def check_tokens():
    """Проверка доступности переменных.

    Проверка присвоения переменным значений из окружения
    в случае отсутствия ссылки на переменную, выполнение остановится.
    """
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
            raise EmptyValueException(value[0])


def send_message(bot, message):
    """Отправка сообщения пользователю.

    Отправка сообщений пользователю, логгируются
    действия успешной и неуспешной отправки.
    """
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logger.error(f'Ошибка при отправке сообщения {error}')
    else:
        logger.debug(f'Бот отправил сообщение: "{message}"')


def get_api_answer(timestamp):
    """Запрос к эндпоинту API.

    Проверка доступности эндпоинта и его ответа
    в случае его доступности.
    """
    payloads = {'from_date': timestamp}
    try:
        status_code = None
        response = requests.get(ENDPOINT, headers=HEADERS, params=payloads)
        status_code = response.status_code
        if status_code != 200:
            raise
    except Exception:
        raise EndpointException(endpoint=ENDPOINT, code=status_code)
    else:
        return response.json()


def check_response(response):
    """Проверка полученного ответа от API.

    Проверка, что в ответе домашнее задание в списке хранится,
    извлечение данных о домашке и текущего времени, для обновления.
    """
    try:
        homework = response['homeworks']
    except KeyError:
        raise KeyError('В ответе API отсутствует ключ "homeworks"')
    else:
        current_date = response['current_date']
        if not isinstance(homework, list):
            raise TypeError('Ответ с "homeworks" вернулся не в списке')
        elif not homework:
            logger.debug('Нового статуса домашней работы нет')
            return None, current_date
        else:
            return homework.pop(), current_date


def parse_status(homework):
    """Извлечение информации из ответа.

    Извлечение значений с названием домашней работы и её статусом,
    в случае если один из ключей недоступен, вызывается исключение.
    """
    try:
        status = homework['status']
        homework_name = homework['homework_name']
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError:
        message = (
            'Один из ключей словаря homework или HOMEWORK_VERDICTS недоступен'
        )
        logger.error(message)
        raise KeyError
    else:
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            homework, timestamp = check_response(response)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
        else:
            if homework is not None:
                message = parse_status(homework)
                send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
