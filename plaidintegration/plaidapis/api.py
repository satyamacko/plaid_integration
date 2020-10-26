import structlog
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from plaidapis.pagination import PaginationMixin
from plaidapis.utils import UserAccount, validate_query_params, ValidationError, UserTransaction

logger = structlog.get_logger()

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