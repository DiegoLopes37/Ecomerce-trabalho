from django.conf import settings
from django.db import models, transaction


class Order(models.Model):
    PENDING, PAID, SHIPPED, DELIVERED, CANCELLED = "pending", "paid", "shipped", "delivered", "cancelled"
    STATUS_CHOICES = [
        (PENDING, "Pendente"),
        (PAID, "Pago"),
        (SHIPPED, "Enviado"),
        (DELIVERED, "Entregue"),
        (CANCELLED, "Cancelado"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    full_name = models.CharField("nome completo", max_length=150)
    phone = models.CharField("telefone", max_length=20)
    address = models.TextField("endereço de entrega")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Pedido #{self.pk}"

    @transaction.atomic
    def change_status(self, new_status):
        """Altera o status; ao cancelar, devolve os itens ao estoque (RF17/RF18)."""
        from catalog.models import Product

        order = Order.objects.select_for_update().get(pk=self.pk)
        if order.status == self.CANCELLED:
            raise ValueError("Pedidos cancelados não podem ser reabertos.")
        if new_status == self.CANCELLED:
            for item in order.items.select_related("product"):
                if item.product_id:
                    Product.objects.filter(pk=item.product_id).update(stock=models.F("stock") + item.quantity)
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        self.status = new_status


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=150)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"
