from django.urls import path
from .views import get_link_token, get_access_token, get_user_transactions

urlpatterns = [
    path('get_link_token/', get_link_token, name='get_link_token'),
    path('get_access_token/', get_access_token, name='get_access_token'),
    path('get_user_transactions/', get_user_transactions, name='get_user_transactions'),
]