import asyncio
import json
import math
import os
import time
import traceback
from asyncio.log import logger

import requests
import telegram
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)


API_KEY_WB_IP = os.getenv('API_KEY_WB_IP')
YANDEX_IP_KEY = os.getenv('YANDEX_IP_KEY')
API_KEY_OZON_KARAVAEV = os.getenv('API_KEY_OZON_KARAVAEV')
CLIENT_ID_OZON_KARAVAEV = os.getenv('CLIENT_ID_OZON_KARAVAEV')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')

bot = telegram.Bot(token=TELEGRAM_TOKEN)

wb_headers_karavaev = {
    'Content-Type': 'application/json',
    'Authorization': API_KEY_WB_IP
}

ozon_headers_karavaev = {
    'Api-Key': API_KEY_OZON_KARAVAEV,
    'Content-Type': 'application/json',
    'Client-Id': CLIENT_ID_OZON_KARAVAEV
}

yandex_headers_karavaev = {
    'Authorization': YANDEX_IP_KEY,
}


def try_except_decorator(requests_per_interval, interval_seconds, max_attempts=50, max_delay=120):
    def decorator(func):
        async def wrapper(instance, *args, **kwargs):
            if not hasattr(instance, '_api_call_state'):
                instance._api_call_state = {}

            method_name = func.name
            if method_name not in instance._api_call_state:
                instance._api_call_state[method_name] = {
                    '_last_query_time': 0,
                    '_current_pause': interval_seconds / requests_per_interval,
                    '_attempts': 0,
                    '_first_request': True
                }

            state = instance._api_call_state[method_name]
            while state['_attempts'] < max_attempts:
                current_time = time.time()
                time_since_last_query = current_time - \
                    state['_last_query_time']
                time_to_wait = max(
                    state['_current_pause'] - time_since_last_query, 0)
                if state['_first_request']:
                    logger.debug(
                        f'Пауза между запросами: {time_to_wait} секунд')
                    await asyncio.sleep(time_to_wait)
                    state['_first_request'] = False

                try:
                    result = await func(instance, *args, **kwargs)
                    state['_last_query_time'] = time.time()
                    state['_current_pause'] = (
                        interval_seconds / requests_per_interval + state['_current_pause']) / 2
                    # Сброс попыток после успешного выполнения
                    state['_attempts'] = 0
                    return result
                except ApiForbiddenError:
                    raise
                except TooManyRequests:
                    state['_attempts'] += 1
                    state['_current_pause'] = min(
                        state['_current_pause'] * 2, max_delay)
                    if state['_attempts'] >= max_attempts:
                        raise
                except Exception as e:
                    logger.error(f'Ошибка запроса к wb: {e}', e)
                    state['_attempts'] += 1
                    state['_current_pause'] = min(
                        state['_current_pause'] * 2, max_delay)
                    if state['_attempts'] >= max_attempts:
                        raise e
        return wrapper
    return decorator


async def requests(self, session, method, url, data=None, json_data=None, headers=None, ):
    async with session.request(method, url, data=data, headers=headers, json=json_data) as response:
        try:
            logger.debug(f'Запрос к {url} выполнен. Статус: {response.status}')
            response.raise_for_status()
        except aiohttp.ClientResponseError as e:  # Предполагая использование aiohttp
            if e.status == 401:
                raise exceptions.ApiForbiddenError(
                    'Неверный API ключ', wb_user_cabinet=self._wb_user_cabinet) from e
            if e.status == 429:
                logger.error(f'Превышен лимит запросов к API. Ошибка: {url}')
                raise exceptions.TooManyRequests from e
            else:
                #
                raise exceptions.UnknownApiRequestError(e) from e
        except Exception as e:
            raise exceptions.UnknownApiRequestError(e) from e
        # Если код не в блоке except, значит ответ был успешным (статус 200-299)
        text = await response.text()
        if text:
            json_answer = json.loads(text)
            if isinstance(json_answer, dict):
                if code := json_answer.get('code'):
                    raise exceptions.ApiErrorWithCode(code,
                                                      json_answer.get('message'), json_answer.get('rejection'))
        return text
