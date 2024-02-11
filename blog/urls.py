from django.urls import path
from . import views
from .views import (
    PostListView,
    PostDetailView,
    PostCreateView,
    PostUpdateView,
    PostDeleteView,
    UserPostListView,
    contact_view,
    add_comment, 
    resources
)

urlpatterns = [
    path('', views.index, name='index'),
    path('user/<str:username>/', UserPostListView.as_view(), name='user_posts'),
    path('post/<int:pk>/', PostDetailView.as_view(), name='post_detail'),
    path('post/new/', PostCreateView.as_view(), name='post_create'),
    path('post/<int:pk>/update/', PostUpdateView.as_view(), name='post_update'),
    path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='post_delete'),
    path('about/', views.about, name='about'),
    path('contact/', contact_view, name='contact'),
    path('blog/', PostListView.as_view(), name='blog'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('resources/', views.resources_view, name='resources'),
    path('post/<int:pk>/comment/', add_comment, name='add_comment'),
    path('privacy-policy/', views.privacy_policy, name='privacy-policy'),
]
