from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Product


def home(request):
    destaques = Product.objects.filter(active=True, stock__gt=0)[:4]
    return render(request, "catalog/home.html", {"destaques": destaques})


def product_list(request):
    qs = Product.objects.filter(active=True)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(name__icontains=q)
    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    return render(request, "catalog/list.html", {"page": page, "q": q})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True)
    return render(request, "catalog/detail.html", {"product": product})
