from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def landing_view(request):
    return render(request, "index.html")

@ensure_csrf_cookie
def test_view(request):
    return render(request, "test.html")