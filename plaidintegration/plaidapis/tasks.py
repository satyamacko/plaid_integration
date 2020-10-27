from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from plaid.errors import APIError, InstitutionError

from accounts.models import CustomUser
from plaidapis.models import UserPlaidMaster, UserAccountMaster
from plaidapis.utils import update_webhook_url, get_plaid_client, fetch_user_accounts, update_user_transactions, \
    fetch_saved_user_accounts, remove_user_transactions

logger = get_task_logger(__name__)


@shared_task
def exchange_public_token_task(public_token, user_id, institution_id):
    """
    This task is called after the user has generated a public token
    while connecting to his bank account.
    """
    try:
        user = CustomUser.objects.filter(id=user_id)[0]
        client = get_plaid_client()
        record = UserPlaidMaster.objects.filter(user=user_id, institution_id=institution_id, active=True)
        logger.info(f'exchange_public_token_task:: Record - {record}')
        if record.exists():
            # We can also check if the existing access token is still valid by
            # querying item data and accordingly set it's active status as false
            # and create a new entry if required
            logger.info(f'exchange_public_token_task:: Record already exists for user_id - {user_id} and '
                        f'institution_id - {institution_id}')
            # updating new user accounts
            fetch_user_accounts_and_save_task.delay(record[0].id)
            return
        res = client.Item.public_token.exchange(public_token)
        # Ideally, We should encrypt the access token while saving in DB
        # and same Key should be used to decrypt the access token
        # while calling any Plaid APIs.
        plaid_master_record = UserPlaidMaster.objects.create(user=user, institution_id=institution_id,
                                                             access_token=res.get('access_token'),
                                                             item_id=res.get('item_id'),
                                                             request_id=res.get('request_id'))
        fetch_user_accounts_and_save_task.delay(plaid_master_record.id)
    except (APIError, InstitutionError) as e:
        # retry this.
        logger.error(f'exchange_public_token_task:: APIError Exception - {str(e)} , type -{e.type} request_id - '
                     f'{e.request_id}, error_code - {e.code}, user_id - {user_id}, institution_id - {institution_id} ')
        exchange_public_token_task.delay(public_token, user_id, institution_id)
    except Exception as e:
        logger.error(f'exchange_public_token_task:: Exception - {str(e)}, user_id - {user_id},'
                     f' institution_id - {institution_id}')


@shared_task
def fetch_user_accounts_and_save_task(plaid_master_record_id):
    """
    This task is currently getting triggered when the user tries
    to login through a new account and a new entry is created in
    UserPlaidMaster table.
    """
    try:
        logger.info(f'fetch_user_accounts_and_save_task:: Executing task, plaid_master_record_id - '
                    f'{plaid_master_record_id}')
        plaid_master_record = UserPlaidMaster.objects.filter(id=plaid_master_record_id)[0]
        response = fetch_user_accounts(plaid_master_record.access_token)
        if response is None:
            logger.error(f'fetch_user_accounts_and_save_task:: Unable to fetch user accounts.'
                         f'user_plaid_master_id= {plaid_master_record_id}')
            return
        saved_accounts_map = fetch_saved_user_accounts(plaid_master_record)
        saved_accounts_count = len(saved_accounts_map)
        api_accounts_count = len(response.get('accounts'))
        counter = 0
        for account in response.get('accounts'):
            # If we are calling this function multiple times for same user,
            # then we should check if the account already exists or not.
            account_id = account.get('account_id')
            if account_id not in saved_accounts_map.keys():
                logger.info(f'fetch_user_accounts_and_save_task:: saving account - {account_id}')
                UserAccountMaster.objects.create(user_plaid_master=plaid_master_record,
                                                 account_id=account_id,
                                                 mask=account.get('mask'),
                                                 account_name=account.get('name'),
                                                 account_official_name=account.get('official_name'),
                                                 type=account.get('type'),
                                                 subtype=account.get('subtype'))
                counter = counter + 1
        logger.info(f'fetch_user_accounts_and_save_task:: task_done plaid_master_record_id - {plaid_master_record_id},'
                    f'api_accounts_count - {api_accounts_count}, saved_accounts_count - {saved_accounts_count},'
                    f'accounts added - {counter}')
    except (APIError, InstitutionError) as e:
        # Retry for this.
        logger.error(f'fetch_user_accounts_and_save_task:: Plaid_Exception - {str(e)}, type - {e.type}, '
                     f'plaid_master_record_id - {plaid_master_record_id}. Retrying for this.')
        fetch_user_accounts_and_save_task.delay(plaid_master_record_id)
    except Exception as e:
        logger.error(f'fetch_user_accounts_and_save_task:: Exception - {str(e)}, plaid_master_record_id - '
                     f'{plaid_master_record_id}')


@shared_task
def process_transaction_callbacks_task(request_data):
    try:
        logger.info(f'process_transaction_callbacks_task:: request - {request_data} ')
        item_id = request_data.get('item_id')
        plaid_master_record = UserPlaidMaster.objects.filter(item_id=item_id)[0]
        webhook_code = request_data.get('webhook_code')
        end_date = date.today().strftime('%Y-%m-%d')
        if request_data.get('webhook_type') == "TRANSACTIONS":
            if webhook_code == "INITIAL_UPDATE":
                # We can ignore the initial update to avoid parallel read
                # and write of transactions for a particular item_id, since
                # HISTORICAL_UPDATE callback might be processed in parallel to this.
                logger.info(f'process_transaction_callbacks_task:: ignoring INITIAL_UPDATE for item_id - {item_id}'
                            f'and  plaid_master_record - {plaid_master_record}')
                return
            elif webhook_code == "HISTORICAL_UPDATE":
                start_date = (date.today() - relativedelta(years=2)).strftime('%Y-%m-%d')
                update_user_transactions(plaid_master_record, start_date, end_date)
            elif webhook_code == "DEFAULT_UPDATE":
                start_date = (date.today() - timedelta(7)).strftime('%Y-%m-%d')
                update_user_transactions(plaid_master_record, start_date, end_date)
            elif webhook_code == "TRANSACTIONS_REMOVED":
                remove_user_transactions(item_id, request_data.get('removed_transactions'))
            else:
                logger.error(f'process_transaction_callbacks_task:: invalid_webhook_code - {webhook_code} ,'
                             f' item_id - {item_id}')
        else:
            logger.warn(f'process_transaction_callbacks_task:: received non transaction callback')
    except (APIError, InstitutionError) as e:
        # Retry for this.
        logger.error(f'process_transaction_callbacks_task:: Plaid_Exception - {str(e)}, type - {e.type}, '
                     f'request - {request_data}. Retrying for this.')
        process_transaction_callbacks_task.delay(request_data)
    except Exception as e:
        logger.error(f'process_transaction_callbacks_task:: Exception - {str(e)}')
