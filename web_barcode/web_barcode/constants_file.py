import os

import dropbox
import telegram
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)

REFRESH_TOKEN_DB = os.getenv('REFRESH_TOKEN_DB')
APP_KEY_DB = os.getenv('APP_KEY_DB')
APP_SECRET_DB = os.getenv('APP_SECRET_DB')

API_KEY_WB_IP = os.getenv('API_KEY_WB_IP')

EMAIL_ADDRESS_FROM = os.getenv('EMAIL_ADDRESS_FROM')
EMAIL_ADDRESS_FROM_PASSWORD = os.getenv('EMAIL_ADDRESS_FROM_PASSWORD')
EMAIL_ADDRESS_TO = os.getenv('EMAIL_ADDRESS_TO')
POST_SERVER = os.getenv('POST_SERVER')
POST_PORT = os.getenv('POST_PORT')

API_KEY_OZON_KARAVAEV = os.getenv('API_KEY_OZON_KARAVAEV')
CLIENT_ID_OZON_KARAVAEV = os.getenv('CLIENT_ID_OZON_KARAVAEV')

OZON_IP_API_TOKEN = os.getenv('OZON_IP__API_TOKEN')
OZON_OOO_API_TOKEN = os.getenv('OZON_OOO_API_TOKEN')
OZON_OOO_CLIENT_ID = os.getenv('OZON_OOO_CLIENT_ID')

OZON_GRAMOTY_API_TOKEN = os.getenv('OZON_GRAMOTY_API_TOKEN')
OZON_GRAMOTY_CLIENT_ID = os.getenv('OZON_GRAMOTY_CLIENT_ID')

OZON_IP_ADV_CLIENT_ACCESS_ID = os.getenv('OZON_IP_ADV_CLIENT_ACCESS_ID')
OZON_IP_ADV_CLIENT_SECRET = os.getenv('OZON_IP_ADV_CLIENT_SECRET')

OZON_OOO_ADV_CLIENT_ACCESS_ID = os.getenv('OZON_OOO_ADV_CLIENT_ACCESS_ID')
OZON_OOO_ADV_CLIENT_SECRET = os.getenv('OZON_OOO_ADV_CLIENT_SECRET')

OZON_GRAMOTY_ADV_CLIENT_ACCESS_ID = os.getenv(
    'OZON_GRAMOTY_ADV_CLIENT_ACCESS_ID')
OZON_GRAMOTY_ADV_CLIENT_SECRET = os.getenv('OZON_GRAMOTY_ADV_CLIENT_SECRET')


WB_OOO_API_KEY = os.getenv('WB_OOO_API_KEY')
WB_API_KEY_INNOTREID = os.getenv('API_KEY_WB_INNOTREID')

API_KEY_WB_GRAMOTY = os.getenv('API_KEY_WB_GRAMOTY')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID_ADMIN = os.getenv('CHAT_ID_ADMIN')
CHAT_ID_MANAGER = os.getenv('CHAT_ID_MANAGER')
CHAT_ID_EU = os.getenv('CHAT_ID_EU')
CHAT_ID_AN = os.getenv('CHAT_ID_AN')

YANDEX_OOO_KEY = os.getenv('YANDEX_OOO_KEY')
YANDEX_IP_KEY = os.getenv('YANDEX_IP_KEY')
YANDEX_GRAMOTY_KEY = os.getenv('YANDEX_GRAMOTY_KEY')

YANDEX_BUSINESS_ID_IP = os.getenv('YANDEX_BUSINESS_ID_IP')
YANDEX_BUSINESS_ID_OOO = os.getenv('YANDEX_BUSINESS_ID_OOO')
YANDEX_BUSINESS_ID_GRAMOTY = os.getenv('YANDEX_BUSINESS_ID_GRAMOTY')

YANDEX_OOO_FBY_CAMPAIGN_ID = os.getenv('YANDEX_OOO_FBY_CAMPAIGN_ID')
YANDEX_OOO_FBS_CAMPAIGN_ID = os.getenv('YANDEX_OOO_FBS_CAMPAIGN_ID')
YANDEX_IP_FBY_CAMPAIGN_ID = os.getenv('YANDEX_IP_FBY_CAMPAIGN_ID')
YANDEX_IP_FBS_CAMPAIGN_ID = os.getenv('YANDEX_IP_FBS_CAMPAIGN_ID')
YANDEX_GRAMOTY_FBY_CAMPAIGN_ID = os.getenv('YANDEX_GRAMOTY_FBY_CAMPAIGN_ID')
YANDEX_GRAMOTY_FBS_CAMPAIGN_ID = os.getenv('YANDEX_GRAMOTY_FBS_CAMPAIGN_ID')

dbx_db = dropbox.Dropbox(oauth2_refresh_token=REFRESH_TOKEN_DB,
                         app_key=APP_KEY_DB,
                         app_secret=APP_SECRET_DB)

wb_headers_karavaev = {
    'Content-Type': 'application/json',
    'Authorization': API_KEY_WB_IP
}
wb_headers_ooo = {
    'Content-Type': 'application/json',
    'Authorization': WB_OOO_API_KEY
}
wb_headers_gramoty = {
    'Content-Type': 'application/json',
    'Authorization': API_KEY_WB_GRAMOTY
}

wb_data_ooo_headers = {
    'Content-Type': 'application/json',
    'Authorization': WB_API_KEY_INNOTREID
}

ozon_headers_karavaev = {
    'Api-Key': API_KEY_OZON_KARAVAEV,
    'Content-Type': 'application/json',
    'Client-Id': CLIENT_ID_OZON_KARAVAEV
}
ozon_headers_ooo = {
    'Api-Key': OZON_OOO_API_TOKEN,
    'Content-Type': 'application/json',
    'Client-Id': OZON_OOO_CLIENT_ID
}
ozon_headers_gramoty = {
    'Api-Key': OZON_GRAMOTY_API_TOKEN,
    'Content-Type': 'application/json',
    'Client-Id': OZON_GRAMOTY_CLIENT_ID
}

yandex_headers_karavaev = {
    'Authorization': YANDEX_IP_KEY,
}
yandex_headers_ooo = {
    'Authorization': YANDEX_OOO_KEY,
}
yandex_headers_gramoty = {
    'Authorization': YANDEX_GRAMOTY_KEY,
}

header_wb_dict = {
    'ООО Иннотрейд': wb_headers_ooo,
    'ИП Караваев': wb_headers_karavaev,
    'ООО Мастерская чудес': wb_headers_gramoty
}


header_ozon_dict = {
    'ООО Иннотрейд': ozon_headers_ooo,
    'ИП Караваев': ozon_headers_karavaev,
    'ООО Мастерская чудес': ozon_headers_gramoty
}
ozon_adv_client_access_id_dict = {
    'ООО Иннотрейд': OZON_OOO_ADV_CLIENT_ACCESS_ID,
    'ИП Караваев': OZON_IP_ADV_CLIENT_ACCESS_ID,
    'ООО Мастерская чудес': OZON_GRAMOTY_ADV_CLIENT_ACCESS_ID
}

ozon_adv_client_secret_dict = {
    'ООО Иннотрейд': OZON_OOO_ADV_CLIENT_SECRET,
    'ИП Караваев': OZON_IP_ADV_CLIENT_SECRET,
    'ООО Мастерская чудес': OZON_GRAMOTY_ADV_CLIENT_SECRET
}

ozon_api_token_dict = {
    'ООО Иннотрейд': OZON_OOO_API_TOKEN,
    'ИП Караваев': OZON_IP_API_TOKEN,
    'ООО Мастерская чудес': OZON_GRAMOTY_API_TOKEN
}


header_yandex_dict = {
    'ООО Иннотрейд': yandex_headers_ooo,
    'ИП Караваев': yandex_headers_karavaev,
    'ООО Мастерская чудес': yandex_headers_gramoty
}

yandex_business_id_dict = {
    'ООО Иннотрейд': YANDEX_BUSINESS_ID_OOO,
    'ИП Караваев': YANDEX_BUSINESS_ID_IP,
    'ООО Мастерская чудес': YANDEX_BUSINESS_ID_GRAMOTY
}

yandex_fbs_campaign_id_dict = {
    'ООО Иннотрейд': YANDEX_OOO_FBS_CAMPAIGN_ID,
    'ИП Караваев': YANDEX_IP_FBS_CAMPAIGN_ID,
    'ООО Мастерская чудес': YANDEX_GRAMOTY_FBS_CAMPAIGN_ID
}
yandex_fby_campaign_id_dict = {
    'ООО Иннотрейд': YANDEX_OOO_FBY_CAMPAIGN_ID,
    'ИП Караваев': YANDEX_IP_FBY_CAMPAIGN_ID,
    'ООО Мастерская чудес': YANDEX_GRAMOTY_FBY_CAMPAIGN_ID
}

yandex_fbs_warehouse_id_dict = {
    'ООО Иннотрейд': 250643,
    'ИП Караваев': 938511
}
yandex_campaign_id_dict_list = [
    yandex_fbs_campaign_id_dict, yandex_fby_campaign_id_dict]

spp_group_list = [CHAT_ID_ADMIN, CHAT_ID_EU]

ur_lico_list_for_yandex_fbs_balance = ['ООО Иннотрейд', 'ИП Караваев']
admins_chat_id_list = [CHAT_ID_ADMIN, CHAT_ID_EU]
bot = telegram.Bot(token=TELEGRAM_TOKEN)


WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT = {
    -1: 'в процессе удаления',
    4: 'готова к запуску',
    7: 'завершена',
    8: 'отказался',
    9: 'идут показы',
    11: 'на паузе'
}

WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT = {
    4: 'в каталоге',
    5: 'в карточке товара',
    6: 'в поиске',
    7: 'в рекомендациях на главной странице',
    8: 'автоматическая',
    9: 'поиск + каталог'
}


campaign_budget_users_list = [CHAT_ID_ADMIN, CHAT_ID_EU]

SUBJECT_REKLAMA_ID_DICT = {
    'Ночник': 1673,
    'Светильник': 330,
    'Грамота/диплом': 3618,
    'Файл вкладыш': 3169
}
