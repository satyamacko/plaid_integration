import plaid
import structlog
from django.conf import settings
from django.http import JsonResponse
from plaid.errors import BaseError, InvalidRequestError
from rest_framework import status
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from plaidapis.models import WebhookCallbackLogs
from plaidapis.pagination import PaginationMixin
from plaidapis.tasks import exchange_public_token_task, process_transaction_callbacks_task
from plaidapis.utils import get_plaid_client, UserAccount, validate_query_params, ValidationError, UserTransaction

logger = structlog.get_logger()


@csrf_exempt
@api_view(['POST'])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
# @permission_classes([IsAuthenticated])
def get_link_token(request):
    client = get_plaid_client()
    print(client, request, request.user, request.user.id, request.data)
    response = client.LinkToken.create({
        'user': {
            'client_user_id': '123',
        },
        'products': ['transactions'],
        'client_name': 'My App',
        'country_codes': ['US'],
        'language': 'en',
        'webhook': 'https://webhook.sample.com',
    })
    print("get_link_token:: response - ", response)
    return JsonResponse(response)


@api_view(['POST'])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
# @permission_classes([IsAuthenticated])
def get_access_token(request):
    client = get_plaid_client()
    print("get_access_token::", client, request, request.user, request.user.id, request.data)
    public_token = request.data['public_token']
    exchange_response = client.Item.public_token.exchange(public_token)
    print("get_access_token:: response - ", exchange_response)
    print('access token: ' + exchange_response.get('access_token'))
    print('item ID: ' + exchange_response.get('item_id'))
    return JsonResponse(exchange_response)


@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def get_public_token_and_exchange(request):
    """
    This API is used on home page to let user connect with
    their bank accounts.
    """
    try:
        client = get_plaid_client()
        logger.info("get_public_token_and_exchange:: - ", request=request, request_user=request.user,
                    request_user_id=request.user.id, request_data=request.data)
        institution_id = request.query_params.get('institution_id')
        if institution_id is None:
            logger.warn("get_public_token_and_exchange:: institution_id is not present in query param. "
                        "Setting default ins_1")
        response = client.Sandbox.public_token.create(initial_products=['transactions'], institution_id=institution_id,
                                                      webhook='https://satyamsammi.free.beeceptor.com')
        public_token = response['public_token']
        exchange_public_token_task.delay(public_token, request.user.id, institution_id)
        res = {
            "success": True,
            "message": "Successfully connected to your bank account.",
            "data": response
        }
        return Response(
                res, status=status.HTTP_200_OK
            )
    except Exception as e:
        logger.error("get_public_token_and_exchange:: Exception - ", exception=str(e))
        res = {
            "success": False,
            "error": str(e)
        }
        return Response(
                res, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
def handle_transaction_webhook_callbacks(request):
    """
    This API is responsible to handle transaction callbacks
    asynchronously. We can implement the webhook verification to validate
    the correct source of callbacks.
    """
    try:
        logger.info("handle_transaction_webhook_callbacks", request=request)
        WebhookCallbackLogs.objects.create(payload=request.data)
        process_transaction_callbacks_task.delay(request.data)
        response = {
            "success": True,
            "message": "Successfully accepted the callback"
        }
        return Response(response, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error("handle_transaction_webhook_callbacks:: Exception - ", str(e))
        response = {
            "success": False,
            "error": str(e)
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


"""
Ideally, all the models should have encrypted ID as
a field. GET APIs should allow filtering only through
encrypted IDs as the mandatory query parameters to avoid 
direct access of these APIs on natural IDs.
"""


class UserAccountMasterListView(APIView, PaginationMixin, UserAccount):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            logger.info("UserAccountMasterListView:: Calling GET API", request_params=request.query_params)
            validate_query_params(request.query_params)
            self.set_filter(request.query_params)
        except ValidationError as e:
            logger.error(f"UserAccountMasterListView:: Get API Failed, ValidationError: {e}")
            return Response(
                self.get_error_response(e), status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"UserAccountMasterListView:: Get API Failed, Exception: {e}")
            return Response(
                self.get_error_response(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        try:
            page_number = (
                int(request.query_params.get("page"))
                if request.query_params.get("page")
                else 1
            )
            self.paginate(self.get_user_account_queryset(), page_number)
            if self.page:
                serializer = self.serializer_class(self.page, many=True)
            else:
                serializer = self.serializer_class(
                    self.get_user_account_queryset(), many=True
                )
        except Exception as e:
            logger.error(f"UserAccountMasterListView:: Get API Failed, Error: {e}")
            return Response(
                self.get_error_response(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response(
            {
                "success": True,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "count": self.result_count,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class UserTransactionMasterListView(APIView, PaginationMixin, UserTransaction):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            logger.info("UserTransactionMasterListView:: Calling GET API", request_params=request.query_params)
            validate_query_params(request.query_params)
            self.set_filter(request.query_params)
        except ValidationError as e:
            logger.error(f"UserTransactionMasterListView:: Get API Failed, ValidationError: {e}")
            return Response(
                self.get_error_response(e), status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"UserTransactionMasterListView:: Get API Failed, Exception: {e}")
            return Response(
                self.get_error_response(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        try:
            page_number = (
                int(request.query_params.get("page"))
                if request.query_params.get("page")
                else 1
            )
            self.paginate(self.get_user_transaction_queryset(), page_number)
            if self.page:
                serializer = self.serializer_class(self.page, many=True)
            else:
                serializer = self.serializer_class(
                    self.get_user_transaction_queryset(), many=True
                )
        except Exception as e:
            logger.error(f"UserTransactionMasterListView:: Get API Failed, Error: {e}")
            return Response(
                self.get_error_response(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response(
            {
                "success": True,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "count": self.result_count,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )