import datetime

from celery_tasks.tasks import add_one_article_info_to_db
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from .models import ArticleWriter, DataForAnalysis


def add_article(request):
    """Отвечает за представление страницы с добавлением артикула в БД"""
    data = ArticleWriter.objects.all().order_by('id')
    context = {
        'data': data,
    }
    if request.method == 'POST' and 'add_button' in request.POST.keys():
        request_data = request.POST
        if ArticleWriter.objects.filter(Q(wb_article=request_data['wildberries_article'])):
            ArticleWriter.objects.filter(wb_article=request_data['wildberries_article']).update(
                seller_article=request_data['seller_article'],
            )
        else:
            obj, created = ArticleWriter.objects.get_or_create(
                seller_article=request_data['seller_article'],
                wb_article=request_data['wildberries_article'],
            )
        add_one_article_info_to_db(
            request_data['seller_article'], request_data['wildberries_article'])
        return redirect('add_article')
    elif request.method == 'POST' and 'change_button' in request.POST.keys():
        request_data = request.POST
        ArticleWriter.objects.filter(id=request_data['change_button']).update(
            seller_article=request_data['seller_article'],
        )
        return redirect('add_article')
    elif request.method == 'POST' and 'del-button' in request.POST.keys():
        ArticleWriter.objects.get(
            wb_article=request.POST['del-button']).delete()
        DataForAnalysis.objects.filter(
            wb_article=request.POST['del-button']).delete()
        return redirect('add_article')

    return render(request, 'price_control/add_article.html', context)


class DataForAnalysisDetailView(ListView):
    model = DataForAnalysis
    template_name = 'price_control/price_article_detail.html'
    context_object_name = 'articles'

    def get_queryset(self):
        return DataForAnalysis.objects.filter(
            wb_article=self.kwargs['wb_article']).order_by('price_date')
