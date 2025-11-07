from django.http import HttpResponse

def home(request):
    return HttpResponse("سلام! این صفحه اصلی پروژه است.")
