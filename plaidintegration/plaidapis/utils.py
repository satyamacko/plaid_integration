from datetime import date, datetime

import plaid
import structlog
from django.conf import settings
from django.db.models import Q
from plaid.errors import PlaidError, APIError, InstitutionError

from plaidapis.models import UserAccountMaster, UserTransactionMaster
from plaidapis.serializers import UserAccountMasterSerializer, UserTransactionMasterSerializer

client = plaid.Client(client_id=settings.PLAID_CLIENT_ID,
                      secret=settings.PLAID_SECRET,
                      environment=settings.PLAID_ENV)

logger = structlog.get_logger()


def get_plaid_client():
    return client


def update_webhook_url(access_token):
    try:
        webhook_response = client.Item.webhook.update(access_token, 'https://satyamsammi.free.beeceptor.com')
        logger.info("update_webhook_url:: Response", response=webhook_response)
        return
    except plaid.errors.APIError as e:
        logger.error("update_webhook_url:: APIError Exception - ", exception=str(e))
        return
    except plaid.errors.InvalidRequestError as e:
        logger.error("update_webhook_url:: InvalidRequestError Exception - ", exception=str(e))
        return e
    except plaid.errors.PlaidError as e:
        logger.error("update_webhook_url:: PlaidError Exception - ", exception=str(e))
        return
    except plaid.errors.PlaidCause as e:
        logger.error("update_webhook_url:: PlaidCause Exception - ", exception=str(e))
        return
    except plaid.errors.BaseError as e:
        logger.error("update_webhook_url:: Exception - ", exception=str(e))
        return


def fetch_user_accounts(access_token):
    try:
        response = client.Accounts.get(access_token)
        logger.info("fetch_user_accounts:: response", response=response)
        return response
    except (APIError, InstitutionError) as e:
        logger.error("fetch_user_accounts:: APIError Exception", exception=str(e), error_type=e.type, error_code=e.code,
                     request_id=e.request_id)
        return e
    except PlaidError as e:
        logger.info("fetch_user_accounts:: Exception - ", exception=str(e), type=e.type, error_code=e.code,
                    request_id=e.request_id)
        return None


def fetch_saved_user_accounts(user_plaid_master):
    accounts_list = list(UserAccountMaster.objects.filter(user_plaid_master=user_plaid_master).values())
    account_dict = dict()
    for account in accounts_list:
        account_dict[account.get('account_id')] = account
    logger.info("fetch_saved_user_accounts:: saved accounts", user_plaid_master_id=user_plaid_master.id,
                account_dict=account_dict, account_dict_len=len(account_dict))
    return account_dict


def get_user_transactions(access_token, start_date, end_date):
    try:
        response = client.Transactions.get(access_token,
                                           start_date=start_date,
                                           end_date=end_date,
                                           count=500)
        logger.info("get_user_transactions:: response -", response=response)
        transactions = response['transactions']
        while len(transactions) < response['total_transactions']:
            response = client.Transactions.get(access_token,
                                               start_date=start_date,
                                               end_date=end_date,
                                               offset=len(transactions)
                                               )
            transactions.extend(response['transactions'])
        logger.info("get_user_transactions:: overall transactions -", transactions=transactions)
        return transactions
    except (APIError, InstitutionError) as e:
        logger.error("get_user_transactions:: APIError/InstitutionError Exception", exception=str(e), error_type=e.type,
                     error_code=e.code, request_id=e.request_id)
        return e
    except PlaidError as e:
        logger.error("get_user_transactions:: PlaidError Exception", exception=str(e), type=e.type, error_code=e.code,
                     request_id=e.request_id)
        return None
    except Exception as e:
        logger.error("get_user_transactions:: Exception", exception=str(e))
        return None


def create_transaction_object(plaid_master_record, transaction):
    UserTransactionMaster.objects.create(user_plaid_master=plaid_master_record,
                                         account_id=transaction.get('account_id'),
                                         account_owner=transaction.get('account_owner'),
                                         transaction_id=transaction.get('transaction_id'),
                                         amount=transaction.get('amount'),
                                         name=transaction.get('name'),
                                         merchant_name=transaction.get('merchant_name'),
                                         category_id=transaction.get('category_id'),
                                         category=transaction.get('category'),
                                         iso_currency_code=transaction.get('iso_currency_code'),
                                         unofficial_currency_code=transaction.get('unofficial_currency_code'),
                                         location=transaction.get('location'),
                                         payment_channel=transaction.get('payment_channel'),
                                         pending=transaction.get('pending'),
                                         payment_meta=transaction.get('payment_meta'),
                                         date=transaction.get('date'),
                                         authorized_date=transaction.get('authorized_date'),
                                         active=True,
                                         )


def update_user_transactions(plaid_master_record, start_date, end_date):
    try:
        logger.info("update_user_transactions_start", plaid_master_record_id=plaid_master_record.id)
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        new_transactions = get_user_transactions(plaid_master_record.access_token, start_date, end_date)
        if new_transactions is None or len(new_transactions) == 0:
            logger.warn("update_user_transactions:: new_transactions not available.",
                        plaid_master_record_id=plaid_master_record.id)
            return
        saved_transactions = set(UserTransactionMaster.objects.filter(user_plaid_master=plaid_master_record,
                                                                      date__gte=start_date_obj.date(),
                                                                      active=True)
                                 .values_list('transaction_id', flat=True))
        logger.info("update_user_transactions", plaid_master_record_id=plaid_master_record.id,
                    new_transactions_len=len(new_transactions), saved_transactions_len=len(saved_transactions))
        counter = 0
        for transaction in new_transactions:
            if transaction.get('transaction_id') not in saved_transactions:
                try:
                    create_transaction_object(plaid_master_record, transaction)
                    counter = counter + 1
                except Exception as e:
                    logger.error("update_user_transactions:: Exception while saving transaction - ", exception=str(e))
        logger.info("update_user_transactions", plaid_master_record_id=plaid_master_record.id, updated_count=counter)
    except (APIError, InstitutionError) as e:
        logger.error("update_user_transactions:: Plaid Exception", exception=str(e), error_type=e.type,
                     error_code=e.code, request_id=e.request_id, plaid_master_record=plaid_master_record.id)
        return e
    except Exception as e:
        logger.error("update_user_transactions:: Exception - ", exception=str(e))
        return None


def remove_user_transactions(item_id, removed_transactions):
    transactions_updated = UserTransactionMaster.objects \
        .filter(transaction_id__in=removed_transactions, active=True) \
        .update(active=False)
    logger.info("remove_user_transactions::", item_id=item_id, transactions=removed_transactions,
                count_removed=transactions_updated)


class ValidationError(Exception):
    pass


class UserAccount(object):
    model = UserAccountMaster
    serializer_class = UserAccountMasterSerializer
    filter = Q()
    filter_dict = dict()

    def get_user_account_queryset(self):
        return self.model.objects.filter(
            self.filter, **self.filter_dict
        ).order_by("id")

    def set_filter(self, params):
        self.filter = Q()
        self.filter_dict = dict()
        if "id" in params:
            self.filter &= Q(id=params["id"])
        if "user_plaid_master_id" in params:
            self.filter &= Q(user_plaid_master__id=params["user_plaid_master_id"])
        if "user_id" in params:
            self.filter &= Q(user_plaid_master__user__id=params["user_id"])
        if "username" in params:
            self.filter &= Q(user_plaid_master__user__username=params["username"])
        if "institution_id" in params:
            self.filter &= Q(user_plaid_master__institution_id=params["institution_id"])
        if "active" in params:
            if params["active"] == 'true':
                self.filter &= Q(active=True)
            else:
                self.filter &= Q(active=False)

    @staticmethod
    def get_error_response(err):
        return {"success": False, "error": str(err)}


class UserTransaction(object):
    model = UserTransactionMaster
    serializer_class = UserTransactionMasterSerializer
    filter = Q()
    filter_dict = dict()

    def get_user_transaction_queryset(self):
        return self.model.objects.filter(
            self.filter, **self.filter_dict
        ).order_by("id")

    def set_filter(self, params):
        self.filter = Q()
        self.filter_dict = dict()
        if "id" in params:
            self.filter &= Q(id=params["id"])
        if "user_plaid_master_id" in params:
            self.filter &= Q(user_plaid_master__id=params["user_plaid_master_id"])
        if "user_id" in params:
            self.filter &= Q(user_plaid_master__user__id=params["user_id"])
        if "username" in params:
            self.filter &= Q(user_plaid_master__user__username=params["username"])
        if "institution_id" in params:
            self.filter &= Q(user_plaid_master__institution_id=params["institution_id"])
        if "active" in params:
            if params["active"] == 'true':
                self.filter &= Q(active=True)
            else:
                self.filter &= Q(active=False)

    @staticmethod
    def get_error_response(err):
        return {"success": False, "error": str(err)}


def validate_query_params(params):
    filter_params = [
        "id",
        "user_plaid_master_id",
        "user_id",
        "username",
        "institution_id",
        "active",
    ]
    pagination_param = "page"
    unaccepted_params = []
    for key in params:
        if key not in filter_params and key != pagination_param:
            unaccepted_params.append(key)
    if unaccepted_params:
        logger.error(
            f"validate_query_params:: Invalid query parameters {unaccepted_params},"
            f" choices are {filter_params}"
        )
        raise ValidationError(
            f"Invalid query parameters {unaccepted_params}, choices are {filter_params}"
        )
