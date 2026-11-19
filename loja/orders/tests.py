from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Product

from .models import Order

User = get_user_model()
ADDR = {"full_name": "Maria Silva", "phone": "(11) 91234-5678", "address": "Rua A, 10, Centro, São Paulo, 01000-000"}


class StoreFlowTests(TestCase):
    def setUp(self):
        self.p = Product.objects.create(name="Amigurumi", price=Decimal("50.00"), stock=5)
        self.user = User.objects.create_user("maria", "m@x.com", "senha-forte-123")
        self.staff = User.objects.create_user("adm", "a@x.com", "senha-forte-123", is_staff=True)

    def test_public_pages(self):
        for url in (reverse("catalog:home"), reverse("catalog:list"), self.p.get_absolute_url()):
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_register_login_logout(self):
        r = self.client.post(reverse("accounts:register"), {
            "username": "nova", "first_name": "Nova", "email": "nova@x.com",
            "password1": "Senha-Forte-987", "password2": "Senha-Forte-987"})
        self.assertRedirects(r, reverse("catalog:home"))
        u = User.objects.get(username="nova")
        self.assertTrue(u.password.startswith("pbkdf2_"))
        self.client.post(reverse("accounts:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertTrue(self.client.login(username="nova", password="Senha-Forte-987"))

    def test_cart_and_checkout_decrements_stock(self):
        self.client.add_cart = lambda q: self.client.post(reverse("cart:add", args=[self.p.id]), {"quantity": q})
        self.client.add_cart(2)
        self.client.post(reverse("cart:update", args=[self.p.id]), {"quantity": 3})
        self.assertEqual(self.client.get(reverse("cart:detail")).context["total"], Decimal("150.00"))
        # exige login
        self.assertEqual(self.client.get(reverse("orders:checkout")).status_code, 302)
        self.client.login(username="maria", password="senha-forte-123")
        r = self.client.post(reverse("orders:checkout"), ADDR)
        order = Order.objects.get()
        self.assertRedirects(r, reverse("orders:detail", args=[order.pk]))
        self.assertEqual(order.total, Decimal("150.00"))
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 2)
        self.assertEqual(len(self.client.get(reverse("orders:history")).context["orders"]), 1)

    def test_cannot_exceed_stock_and_remove(self):
        self.client.post(reverse("cart:add", args=[self.p.id]), {"quantity": 99})
        self.assertEqual(self.client.session["cart"][str(self.p.id)], 5)
        self.client.post(reverse("cart:remove", args=[self.p.id]))
        self.assertEqual(self.client.session["cart"], {})

    def test_cancel_restores_stock_and_admin_status(self):
        self.client.post(reverse("cart:add", args=[self.p.id]), {"quantity": 2})
        self.client.login(username="maria", password="senha-forte-123")
        self.client.post(reverse("orders:checkout"), ADDR)
        order = Order.objects.get()
        self.client.logout()
        self.client.login(username="adm", password="senha-forte-123")
        self.client.post(reverse("painel:order_detail", args=[order.pk]), {"status": "shipped"})
        order.refresh_from_db()
        self.assertEqual(order.status, "shipped")
        self.client.post(reverse("painel:order_detail", args=[order.pk]), {"status": "cancelled"})
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 5)

    def test_regular_user_blocked_from_panel_and_other_orders(self):
        self.assertEqual(self.client.get(reverse("painel:dashboard")).status_code, 302)  # anônimo -> login
        self.client.login(username="maria", password="senha-forte-123")
        for name in ("painel:dashboard", "painel:products", "painel:orders", "painel:product_create"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403)
        o = Order.objects.create(user=self.staff, total=1, **ADDR)
        self.assertEqual(self.client.get(reverse("orders:detail", args=[o.pk])).status_code, 404)

    def test_admin_product_crud(self):
        self.client.login(username="adm", password="senha-forte-123")
        r = self.client.post(reverse("painel:product_create"), {"name": "Bolsa", "price": "80", "stock": "3", "active": "on"})
        self.assertRedirects(r, reverse("painel:products"))
        p = Product.objects.get(name="Bolsa")
        self.client.post(reverse("painel:product_edit", args=[p.pk]), {"name": "Bolsa G", "price": "90", "stock": "4", "active": "on"})
        p.refresh_from_db()
        self.assertEqual((p.name, p.stock), ("Bolsa G", 4))
        bad = self.client.post(reverse("painel:product_create"), {"name": "X", "price": "-1", "stock": "1"})
        self.assertEqual(bad.status_code, 200)
        self.client.post(reverse("painel:product_delete", args=[p.pk]))
        self.assertFalse(Product.objects.filter(pk=p.pk).exists())
