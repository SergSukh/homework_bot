import os
import sys
import requests
import logging
import time
import telegram

from dotenv import load_dotenv
import exception


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
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
    logger.info('the message has been sent to the addressee')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except exception.BotSendMessageError:
        logger.debug('message don`t send')
    return


def get_api_answer(current_timestamp):
    """Опрашиваем API, оцениваем дотсупность и получаем ответ."""
    keys_to_check = ['homeworks', 'current_date']
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        raise exception.API_Status
    logger.info('get api answer success in module <get_api_answer>')
    response = response.json()
    for key in keys_to_check:
        if key not in response:
            logger.debug(f'api answer dictionary haven`t key {key}')

    return response


def check_response(response):
    """Проверяем ответ сервера и готовим данные для финальной обработки."""
    """Проверка ответа на список словарей."""
    try:
        homeworks = response['homeworks']
        assert type(homeworks) == list
    except KeyError:
        message = 'Key Error in dictionary'
        logger.debug(message)
    except TypeError:
        message = 'response -Not list '
        logger.debug(message)
        return message
    if type(len(homeworks)) != int:
        raise TypeError
    if not homeworks:
        message = ('The homework is empty')
        logger.info(message)
        return message
    elif homeworks == []:
        message = ('The status of homework has empty list')
        logger.info(message)
        return 'Статус проверки работы на сервере не изменился'

    """Опрос каждого словаря из списка."""
    message = ''
    for i in range(len(homeworks)):
        try:
            homework = homeworks[i]
            message += parse_status(homework)
        except KeyError:
            logger.debug('Key Error in dictionary')
            message = 'Key Error in dictionary'
            break
        except TypeError:
            logger.debug('Type Error in dictionary')
            message = 'Type Error in dictionary'
            break
    return message


def parse_status(homework):
    """Проверка статуса работы, определяем переменные."""
    keys_to_check = ['homework_name', 'status']
    message = ''
    """Проверяем наличие соответствующих переменных в словаре."""
    for key in keys_to_check:
        if key not in homework:
            raise KeyError
    homework_name = homework['homework_name']
    if homework_name is None:
        raise exception.HomeWorkKeyError
    homework_status = homework['status']
    if (homework_status is None) or (homework_status not in HOMEWORK_STATUSES):
        raise KeyError
    else:
        verdict = HOMEWORK_STATUSES[homework_status] or homework_status
        message = ('Изменился статус проверки работы',
                   f'"{homework_name}". {verdict}')
    return message


def check_tokens():
    """Для проверки используем os.environ в случае ошибки - False."""
    env_vars = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    check = False
    try:
        for v in env_vars:
            os.environ.get(v)
        assert PRACTICUM_TOKEN is not None
        assert TELEGRAM_TOKEN is not None
        assert TELEGRAM_CHAT_ID is not None
    except Exception as e:
        logger.exception(
            f'{e} check the variables the variable is not defined')
    else:
        logger.info('Tokens loaded successfully.')
        check = True
    try:
        assert check is True
    except Exception as e:
        logger.exception(f'{e} Tokens isn`t loaded..')
        return False
    return True


def main():
    """Основная логика работы бота."""
    """Определяем наличие всех переменных."""
    try:
        check = check_tokens()
    except AssertionError:
        logger.critical('Security check failed')
    else:
        logger.info('Loaded success')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    prev_message = ''

    """А тут бесконечный циклб прерывается только в случае токенов."""
    while True:
        if not check:
            break
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response['current_date']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
        else:
            message = check_response(response)
        if message != prev_message and message != '':
            send_message(bot, message)
            prev_message = message
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
