import datetime

# Получаем текущую дату
today = datetime.datetime.now()

print(today.hour)

# Используем метод strftime() для форматирования даты и вывода дня недели
day_of_week = today.strftime('%A')

print("Сегодня " + day_of_week)
