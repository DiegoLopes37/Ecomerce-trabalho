from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Product
from orders.models import Order

from .forms import OrderStatusForm, ProductForm


def staff_required(view):
    """RNF07/RNF09: exige login; usuários comuns recebem 403."""

    def check(user):
        if not user.is_staff:
            raise PermissionDenied
        return True

    return login_required(user_passes_test(check)(view))


@staff_required
def dashboard(request):
    return render(request, "painel/dashboard.html", {
        "products": Product.objects.count(),
        "pending": Order.objects.filter(status=Order.PENDING).count(),
        "low_stock": Product.objects.filter(stock__lte=3, active=True).count(),
    })


@staff_required
def product_list(request):
    return render(request, "painel/product_list.html", {"products": Product.objects.all()})


@staff_required
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Produto cadastrado com sucesso.")
            return redirect("painel:products")
        messages.error(request, "Não foi possível salvar o produto. Verifique os campos.")
    return render(request, "painel/product_form.html", {"form": form, "title": "Novo produto"})


@staff_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Produto atualizado com sucesso.")
            return redirect("painel:products")
        messages.error(request, "Não foi possível salvar o produto. Verifique os campos.")
    return render(request, "painel/product_form.html", {"form": form, "title": f"Editar: {product.name}"})


@staff_required
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()  # itens de pedidos antigos mantêm nome/preço (product vira NULL)
    messages.success(request, f"Produto “{name}” excluído.")
    return redirect("painel:products")


@staff_required
def order_list(request):
    orders = Order.objects.select_related("user")
    status = request.GET.get("status")
    if status in dict(Order.STATUS_CHOICES):
        orders = orders.filter(status=status)
    return render(request, "painel/order_list.html", {
        "orders": orders, "statuses": Order.STATUS_CHOICES, "current": status})


@staff_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related("user").prefetch_related("items"), pk=pk)
    form = OrderStatusForm(request.POST or None, initial={"status": order.status})
    if request.method == "POST":
        if form.is_valid():
            try:
                order.change_status(form.cleaned_data["status"])
                messages.success(request, f"Status do pedido #{order.pk} atualizado.")
                return redirect("painel:order_detail", pk=order.pk)
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Status inválido.")
    return render(request, "painel/order_detail.html", {"order": order, "form": form})
