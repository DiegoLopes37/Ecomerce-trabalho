from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [
    path("cadastro/", views.register, name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("sair/", views.logout_view, name="logout"),
]
