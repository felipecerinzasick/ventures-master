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
    resources_view
)

urlpatterns = [
    path('', views.index, name='index'),
    path('user/<str:username>/', UserPostListView.as_view(), name='user_posts'),
    path('post/<int:pk>/', PostDetailView.as_view(), name='post_detail'),
    path('post/new/', PostCreateView.as_view(), name='post_create'),
    path('post/<int:pk>/update/', PostUpdateView.as_view(), name='post_update'),
    path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='post_delete'),
    path('about/', views.about, name='about'),
    path('bitcoin/', views.bitcoin, name='bitcoin'),
    path('contact/', contact_view, name='contact'),
    path('blog/', PostListView.as_view(), name='blog'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/mstr/', views.mstr_dashboard, name='mstr_dashboard'),
    path('dashboard/report.pdf', views.portfolio_report_pdf, name='portfolio_report_pdf'),
    path('api/wealth-progression/', views.wealth_progression, name='wealth_progression'),
    path('api/bitcoin-price/', views.bitcoin_price, name='bitcoin_price'),
    path('api/mstr-btc/', views.mstr_btc, name='mstr_btc'),
    path('api/ibkr-portfolio/', views.ibkr_portfolio, name='ibkr_portfolio'),
    path('resources/', views.resources_view, name='resources'),
    path('post/<int:pk>/comment/', add_comment, name='add_comment'),
    path('privacy-policy/', views.privacy_policy, name='privacy-policy'),
]
