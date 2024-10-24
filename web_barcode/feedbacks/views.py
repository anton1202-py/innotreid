import os
from datetime import datetime, timedelta

from analytika_reklama.models import DailyCampaignParameters
from django.db.models import Avg, Count, Max, Q
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView
from dotenv import load_dotenv
from feedbacks.models import FeedbacksWildberries
from feedbacks.supplyment import excel_import_previously_data
from price_system.models import Articles
from reklama.forms import FilterUrLicoForm
from reklama.models import UrLico


def articles_list_with_main_info(request):
    """
    Отображает список артикулов с количеством отзывов
    и средней оценкой на основе этих отзывов.
    Все данные берутся из базы данных
    """
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Общая информация по отзывам артикулов'
    ur_lico_data = UrLico.objects.all()

    articles_feedbacks = FeedbacksWildberries.objects.filter(common_article__company='ООО Иннотрейд'
                                                             ).values(
        'common_article',
        'common_article__common_article',
        'common_article__company',
        'common_article__name'
    ).annotate(total_feedbacks=Count('id'), average_valuation=Avg('product_valuation')).order_by('-total_feedbacks')

    if request.POST:
        print(request.POST)
        if 'ur_lico_select' in request.POST:
            filter_ur_lico = request.POST['ur_lico_select']
            articles_feedbacks = FeedbacksWildberries.objects.filter(common_article__company=filter_ur_lico
                                                                     ).values(
                'common_article',
                'common_article__common_article',
                'common_article__company',
                'common_article__name'
            ).annotate(total_feedbacks=Count('id'), average_valuation=Avg('product_valuation')).order_by('-total_feedbacks')
        elif 'common_article' in request.POST:
            common_article = request.POST['common_article']
            articles_feedbacks = FeedbacksWildberries.objects.filter(common_article__common_article__contains=common_article
                                                                     ).values(
                'common_article',
                'common_article__common_article',
                'common_article__company',
                'common_article__name'
            ).annotate(total_feedbacks=Count('id'), average_valuation=Avg('product_valuation')).order_by('-total_feedbacks')
        elif 'import_file' in request.FILES:
            import_data_error_text = excel_import_previously_data(
                request.FILES['import_file'])
    context = {
        'page_name': page_name,
        'articles_feedbacks': articles_feedbacks,
        'ur_lico_data': ur_lico_data,

    }
    return render(request, 'feedbacks/articles_list_with_amount_feedbacks.html', context)


class FeedbacksArticleDetailView(ListView):
    model = FeedbacksWildberries
    template_name = 'feedbacks/article_feedbacks.html'

    def get_context_data(self, **kwargs):
        context = super(FeedbacksArticleDetailView,
                        self).get_context_data(**kwargs)
        article_data = Articles.objects.filter(
            common_article=self.kwargs['common_article'])[0]
        page_name = f"Отзывы артикула: {self.kwargs['common_article']} ({article_data.name})"

        articles_feedbacks = FeedbacksWildberries.objects.filter(
            common_article__common_article=self.kwargs['common_article']).exclude(text__exact='').order_by('-created_date')
        context.update({
            'articles_feedbacks': articles_feedbacks,
            'page_name': page_name,
        })
        return context
