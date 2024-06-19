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


def articles_list_with_main_info(request):
    """
    Отображает список артикулов с количеством отзывов
    и средней оценкой на основе этих отзывов.
    Все данные берутся из базы данных
    """
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Общая информация по отзывам артикулов'
    # budget_working()
    articles_feedbacks = FeedbacksWildberries.objects.filter(common_article__company='ООО Иннотрейд'
                                                             ).values(
        'common_article',
        'common_article__common_article',
        'common_article__company',
        'common_article__name'
    ).annotate(total_feedbacks=Count('id'), average_valuation=Avg('product_valuation')).order_by('-total_feedbacks')

    if request.POST:
        if 'import_file' in request.FILES:
            import_data_error_text = excel_import_previously_data(
                request.FILES['import_file'])
    context = {
        'page_name': page_name,
        'articles_feedbacks': articles_feedbacks,

    }
    return render(request, 'feedbacks/articles_list_with_amount_feedbacks.html', context)


class FeedbacksArticleDetailView(ListView):
    model = FeedbacksWildberries
    template_name = 'feedbacks/article_feedbacks.html'

    def get_context_data(self, **kwargs):
        context = super(FeedbacksArticleDetailView,
                        self).get_context_data(**kwargs)
        page_name = f"Отзывы артикула: {self.kwargs['common_article']}"
        articles_feedbacks = FeedbacksWildberries.objects.filter(
            common_article__common_article=self.kwargs['common_article']).exclude(text__exact='').order_by('-created_date')
        context.update({
            'articles_feedbacks': articles_feedbacks,
            'page_name': page_name,
        })
        return context
