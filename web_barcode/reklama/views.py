import os
from datetime import datetime, timedelta

from analytika_reklama.models import DailyCampaignParameters
from django.db.models import Max, Q
from django.shortcuts import redirect, render
from dotenv import load_dotenv
from price_system.models import Articles
from reklama.forms import FilterUrLicoForm
from reklama.models import OzonCampaign, UrLico
from reklama.periodic_tasks import ozon_status_one_campaign
from reklama.supplyment import create_articles_company, header_determinant

dotenv_path = os.path.join(os.path.dirname(
    __file__), '..', 'web_barcode', '.env')
load_dotenv(dotenv_path)


def ozon_ad_campaigns(request):
    """Отображает список рекламных компаний OZON и добавляет их"""
    company_list = OzonCampaign.objects.all().order_by('id')
    form = FilterUrLicoForm()
    # Словарь с текущим статусом рекламных кампаний вида {кампания: статус}
    campaign_status = {}
    if request.POST:
        request_data = request.POST
        if 'add_button' in request.POST:
            ur_lico_obj = UrLico.objects.get(id=request_data['ur_lico_name'])
            obj, created = OzonCampaign.objects.get_or_create(
                campaign_number=request_data['campaign_number'],
                ur_lico=ur_lico_obj
            )
            ozon_status_one_campaign(request_data['campaign_number'])

        elif 'del-button' in request.POST:
            OzonCampaign.objects.get(
                campaign_number=request_data['del-button']).delete()
        return redirect('ozon_ad_campaigns')

    context = {
        'data': company_list,
        'form': form,
        'campaign_status': campaign_status,
    }
    return render(request, 'reklama/ozon_ad_campaigns.html', context)
