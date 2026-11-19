import re

from django import forms

from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("full_name", "phone", "address")
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = re.sub(r"\D", "", phone)
        if not 10 <= len(digits) <= 13:
            raise forms.ValidationError("Informe um telefone válido com DDD.")
        return phone

    def clean_address(self):
        address = self.cleaned_data["address"].strip()
        if len(address) < 10:
            raise forms.ValidationError("Informe o endereço completo (rua, número, bairro, cidade, CEP).")
        return address
