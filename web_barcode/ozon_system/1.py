import datetime

today = datetime.date.today()
first_day_of_next_month = datetime.date(today.year, today.month+1, 1)
penultimate_day_of_month = first_day_of_next_month - datetime.timedelta(days=2)

# Выведет предпоследний день текущего месяца
print(penultimate_day_of_month.day)
