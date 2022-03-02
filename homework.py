import os
import sys
import requests
import logging
import time

from http import HTTPStatus
from dotenv import load_dotenv
from exception import API_Status, BotSendMessageError, HomeWorkKeyError
import telegram

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
MESSEGE_MAX_LENGTH = 4095
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправка сообщений ботом."""
    try:
        message = message[:MESSEGE_MAX_LENGTH]
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('the message has been sent to the addressee')
        send = True
    except BotSendMessageError:
        send = False
        logger.debug('message don`t send')
    return send


def get_api_answer(current_timestamp):
    """Опрашиваем API, оцениваем дотсупность и получаем ответ."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
        status_code = response.status_code
        message = HTTPStatus(status_code).description
        if response.status_code != HTTPStatus.OK.value:
            logger.exception(message)
            raise API_Status(message)
    except Exception as error:
        error_message = HTTPStatus(status_code).description
        logger.exception(error)
        raise API_Status(error_message)
    response = response.json()
    return response


def check_response(response):
    """Проверяем ответ сервера и готовим данные для финальной обработки."""
    keys_to_check = ['homeworks', 'current_date']
    """Проверка ответа на список словарей."""
    for key in keys_to_check:
        if key not in response:
            logger.debug(f'api answer dictionary haven`t key {key}')

    try:
        homeworks = response['homeworks']
    except KeyError:
        message = 'Key Error in dictionary'
        logger.debug(message)
        raise KeyError(message)
    if not isinstance(homeworks, list):
        message = 'response -Not list '
        logger.debug(message)
        raise TypeError(message)
    if not homeworks or homeworks == []:
        message = 'The homework is empty'
        return message

    """Опрос каждого словаря из списка."""
    message = ''
    for hw in range(len(homeworks)):
        try:
            homework = homeworks[hw]
            message += parse_status(homework)
        except Exception as error:
            message += f'For homework[{hw}] {error} in list dictionary'
            logger.debug(message)
    return message


def parse_status(homework):
    """Проверка статуса работы, определяем переменные."""
    keys_to_check = ['homework_name', 'status']
    message = ''
    """Проверяем наличие соответствующих переменных в словаре."""
    for key in keys_to_check:
        if key not in homework:
            raise KeyError
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise HomeWorkKeyError
    homework_status = homework['status']
    if (homework_status is None) or (homework_status not in HOMEWORK_STATUSES):
        raise KeyError
    verdict = HOMEWORK_STATUSES[homework_status] or homework_status
    message = f'Изменился статус проверки работы "{homework_name}". {verdict}'
    return message


def check_tokens():
    """Для проверки используем os.environ в случае ошибки - False."""
    check = False
    try:
        if ((PRACTICUM_TOKEN is None)
           or (TELEGRAM_TOKEN is None)
           or (TELEGRAM_CHAT_ID is None)):
            logger.critical('Some variable is missing. System Error')
            raise SystemError
    except Exception as e:
        logger.exception(
            f'{e} check the variables the variable is not defined')
    else:
        logger.info('Tokens loaded successfully.')
        check = True
    if check:
        return True
    logger.exception('Tokens isn`t loaded..')
    return False


def main():
    """Основная логика работы бота."""
    """Запрашиваем наличие всех переменных."""
    if not check_tokens():
        logger.critical('Security check failed')
        raise SystemExit
    logger.info('Loaded success')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    prev_message = ''
    prev_error_message = ''

    """А тут бесконечный цикл."""
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response['current_date']
            message = check_response(response)
            if message != prev_message and message != '':
                if send_message(bot, message):
                    prev_message = message
        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            logger.exception(error_message)
            if error_message != prev_error_message:
                if send_message(bot, error_message):
                    prev_error_message = error_message
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
