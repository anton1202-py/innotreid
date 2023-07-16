import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT



import psycopg2

def connect_to_postgres():
    try:
        # Подключение к базе данных PostgreSQL
        conn = psycopg2.connect(
            host="51.250.110.190",
            database="namefile",
            user="nameadmin",
            password="djkm714"
        )
        
        # Создание курсора
        cursor = conn.cursor()
        #create_table_query = '''
        #    CREATE TABLE namenumbers (
        #    numb INT NOT NULL
        #    )
        #'''
        #cursor.execute(create_table_query)
        #conn.commit()
        # Выполнение SQL-запроса
        cursor.execute('''INSERT INTO namenumbers VALUES (15660);''')
        #cursor.execute('''SELECT * FROM namenumbers;''')
        # Получение результатов запроса
        #rows = cursor.fetchall()
        
        # Вывод результатов
        #for row in rows:
        #    print(row)
        #
        # Закрытие курсора и соединения
        conn.commit()
        cursor.close()
        conn.close()
        
    except (Exception, psycopg2.Error) as error:
        print("Ошибка при подключении к PostgreSQL:", error)

connect_to_postgres()