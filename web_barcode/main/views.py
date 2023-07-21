from django.shortcuts import render

from .forms import AddPostSignal


def index(request):
    if request.method == 'POST':
        form = AddPostSignal(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            ctr = form.cleaned_data['max_ctr']
            watches = form.cleaned_data['min_watches']

    else:
        print('Таков путь')
        form = AddPostSignal()

    return render(request, 'main/index.html', {'form': form})


def barcode(request):
    return render(request, 'main/barcode.html')


def qrcode(request):
    return render(request, 'main/qrcode.html')


def barcodebox(request):
    return render(request, 'main/barcodebox.html')
