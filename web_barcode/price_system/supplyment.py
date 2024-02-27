import datetime
import os
from datetime import date

from django.http import FileResponse, HttpResponse, JsonResponse
from openpyxl import Workbook
from openpyxl.reader.excel import load_workbook
from openpyxl.styles import Alignment, Border, PatternFill, Side

from .models import ArticleGroup, Articles, Groups


def excel_creating_mod(data):
    """Создает и скачивает excel файл"""
    # Создаем DataFrame из данных
    wb = Workbook()
    # Получаем активный лист
    ws = wb.active

    # Заполняем лист данными
    for row, item in enumerate(data, start=2):
        ws.cell(row=row, column=1, value=str(item.common_article))
        ws.cell(row=row, column=2, value=str(item.group))
    # Устанавливаем заголовки столбцов
    ws.cell(row=1, column=1, value='Артикул')
    ws.cell(row=1, column=2, value='Группа')

    al = Alignment(horizontal="center",
                   vertical="center")
    al_left = Alignment(horizontal="left",
                        vertical="center")
    al2 = Alignment(vertical="center", wrap_text=True)
    thin = Side(border_style="thin", color="000000")
    thick = Side(border_style="medium", color="000000")
    pattern = PatternFill('solid', fgColor="fcff52")

    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 10

    for i in range(len(data)+1):
        for c in ws[f'A{i+1}:I{i+1}']:
            for i in range(9):
                c[i].border = Border(top=thin, left=thin,
                                     bottom=thin, right=thin)
                c[i].alignment = al_left

    # Сохраняем книгу Excel в память
    response = HttpResponse(content_type='application/xlsx')
    response['Content-Disposition'] = 'attachment; filename=table.xlsx'
    wb.save(response)

    return response


def excel_import_data(xlsx_file):
    """Импортирует данные о группе артикула из Excel"""
    # xlsx_file = request.FILES['xlsx_file']
    workbook = load_workbook(filename=xlsx_file, read_only=True)
    worksheet = workbook.active
    # Читаем файл построчно и создаем объекты.
    for row in range(1, len(list(worksheet.rows))):
        if list(worksheet.rows)[row][1].value == 'None' or list(worksheet.rows)[row][1].value == '':
            continue
        else:
            print(list(worksheet.rows)[row][1].value)
            new_obj = ArticleGroup.objects.filter(
                common_article=Articles.objects.get(
                    common_article=list(worksheet.rows)[row][0].value)
            ).update(group=Groups.objects.get(name=list(worksheet.rows)[row][1].value))
