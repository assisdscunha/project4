
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    
    # API Routes
    path("posts", views.share_post, name="posts"),
    path("posts/<int:post_id>", views.post, name="posts"),
    path("posts/<str:page_name>", views.page, name="posts"),
]
