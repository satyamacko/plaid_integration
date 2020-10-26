from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from plaidapis.models import UserAccountMaster, UserTransactionMaster


class UserAccountMasterSerializer(ModelSerializer):
    user_plaid_master_id = serializers.CharField(source="user_plaid_master.id")
    user_id = serializers.CharField(source="user_plaid_master.user.id")
    username = serializers.CharField(source="user_plaid_master.user.username")
    institution_id = serializers.CharField(source="user_plaid_master.institution_id")

    class Meta:
        model = UserAccountMaster
        fields = [
            "id",
            "user_plaid_master_id",
            "user_id",
            "username",
            "institution_id",
            "account_name",
            "mask",
            "account_official_name",
            "type",
            "subtype"
        ]


class UserTransactionMasterSerializer(ModelSerializer):
    user_plaid_master_id = serializers.CharField(source="user_plaid_master.id")
    user_id = serializers.CharField(source="user_plaid_master.user.id")
    username = serializers.CharField(source="user_plaid_master.user.username")
    institution_id = serializers.CharField(source="user_plaid_master.institution_id")

    class Meta:
        model = UserTransactionMaster
        fields = [
            "id",
            "user_plaid_master_id",
            "user_id",
            "username",
            "institution_id",
            "account_id",
            "account_owner",
            "transaction_id",
            "amount",
            "name",
            "merchant_name",
            "category_id",
            "category",
            "iso_currency_code",
            "unofficial_currency_code",
            "location",
            "payment_channel",
            "pending",
            "payment_meta",
            "date",
            "authorized_date"
        ]
