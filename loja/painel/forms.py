from django import forms

from catalog.models import Product
from orders.models import Order


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "description", "price", "stock", "image", "active")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("O preço deve ser maior que zero.")
        return price

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 3:
            raise forms.ValidationError("O nome deve ter ao menos 3 caracteres.")
        return name


class OrderStatusForm(forms.Form):
    status = forms.ChoiceField(label="Status", choices=Order.STATUS_CHOICES)
