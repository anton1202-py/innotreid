from analytika_reklama.models import (CommonCampaignDescription,
                                      MainCampaignClusters,
                                      MainCampaignParameters)
from analytika_reklama.wb_supplyment import articles_for_keywords
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import ListView

from web_barcode.constants_file import (WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
                                        WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
                                        bot, header_wb_data_dict)


@login_required
def main_adv_info(request):
    """Отображает общую информацию о кампании"""
    page_name = 'Инфо о рекламных кампаний'
    # articles_for_keywords()
    campaign_list = CommonCampaignDescription.objects.all().order_by('id')

    context = {
        'page_name': page_name,
        'campaign_list': campaign_list,
        'WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT': WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
        'WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT': WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
    }
    return render(request, 'analytika_reklama/adv_campaign.html', context)


@login_required
def common_adv_statistic(request):
    """Отображает статистику кампаний"""
    page_name = 'Статитстика рекламных кампаний'
    campaign_info = MainCampaignParameters.objects.all().order_by('id')

    context = {
        'page_name': page_name,
        'campaign_info': campaign_info,
    }
    return render(request, 'analytika_reklama/adv_campaign_statistic.html', context)


@login_required
def adv_clusters(request):
    """Отображает кластеры кампаний"""
    page_name = 'Кластеры и ключевые слова кампаний'
    campaign_clusters = MainCampaignClusters.objects.filter(
        campaign__ur_lico=1).order_by('id')

    context = {
        'page_name': page_name,
        'campaign_clusters': campaign_clusters,
    }
    return render(request, 'analytika_reklama/adv_clusters.html', context)


class CampaignClustersView(ListView):
    model = CommonCampaignDescription
    template_name = 'analytika_reklama/adv_clusters.html'
    context_object_name = 'data'

    def __init__(self, *args, **kwargs):
        self.ur_lico = kwargs.pop('ur_lico', None)
        super(CampaignClustersView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(CampaignClustersView,
                        self).get_context_data(**kwargs)
        print(self.kwargs)
        cluster_data = MainCampaignClusters.objects.filter(
            campaign=self.kwargs['id'])
        context.update({
            'clusters_data': cluster_data,
            'page_name': f"Кластеры кампании {self.kwargs['id']}",
        })
        return context
