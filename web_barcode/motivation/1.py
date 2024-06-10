import pandas as pd
from sqlalchemy import create_engine

# Подключение к базе данных на удаленном сервере
engine = create_engine(
    'postgresql://databaseadmin:Up3psv8x@158.160.28.219:5432/innotreid')
# Чтение данных из Excel файла
print(engine.connect())
# df = pd.read_excel('путь_к_вашему_файлу.xlsx')
# # Загрузка данных в базу данных
# df.to_sql('название_таблицы', engine, if_exists='replace', index=False)
