from analytika_reklama.models import (CommonCampaignDescription,
                                      DailyCampaignParameters, KeywordPhrase,
                                      MainArticleExcluded, MainArticleKeyWords,
                                      MainCampaignClusters,
                                      MainCampaignParameters,
                                      StatisticCampaignKeywordPhrase)
from analytika_reklama.periodic_tasks import (
    add_campaigns_statistic_to_db, get_auto_campaign_statistic_common_data,
    get_clusters_statistic_for_autocampaign,
    get_searchcampaign_keywords_statistic)
from create_reklama.models import CreatedCampaign
from django.contrib.auth.decorators import login_required
from django.db.models import (Case, Count, ExpressionWrapper, F, FloatField,
                              Sum, When)
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.views.generic import ListView
from price_system.models import Articles
from reklama.models import UrLico

from web_barcode.constants_file import (WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
                                        WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
                                        bot, header_wb_data_dict)


@login_required
def main_adv_info(request):
    """Отображает общую информацию о кампании"""
    page_name = 'Инфо о рекламных кампаний'

    campaign_list = CreatedCampaign.objects.filter(
        ur_lico=1).order_by('id')
    ur_lico_data = UrLico.objects.all()
    if request.POST:
        if 'campaign_number' in request.POST:
            campaign_number = request.POST['campaign_number']
            campaign_list = CreatedCampaign.objects.filter(
                campaign_number=campaign_number).order_by('id')
        if 'ur_lico_select' in request.POST:
            filter_ur_lico = request.POST['ur_lico_select']
            campaign_list = CreatedCampaign.objects.filter(
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
def keyword_statistic_info(request):
    """Отображает статистику ключевых фраз"""
    page_name = 'Статистика ключевых фраз'

    keyword_stats = StatisticCampaignKeywordPhrase.objects.values('keyword__phrase').annotate(
        keyword_obj=F('keyword'),
        total_views=Sum('views'),
        total_clicks=Sum('clicks'),
        total_summ=Sum('summ'),
        click_to_view_ratio=ExpressionWrapper(
            F('total_clicks') * 100 / Case(
                When(total_views=0, then=1),
                default=F('total_views'),
                output_field=FloatField()
            ),
            output_field=FloatField()
        )
    ).filter(total_views__gt=300).order_by('-total_views')

    context = {
        'page_name': page_name,
        'keyword_stats': keyword_stats
    }
    return render(request, 'analytika_reklama/adv_kwstatistic.html', context)


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
    model = CreatedCampaign
    template_name = 'analytika_reklama/adv_clusters.html'
    context_object_name = 'data'

    def __init__(self, *args, **kwargs):
        self.ur_lico = kwargs.pop('ur_lico', None)
        super(CampaignClustersView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(CampaignClustersView,
                        self).get_context_data(**kwargs)
        campaign_object = CreatedCampaign.objects.get(
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
    model = CreatedCampaign
    template_name = 'analytika_reklama/adv_campaign_daily_statistic.html'
    context_object_name = 'data'

    def __init__(self, *args, **kwargs):
        self.ur_lico = kwargs.pop('ur_lico', None)
        super(CampaignDailyStatisticView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(CampaignDailyStatisticView,
                        self).get_context_data(**kwargs)
        campaign_object = CreatedCampaign.objects.get(
            id=self.kwargs['id'])
        statistic_data = DailyCampaignParameters.objects.filter(
            campaign=self.kwargs['id'])
        context.update({
            'statistic_data': statistic_data,
            'page_name': f"Статистика кампании: {campaign_object.campaign_name} ({campaign_object.campaign_number})",
            'WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT': WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
            'WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT': WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
        })
        return context

    def get_queryset(self):
        return DailyCampaignParameters.objects.filter(
            campaign=self.kwargs['id'])


@login_required
def articles_words_main_info(request):
    """Отображает общую статистику наличия ключевых и минус фраз у артикула"""
    page_name = 'Наличие ключевых фраз артикула'
    article_key_words_info = {}
    common_keywords_info = MainArticleKeyWords.objects.values(
        'article').annotate(cluster_count=Count('cluster')).order_by('-cluster_count')

    common_excludes_info = MainArticleExcluded.objects.values(
        'article').annotate(excluded_count=Count('excluded'))
    for data in common_keywords_info:
        article_key_words_info[Articles.objects.get(id=data['article'])] = {
            'cluster_count': data['cluster_count']}
    for data in common_excludes_info:
        article_key_words_info[Articles.objects.get(id=data['article'])
                               ]['excluded_count'] = data['excluded_count']
    context = {
        'page_name': page_name,
        'article_key_words_info': article_key_words_info,
        'excluded_count': 'excluded_count',
        'cluster_count': 'cluster_count'
    }
    return render(request, 'analytika_reklama/adv_article_words_info.html', context)


class ArticleClustersView(ListView):
    model = MainArticleKeyWords
    template_name = 'analytika_reklama/article_clusters.html'
    context_object_name = 'data'

    def __init__(self, *args, **kwargs):
        self.ur_lico = kwargs.pop('ur_lico', None)
        super(ArticleClustersView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ArticleClustersView,
                        self).get_context_data(**kwargs)

        cluster_data = MainArticleKeyWords.objects.filter(
            article=self.kwargs['id'])
        article_description = MainArticleKeyWords.objects.filter(
            article=self.kwargs['id'])[0].article
        context.update({
            'clusters_data': cluster_data,
            'page_name': f"Кластеры артикула {article_description.common_article}: {article_description}",
        })
        return context

    def get_queryset(self):
        return MainArticleKeyWords.objects.filter(
            article=self.kwargs['id'])


class KeyPhraseCampaignStatisticView(ListView):
    """
    Описывает статистику ключевой фразы у каждой кампании
    """
    model = StatisticCampaignKeywordPhrase
    template_name = 'analytika_reklama/adv_phrase_statistic.html'
    context_object_name = 'data'

    def __init__(self, *args, **kwargs):
        super(KeyPhraseCampaignStatisticView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(KeyPhraseCampaignStatisticView,
                        self).get_context_data(**kwargs)

        phrase_data = StatisticCampaignKeywordPhrase.objects.filter(
            keyword=self.kwargs['id']).values('campaign__articles_name').annotate(
            campaign_name=F('campaign__campaign_name'),
            total_views=Sum('views'),
            total_clicks=Sum('clicks'),
            total_summ=Sum('summ'),
            click_to_view_ratio=ExpressionWrapper(
                F('total_clicks') * 100 / Case(
                    When(total_views=0, then=1),
                    default=F('total_views'),
                    output_field=FloatField()
                ),
                output_field=FloatField()
            )
        ).order_by('-total_views')[:10]
        print(phrase_data)
        phrase_obj = KeywordPhrase.objects.get(id=self.kwargs['id'])

        context.update({
            'phrase_data': phrase_data,
            'page_name': f"Статитстика фразы: {phrase_obj.phrase}",
        })
        return context

    # def get_queryset(self):
    #     return MainCampaignClusters.objects.filter(
    #         campaign=self.kwargs['id'])
