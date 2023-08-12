import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

connection = psycopg2.connect(user=os.getenv('POSTGRES_USER'),
    # пароль, который указали при установке PostgreSQL
    password=os.getenv('POSTGRES_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB_NAME'))
cursor = connection.cursor()

postgreSQL_select_Query = '''SELECT article_marketplace, 
       SUM(CASE WHEN date_trunc('day', pub_date) = CURRENT_DATE THEN amount ELSE 0 END) AS today_quantity,
       SUM(CASE WHEN date_trunc('day', pub_date) = date_trunc('day', CURRENT_DATE - INTERVAL '1 day') THEN amount ELSE 0 END) AS yesterday_quantity
FROM database_yandex_stocks_innotreid
WHERE date_trunc('day', pub_date) IN (CURRENT_DATE, date_trunc('day', CURRENT_DATE - INTERVAL '1 day'))
GROUP BY article_marketplace
HAVING SUM(CASE WHEN date_trunc('day', pub_date) = CURRENT_DATE THEN amount ELSE 0 END) = 0
   AND SUM(CASE WHEN date_trunc('day', pub_date) = date_trunc('day', CURRENT_DATE - INTERVAL '1 day') THEN amount ELSE 0 END) > 0;'''
cursor.execute(postgreSQL_select_Query)

sender_data = cursor.fetchall()

for i in sender_data:
    print(f'Остаток на складе FBY артикула {i[0]} сегодня {i[1]}, вчера было {i[2]}')
