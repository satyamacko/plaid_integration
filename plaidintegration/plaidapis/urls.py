from django.urls import path

from .views import get_link_token, get_access_token, get_public_token_and_exchange, \
    handle_transaction_webhook_callbacks, UserAccountMasterListView, UserTransactionMasterListView

urlpatterns = [
    path('get_link_token/', get_link_token, name='get_link_token'),
    path('get_access_token/', get_access_token, name='get_access_token'),
    path('get_public_token/', get_public_token_and_exchange, name='get_public_token'),
    path('user_accounts/', UserAccountMasterListView.as_view(), name='user_accounts_list_view'),
    path('user_transactions/', UserTransactionMasterListView.as_view(), name='user_transactions_list_view'),
    path('transaction_callbacks/', handle_transaction_webhook_callbacks, name='handle_transaction_webhook_callbacks'),
]