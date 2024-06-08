from analytika_reklama.models import (CommonCampaignDescription,
                                      DailyCampaignParameters,
                                      MainCampaignClusters,
                                      MainCampaignParameters)
from analytika_reklama.periodic_tasks import (
    add_campaigns_statistic_to_db, add_info_to_db_about_all_campaigns,
    get_clusters_statistic_for_autocampaign,
    get_searchcampaign_keywords_statistic)
from analytika_reklama.wb_supplyment import articles_for_keywords
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import ListView
from reklama.models import UrLico

from web_barcode.constants_file import (WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
                                        WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
                                        bot, header_wb_data_dict)


@login_required
def main_adv_info(request):
    """Отображает общую информацию о кампании"""
    page_name = 'Инфо о рекламных кампаний'
    # articles_for_keywords()
    campaign_list = CommonCampaignDescription.objects.filter(
        ur_lico=1).order_by('id')
    ur_lico_data = UrLico.objects.all()
    if request.POST:
        if 'campaign_number' in request.POST:
            campaign_number = request.POST['campaign_number']
            campaign_list = CommonCampaignDescription.objects.filter(
                campaign_number=campaign_number).order_by('id')
        if 'ur_lico_select' in request.POST:
            filter_ur_lico = request.POST['ur_lico_select']
            campaign_list = CommonCampaignDescription.objects.filter(
                ur_lico=int(filter_ur_lico)).order_by('id')
    context = {
        'page_name': page_name,
        'campaign_list': campaign_list,
        'ur_lico_data': ur_lico_data,
        'WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT': WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
        'WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT': WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
    }
    return render(request, 'analytika_reklama/adv_campaign.html', context)


@login_required
def common_adv_statistic(request):
    """Отображает статистику кампаний"""
    page_name = 'Статитстика рекламных кампаний'
    campaign_info = MainCampaignParameters.objects.all().order_by('id')
    ur_lico_data = UrLico.objects.all()
    if request.POST:
        if 'campaign_number' in request.POST:
            campaign_number = request.POST['campaign_number']
            campaign_info = MainCampaignParameters.objects.filter(
                campaign__campaign_number=campaign_number).order_by('id')
        if 'ur_lico_select' in request.POST:
            filter_ur_lico = request.POST['ur_lico_select']
            campaign_info = MainCampaignParameters.objects.filter(
                campaign__ur_lico=int(filter_ur_lico)).order_by('id')
    context = {
        'page_name': page_name,
        'campaign_info': campaign_info,
        'ur_lico_data': ur_lico_data,
        'WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT': WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
        'WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT': WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
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
        # print(self.kwargs['ur_lico'])
        campaign_object = CommonCampaignDescription.objects.get(
            id=self.kwargs['id'])
        cluster_data = MainCampaignClusters.objects.filter(
            campaign=self.kwargs['id'])
        context.update({
            'clusters_data': cluster_data,
            'page_name': f"Кластеры кампании: {campaign_object.campaign_name} ({campaign_object.campaign_number})",
        })
        return context

    def get_queryset(self):
        return MainCampaignClusters.objects.filter(
            campaign=self.kwargs['id'])


class CampaignDailyStatisticView(ListView):
    model = CommonCampaignDescription
    template_name = 'analytika_reklama/adv_campaign_daily_statistic.html'
    context_object_name = 'data'

    def __init__(self, *args, **kwargs):
        self.ur_lico = kwargs.pop('ur_lico', None)
        super(CampaignDailyStatisticView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(CampaignDailyStatisticView,
                        self).get_context_data(**kwargs)
        # print(self.kwargs['ur_lico'])
        campaign_object = CommonCampaignDescription.objects.get(
            id=self.kwargs['id'])
        statistic_data = DailyCampaignParameters.objects.filter(
            campaign=self.kwargs['id'])
        print(self.kwargs['id'])
        context.update({
            'statistic_data': statistic_data,
            'page_name': f"Статистика кампании: {campaign_object.campaign_name} ({campaign_object.campaign_number})",
            'WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT': WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
            'WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT': WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
        })
        return context

    def get_queryset(self):
        print(DailyCampaignParameters.objects.filter(
            campaign=self.kwargs['id']))
        return DailyCampaignParameters.objects.filter(
            campaign=self.kwargs['id'])
