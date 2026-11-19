from django.urls import path

from . import views

app_name = "orders"
urlpatterns = [
    path("", views.history, name="history"),
    path("finalizar/", views.checkout, name="checkout"),
    path("<int:pk>/", views.detail, name="detail"),
]
