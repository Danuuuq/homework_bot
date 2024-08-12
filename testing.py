import os

from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('TOKEN_YA')
TELEGRAM_TOKEN = os.getenv('TOKEN_TG')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

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