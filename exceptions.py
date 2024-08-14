"""
Исключения для телеграмм-бота.

Исключения для обработки следующих исключений:
1. Не созданы переменные окружения для работы проекта;
2. Проблемы с доступностью эндопоинта.
"""


class EmptyValueException(Exception):
    """Исключение для пустых переменных."""

    def __init__(self, tokens):
        self.tokens = tokens

    def __str__(self):
        return f'Отсутствуют обязательные переменные: {self.tokens}'


class EndpointException(Exception):
    """Исключение для ошибок с эндпоинтом."""

    def __init__(self, endpoint=None, code=None):
        self.endpoint = endpoint
        self.code = code

    def __str__(self):
        if self.code:
            return (
                f'Эндпоинт {self.endpoint} недоступен. '
                f'Код ответа API: {self.code}'
            )
        else:
            return f'Ошибка при обращении к эндпоинту {self.endpoint}.'
