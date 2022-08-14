from django.shortcuts import render
from booktest.models import BookInfo
from django.http import HttpResponse
# Create your views here.
def index(request):
    books = BookInfo.objects.all()
    # book = books.btitle
    tr = BookInfo()
    tr.btitle = "jiajiajia"
    tr.bread = 20
    tr.save()
    return render(request,"index.html",{"book":books})
    # return HttpResponse(books)