import datetime

from celery_tasks.tasks import add_article_price_info_to_database
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from .models import ArticleWriter, DataForAnalysis


def add_article(request):

    data = ArticleWriter.objects.all()

    today = datetime.datetime.today().strftime("%d-%m-%Y")
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
            add_article_price_info_to_database()
        return redirect('add_article')
    elif request.method == 'POST' and 'del-button' in request.POST.keys():
        ArticleWriter.objects.get(
            wb_article=request.POST['del-button']).delete()
        return redirect('add_article')

    return render(request, 'price_control/add_article.html', context)


class DataForAnalysisDetailView(ListView):
    model = DataForAnalysis
    template_name = 'price_control/price_article_detail.html'
    context_object_name = 'articles'

    def get_queryset(self):
        print(self.context_object_name)
        return DataForAnalysis.objects.filter(
            wb_article=self.kwargs['wb_article'])
