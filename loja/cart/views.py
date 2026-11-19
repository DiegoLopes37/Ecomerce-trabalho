from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from catalog.models import Product

from .cart import Cart


def _qty(request, default=1):
    try:
        return int(request.POST.get("quantity", default))
    except (TypeError, ValueError):
        return None


def detail(request):
    cart = Cart(request)
    return render(request, "cart/detail.html", {"items": cart.items(), "total": cart.total})


@require_POST
def add(request, product_id):
    product = get_object_or_404(Product, id=product_id, active=True)
    qty = _qty(request)
    if qty is None or qty < 1:
        messages.error(request, "Quantidade inválida.")
    elif product.stock == 0:
        messages.error(request, f"“{product.name}” está sem estoque.")
    elif Cart(request).add(product, qty):
        messages.success(request, f"“{product.name}” adicionado ao carrinho.")
    else:
        messages.warning(request, f"Quantidade limitada ao estoque disponível de “{product.name}” ({product.stock}).")
    nxt = request.POST.get("next", "")
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return redirect(nxt)
    return redirect("cart:detail")


@require_POST
def update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    qty = _qty(request)
    if qty is None or qty < 0:
        messages.error(request, "Quantidade inválida.")
    elif Cart(request).set_quantity(product, qty):
        messages.success(request, "Carrinho atualizado.")
    else:
        messages.warning(request, f"Quantidade ajustada ao estoque disponível ({product.stock}).")
    return redirect("cart:detail")


@require_POST
def remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Cart(request).remove(product)
    messages.success(request, f"“{product.name}” removido do carrinho.")
    return redirect("cart:detail")
