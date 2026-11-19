from decimal import Decimal

from catalog.models import Product

SESSION_KEY = "cart"


class Cart:
    """Carrinho guardado na sessão: {product_id: quantidade}."""

    def __init__(self, request):
        self.session = request.session
        self.data = self.session.setdefault(SESSION_KEY, {})

    def _save(self):
        self.session.modified = True

    def add(self, product, quantity=1):
        """Retorna False se a quantidade foi limitada pelo estoque."""
        key = str(product.id)
        wanted = self.data.get(key, 0) + quantity
        self.data[key] = min(wanted, product.stock)
        self._save()
        return wanted <= product.stock

    def set_quantity(self, product, quantity):
        """Retorna False se a quantidade foi limitada pelo estoque."""
        if quantity <= 0:
            self.remove(product)
            return True
        self.data[str(product.id)] = min(quantity, product.stock)
        self._save()
        return quantity <= product.stock

    def remove(self, product):
        self.data.pop(str(product.id), None)
        self._save()

    def clear(self):
        self.session[SESSION_KEY] = {}
        self._save()

    def items(self):
        products = Product.objects.filter(id__in=[int(i) for i in self.data], active=True)
        result = []
        for p in products:
            qty = min(self.data[str(p.id)], p.stock)
            if qty > 0:
                result.append({"product": p, "quantity": qty, "subtotal": p.price * qty})
        return result

    def __len__(self):
        return sum(self.data.values())

    @property
    def total(self):
        return sum((i["subtotal"] for i in self.items()), Decimal("0"))
