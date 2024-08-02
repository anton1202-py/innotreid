my_dict = {1: [1, 2, 3], 2: [2, 1, 3], 3: [3, 3, 2]}

# Сортировка словаря по второму элементу во внутренних списках
sorted_dict = dict(sorted(my_dict.items(), key=lambda item: item[1][1]))

print(sorted_dict)
