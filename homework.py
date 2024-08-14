import logging
import os
import requests
import time

from dotenv import load_dotenv
from exceptions import EndpointException, EmptyValueException
from http import HTTPStatus
from telebot import TeleBot, apihelper

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

logger = logging.getLogger(__name__)


def check_tokens():
    """Проверка доступности переменных.

    Проверка присвоения переменным значений из окружения
    в случае отсутствия ссылки на переменную, выполнение остановится.
    """
    empty_value = []
    for value in [
        ('PRACTICUM_TOKEN', PRACTICUM_TOKEN),
        ('TELEGRAM_TOKEN', TELEGRAM_TOKEN),
        ('TELEGRAM_CHAT_ID', TELEGRAM_CHAT_ID)
    ]:
        if value[1] is None:
            empty_value.append(value[0])
    if len(empty_value) > 0:
        logger.critical(
            f'Отсутствуют обязательные переменные окружения: {empty_value}. '
            'Программа принудительно остановлена.'
        )
        raise EmptyValueException(empty_value)


def send_message(bot, message):
    """Отправка сообщения пользователю.

    Отправка сообщений пользователю, логгируются
    действия успешной и неуспешной отправки.
    """
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except apihelper.ApiException as error:
        logger.error(f'Ошибка при отправке сообщения: {error}')
    else:
        logger.debug(f'Бот отправил сообщение: "{message}"')


def get_api_answer(timestamp):
    """Запрос к эндпоинту API.

    Проверка доступности эндпоинта и его ответа
    в случае его доступности.
    """
    payloads = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payloads)
    except requests.exceptions.RequestException:
        raise EndpointException(endpoint=ENDPOINT)
    status_code = response.status_code
    if status_code != HTTPStatus.OK:
        raise EndpointException(endpoint=ENDPOINT, code=status_code)
    return response.json()


def check_response(response):
    """Проверка полученного ответа от API.

    Проверка, что в ответе домашнее задание хранится в списке,
    извлечение данных о домашке и текущего времени, для обновления.
    """
    try:
        homework = response['homeworks']
    except KeyError as key:
        raise KeyError(f'В ответе API отсутствует ключ {key}')
    if not isinstance(homework, list):
        raise TypeError('Ответ с "homeworks" вернулся не в списке')
    elif not homework:
        logger.debug('Нового статуса домашней работы нет')
        return None
    else:
        return homework.pop()


def parse_status(homework):
    """Извлечение информации из ответа.

    Извлечение значений с названием домашней работы и её статусом,
    в случае если один из ключей недоступен, вызывается исключение.
    """
    try:
        status = homework['status']
        homework_name = homework['homework_name']
    except KeyError as error:
        message = (f'Ключ {error} отсутствует в ответе от API')
        raise KeyError(message)
    try:
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError as error:
        message = (f'Получен неожиданный статус домашней работы: {error}')
        raise KeyError(message)
    else:
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    check_tokens()
    bot = TeleBot(TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = None
    while True:
        try:
            response = get_api_answer(timestamp)
            try:
                timestamp = response['current_date']
            except KeyError:
                raise KeyError('В ответе API отсутствует временная метка')
            homework = check_response(response)
            if homework is not None:
                message = parse_status(homework)
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if last_message != message:
                send_message(bot, message)
                last_message = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
