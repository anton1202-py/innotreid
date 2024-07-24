import json

from analytika_reklama.jam_statistic import \
    analytika_reklama_excel_with_jam_data
from analytika_reklama.models import (ArticleCampaignWhiteList,
                                      CommonCampaignDescription,
                                      DailyCampaignParameters,
                                      JamMainArticleKeyWords, KeywordPhrase,
                                      MainArticleExcluded, MainArticleKeyWords,
                                      MainCampaignClusters,
                                      MainCampaignExcluded,
                                      MainCampaignParameters,
                                      StatisticCampaignKeywordPhrase)
from analytika_reklama.periodic_tasks import (
    add_campaigns_statistic_to_db, get_auto_campaign_statistic_common_data,
    get_campaigns_amount_in_keyword_phrase,
    get_clusters_statistic_for_autocampaign,
    get_searchcampaign_keywords_statistic, keyword_for_articles)
from api_request.wb_requests import (get_del_minus_phrase_to_auto_campaigns,
                                     statistic_keywords_auto_campaign)
from create_reklama.minus_words_working import \
    get_minus_phrase_from_wb_auto_campaigns
from create_reklama.models import CreatedCampaign
from create_reklama.supplyment import (create_reklama_excel_with_campaign_data,
                                       white_list_phrase)
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import (Case, Count, ExpressionWrapper, F, FloatField,
                              OuterRef, Q, Subquery, Sum, When)
from django.db.models.functions import Coalesce, Round
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import ListView
from price_system.models import Articles
from reklama.models import UrLico

from web_barcode.constants_file import (WB_ADVERTISMENT_CAMPAIGN_STATUS_DICT,
                                        WB_ADVERTISMENT_CAMPAIGN_TYPE_DICT,
                                        bot, header_wb_data_dict,
                                        header_wb_dict)


@login_required
def main_adv_info(request):
    """Отображает общую информацию о кампании"""
    page_name = 'Инфо о рекламных кампаний'
    # keyword_for_articles()
    # add_campaigns_statistic_to_db()
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
    page_name = 'Статистика рекламных кампаний'
    campaign_info = MainCampaignParameters.objects.filter(
        campaign__ur_lico__ur_lice_name="ООО Иннотрейд").order_by('id')
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
    ur_lico_data = UrLico.objects.all()
    keyword_stats = StatisticCampaignKeywordPhrase.objects.values('keyword__phrase').annotate(
        campaign_amount=F('keyword__campaigns_amount'),
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
    if request.POST:
        keyword_filter_stat = StatisticCampaignKeywordPhrase.objects.all()
        if 'datestart' in request.POST and request.POST['datestart']:
            date_start = request.POST.get('datestart')
            keyword_filter_stat = keyword_filter_stat.filter(
                Q(statistic_date__gte=date_start))

        if 'datefinish' in request.POST and request.POST['datefinish']:
            date_finish = request.POST.get('datefinish')
            keyword_filter_stat = keyword_filter_stat.filter(
                Q(statistic_date__lt=date_finish))

        if 'ur_lico_select' in request.POST:
            filter_ur_lico = request.POST['ur_lico_select']
            keyword_filter_stat = keyword_filter_stat.filter(
                Q(campaign__ur_lico=filter_ur_lico))

        keyword_stats = keyword_filter_stat.values('keyword__phrase').annotate(
            campaign_amount=F('keyword__campaigns_amount'),
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
        'keyword_stats': keyword_stats,
        'ur_lico_data': ur_lico_data,
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
        'article').annotate(excluded_count=Count('excluded'))[:10]
    for data in common_keywords_info:
        article_key_words_info[Articles.objects.get(id=data['article'])] = {
            'cluster_count': data['cluster_count']}
    for data in common_excludes_info:
        if Articles.objects.get(id=data['article']) in article_key_words_info:
            article_key_words_info[Articles.objects.get(id=data['article'])
                                   ]['excluded_count'] = data['excluded_count']
    errors_data = ''
    ok_answer = ''
    if request.POST:
        if 'import_file' in request.FILES:
            errors_data = analytika_reklama_excel_with_jam_data(
                request.FILES['import_file'])
            if type(errors_data) != str:
                ok_answer = f"Файл {request.FILES['import_file']} принят в работу"
    context = {
        'page_name': page_name,
        'errors_data': errors_data,
        'ok_answer': ok_answer,
        'article_key_words_info': article_key_words_info,
        'excluded_count': 'excluded_count',
        'cluster_count': 'cluster_count'
    }
    return render(request, 'analytika_reklama/adv_article_words_info.html', context)


class MainArticleExcludedView(ListView):
    model = MainArticleExcluded
    template_name = 'analytika_reklama/article_excluded.html'
    context_object_name = 'data'

    def __init__(self, *args, **kwargs):
        self.ur_lico = kwargs.pop('ur_lico', None)
        super(MainArticleExcludedView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MainArticleExcludedView,
                        self).get_context_data(**kwargs)

        cluster_data = MainArticleExcluded.objects.filter(
            article=self.kwargs['id'])
        article_description = MainArticleExcluded.objects.filter(
            article=self.kwargs['id'])[0].article
        article_id = self.kwargs['id']
        context.update({
            'article_id': article_id,
            'clusters_data': cluster_data,
            'page_name': f"Минус слова артикула {article_description.common_article}: {article_description.name}",
        })
        return context

    def get_queryset(self):
        return MainArticleExcluded.objects.filter(
            article=self.kwargs['id'])


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
        data_dict = {}
        cluster_data = MainArticleKeyWords.objects.filter(
            article=self.kwargs['id'])
        for data in cluster_data:
            data_dict[data.cluster.phrase] = [data.views]

        article_description = MainArticleKeyWords.objects.filter(
            article=self.kwargs['id'])[0].article
        article_id = self.kwargs['id']

        jam_data = JamMainArticleKeyWords.objects.filter(
            article=self.kwargs['id']).values('cluster').annotate(
                cluster_name=F('cluster__phrase'),
                total_frequency=Sum('frequency'),
                total_views=Sum('views'),
                total_go_to_card=Sum('go_to_card'),
                total_added_to_cart=Sum('added_to_cart'),
                total_ordered=Sum('ordered')
        )
        for data in jam_data:
            if data['cluster_name'] in data_dict:
                data_dict[data['cluster_name']].append(data['total_frequency'])
                data_dict[data['cluster_name']].append(data['total_views'])
                data_dict[data['cluster_name']].append(
                    data['total_added_to_cart'])
                data_dict[data['cluster_name']].append(data['total_ordered'])
            else:
                data_dict[data['cluster_name']] = [0, data['total_frequency'],
                                                   data['total_views'], data['total_added_to_cart'], data['total_ordered']]

        context.update({
            'article_id': article_id,
            'clusters_data': cluster_data,
            'data_dict': data_dict,
            'page_name': f"Кластеры артикула {article_description.common_article}: {article_description.name}",
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
    object_list = None

    def __init__(self, *args, **kwargs):
        super(KeyPhraseCampaignStatisticView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(KeyPhraseCampaignStatisticView,
                        self).get_context_data(**kwargs)
        phrase_obj = KeywordPhrase.objects.get(id=self.kwargs['id'])
        ur_lico_data = UrLico.objects.all()
        # get_auto_campaign_statistic_common_data()
        phrase_data = StatisticCampaignKeywordPhrase.objects.filter(campaign__isnull=False,
                                                                    keyword=self.kwargs['id']).values('campaign__articles_name').annotate(
            campaign_obj=F('campaign'),
            campaign_name=F('campaign__campaign_name'),

            campaign_number=F('campaign__campaign_number'),
            campaign_ur_lico=F('campaign__ur_lico__ur_lice_name'),
            total_views=Sum('views'),
            total_clicks=Sum('clicks'),
            total_summ=Sum('summ'),
            click_to_view_ratio=ExpressionWrapper(
                Round(F('total_clicks') * 100 / Case(
                    When(total_views=0, then=1),
                    default=F('total_views'),
                    output_field=FloatField()
                ), 2),
                output_field=FloatField()
            ),
            phrase_list=Subquery(
                ArticleCampaignWhiteList.objects.filter(
                    campaign=OuterRef('campaign'), keyword=phrase_obj).values('phrase_list')[:1]
            )
        ).order_by('-total_views')
        numeric_list = []
        for data in phrase_data:
            inner_list = []
            numeric_list.append(
                round(100*(data['total_clicks']/data['total_views']), 2))
            ur_lic = data['campaign_ur_lico']
            camp_numb = data['campaign_number']
            minus_phrase_campaign_list = MainCampaignExcluded.objects.filter(
                campaign__ur_lico__ur_lice_name=ur_lic, campaign__campaign_number=camp_numb).values('excluded')
            campaign_obj = CreatedCampaign.objects.get(
                ur_lico__ur_lice_name=ur_lic, campaign_number=camp_numb)
            white_list = white_list_phrase(campaign_obj)
            for phrase in minus_phrase_campaign_list:
                if phrase['excluded'] not in white_list:
                    inner_list.append(phrase['excluded'])
            if phrase_obj.phrase in inner_list:
                data['minus_checker'] = True
            else:
                data['minus_checker'] = False
        print(numeric_list)
        context.update({
            'phrase_data': phrase_data,
            'keyphrase_obj': self.kwargs['id'],
            'page_name': f"Статистика фразы: {phrase_obj.phrase}",
            'minus_phrase': phrase_obj.phrase,
            'ur_lico_data': ur_lico_data
        })
        return context

    def post(self, request, *args, **kwargs):
        phrase_obj = KeywordPhrase.objects.get(id=self.kwargs['id'])
        ur_lico_data = UrLico.objects.all()
        phrase_data = StatisticCampaignKeywordPhrase.objects.filter(campaign__isnull=False,
                                                                    keyword=self.kwargs['id'])
        if request.POST:
            if 'datestart' in request.POST and request.POST['datestart']:
                date_start = request.POST.get('datestart')

                phrase_data = phrase_data.filter(
                    Q(statistic_date__gte=date_start))
            if 'datefinish' in request.POST and request.POST['datefinish']:
                date_finish = request.POST.get('datefinish')
                phrase_data = phrase_data.filter(
                    Q(statistic_date__lt=date_finish))
            if 'ur_lico_select' in request.POST:
                filter_ur_lico = request.POST['ur_lico_select']
                phrase_data = phrase_data.filter(
                    Q(campaign__ur_lico=filter_ur_lico))

        phrase_data = phrase_data.values('campaign__articles_name').annotate(
            campaign_obj=F('campaign'),
            campaign_name=F('campaign__campaign_name'),

            campaign_number=F('campaign__campaign_number'),
            campaign_ur_lico=F('campaign__ur_lico__ur_lice_name'),
            total_views=Sum('views'),
            total_clicks=Sum('clicks'),
            total_summ=Sum('summ'),
            click_to_view_ratio=ExpressionWrapper(
                Round(F('total_clicks') * 100 / Case(
                    When(total_views=0, then=1),
                    default=F('total_views'),
                    output_field=FloatField()
                ), 2),
                output_field=FloatField()
            ),
            phrase_list=Subquery(
                ArticleCampaignWhiteList.objects.filter(
                    campaign=OuterRef('campaign'), keyword=phrase_obj).values('phrase_list')[:1]
            )
        ).order_by('-total_views')
        for data in phrase_data:
            inner_list = []
            ur_lic = data['campaign_ur_lico']
            camp_numb = data['campaign_number']
            minus_phrase_campaign_list = MainCampaignExcluded.objects.filter(
                campaign__ur_lico__ur_lice_name=ur_lic, campaign__campaign_number=camp_numb).values('excluded')

            campaign_obj = CreatedCampaign.objects.get(
                ur_lico__ur_lice_name=ur_lic, campaign_number=camp_numb)
            white_list = white_list_phrase(campaign_obj)
            for phrase in minus_phrase_campaign_list:
                if phrase['excluded'] not in white_list:
                    inner_list.append(phrase['excluded'])
            if phrase_obj.phrase in inner_list:
                data['minus_checker'] = True
            else:
                data['minus_checker'] = False

        context = {
            'phrase_data': phrase_data,
            'keyphrase_obj': self.kwargs['id'],
            'page_name': f"Статистика фразы: {phrase_obj.phrase}",
            'minus_phrase': phrase_obj.phrase,
            'ur_lico_data': ur_lico_data,
        }
        return self.render_to_response(context)


def minus_words_checked_campaigns(request):
    """Присваивает минус слово чекнутым кампаниям"""
    campaigns_data = json.loads(request.POST.get('campaignData'))
    minus_words = request.POST.get('minus_word')

    for campaign_number, ur_lico in campaigns_data.items():
        # Получаем список минус фраз кампании
        campaign_minus_phrase_list = get_minus_phrase_from_wb_auto_campaigns(
            ur_lico, campaign_number)
        if minus_words not in campaign_minus_phrase_list:
            campaign_minus_phrase_list.append(minus_words)
            header = header_wb_dict[ur_lico]
            get_del_minus_phrase_to_auto_campaigns(
                header, campaign_number, campaign_minus_phrase_list)

    return JsonResponse({'message': 'Value saved successfully.'})


def update_white_phrase(request):
    """Обновлят белый список у рекламной кампании"""
    if request.POST:
        # print(request.POST)
        campaign_obj = request.POST.get('campaign_obj')
        white_phrase = request.POST.get('white_phrase')
        keyphrase_obj = int(request.POST.get('keyphrase_obj'))

        phrase_obj = KeywordPhrase.objects.get(id=keyphrase_obj)
        camp_obj = CreatedCampaign.objects.get(id=campaign_obj)
        if ArticleCampaignWhiteList.objects.filter(campaign=camp_obj, keyword=phrase_obj).exists():
            ArticleCampaignWhiteList.objects.filter(
                campaign=camp_obj, keyword=phrase_obj).update(phrase_list=white_phrase)
        else:
            ArticleCampaignWhiteList(
                campaign=camp_obj,
                phrase_list=white_phrase,
                keyword=phrase_obj
            ).save()

    return JsonResponse({'message': 'Value saved successfully.'})
