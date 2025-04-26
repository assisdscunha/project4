
from django.urls import path, re_path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    
    # API Routes
    path("posts", views.share_post, name="share_post"),
    path("posts/<int:post_id>", views.post, name="get_post"),
    path("posts/profile/<str:username>", views.handle_profile, name="profile"),
    path("posts/<str:page_name>", views.page, name="page"),
    
    # Catch for frontend
    re_path(r"^(all|following|profile/[^/]+)?/?$", views.index, name="spa-catchall"),
]
