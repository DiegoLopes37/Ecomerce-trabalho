from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from cart.cart import Cart
from catalog.models import Product

from .forms import CheckoutForm
from .models import Order, OrderItem


class StockError(Exception):
    pass


@transaction.atomic
def create_order(user, cart, data):
    """Cria o pedido e baixa o estoque com bloqueio de linha (RF11, RF12, RF18)."""
    wanted = {int(pid): qty for pid, qty in cart.data.items()}
    products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=wanted, active=True)}
    if not wanted or not products:
        raise StockError("Seu carrinho está vazio.")

    order = Order.objects.create(user=user, **data)
    total = Decimal("0")
    for pid, qty in wanted.items():
        product = products.get(pid)
        if product is None:
            raise StockError("Um dos produtos do carrinho não está mais disponível.")
        if qty > product.stock:
            raise StockError(f"Estoque insuficiente para “{product.name}” (disponível: {product.stock}).")
        product.stock -= qty
        product.save(update_fields=["stock"])
        OrderItem.objects.create(order=order, product=product, product_name=product.name,
                                 unit_price=product.price, quantity=qty)
        total += product.price * qty
    order.total = total
    order.save(update_fields=["total"])
    return order


@login_required
def checkout(request):
    cart = Cart(request)
    items = cart.items()
    if not items:
        messages.warning(request, "Seu carrinho está vazio.")
        return redirect("catalog:list")

    initial = {"full_name": request.user.get_full_name()}
    form = CheckoutForm(request.POST or None, initial=initial)
    if request.method == "POST":
        if form.is_valid():
            try:
                order = create_order(request.user, cart, form.cleaned_data)
            except StockError as e:
                messages.error(request, str(e))
                return redirect("cart:detail")
            cart.clear()
            messages.success(request, f"Pedido #{order.pk} realizado com sucesso!")
            return redirect("orders:detail", pk=order.pk)
        messages.error(request, "Corrija os erros do formulário para finalizar a compra.")
    return render(request, "orders/checkout.html", {"form": form, "items": items, "total": cart.total})


@login_required
def history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items")
    return render(request, "orders/history.html", {"orders": orders})


@login_required
def detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=pk)
    return render(request, "orders/detail.html", {"order": order})
