import asyncio

from django.shortcuts import render

from web_barcode.ozon_system.supplyment import \
    delete_ozon_articles_with_low_price_current_ur_lico
from web_barcode.price_system.models import Groups


async def groups_view(request, ur_lico):
    """Отвечает за Отображение ценовых групп"""
    data = Groups.objects.filter(company=ur_lico).order_by('id')
    loop = asyncio.get_event_loop()

    if 'delete_low_price_button' in request.POST:
        # Удаляем артикулы из акции, если цена в акции ниже,
        # чем установленная минимальная цена.
        # delete_ozon_articles_with_low_price_current_ur_lico(ur_lico)
        await loop.run_in_executor(None, delete_ozon_articles_with_low_price_current_ur_lico, ur_lico)

    context = {
        'data': data,
        'ur_lico': ur_lico,
    }
    return render(request, 'price_system/groups.html', context)


def ip_groups_view(request):
    """Отвечает за Отображение ценовых групп ИП"""
    async def wrapper():
        return await groups_view(request, 'ИП Караваев')
    return wrapper()
