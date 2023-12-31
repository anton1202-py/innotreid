from datetime import date, timedelta

from database.forms import SelectDateForm
from django.db.models import Q
from django.shortcuts import redirect, render
from django.views.generic import DeleteView, DetailView, ListView, UpdateView

from .models import Stocks_Innotreid


def database_yandex_stock(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    control_date_stock = date.today() - timedelta(days=1)
    data = Stocks_Innotreid.objects.filter(Q(pub_date__range=[
        control_date_stock,
        control_date_stock]))
    form = SelectDateForm(request.POST or None)
    datestart = control_date_stock
    datefinish = control_date_stock
    
    if form.is_valid():
        datestart = form.cleaned_data.get("datestart")
        datefinish = form.cleaned_data.get("datefinish")
        article_filter = form.cleaned_data.get("article_filter")
        if article_filter == '':
            data = Stocks_Innotreid.objects.filter(
                Q(pub_date__range=[datestart, datefinish]))
        else:
            data = Stocks_Innotreid.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(article_marketplace=article_filter))
    context = {
        'form': form,
        'data': data,
        'datestart': str(datestart),
    }
    return render(request, 'database_yandex/stock_yandex_innotreid.html', context)


class DatabaseStockDetailView(ListView):
    model = Stocks_Innotreid
    template_name = 'database_yandex/stock_article_yandex_detail.html'
    context_object_name = 'articles'

    def get_queryset(self):
        return Stocks_Innotreid.objects.filter(
            article_marketplace=self.kwargs['article_marketplace'])
