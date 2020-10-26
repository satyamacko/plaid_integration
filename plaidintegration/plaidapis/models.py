from django.db import models

from accounts.models import CustomUser


class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserPlaidMaster(TimeStampMixin):
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, null=False, db_index=True)
    access_token = models.CharField(max_length=128)
    item_id = models.CharField(max_length=128, db_index=True)
    request_id = models.CharField(max_length=64)
    institution_id = models.CharField(max_length=32)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username + '_institution_id_' + self.institution_id


class UserAccountMaster(TimeStampMixin):
    user_plaid_master = models.ForeignKey(UserPlaidMaster, on_delete=models.PROTECT, db_index=True)
    account_id = models.CharField(max_length=128)
    mask = models.CharField(max_length=32, null=True)
    account_name = models.CharField(max_length=128)
    account_official_name = models.CharField(max_length=128, null=True)
    type = models.CharField(max_length=128)
    subtype = models.CharField(max_length=128)

    def __str__(self):
        return str(self.user_plaid_master) + '_ac_name_' + self.account_name


class UserTransactionMaster(TimeStampMixin):
    user_plaid_master = models.ForeignKey(UserPlaidMaster, on_delete=models.PROTECT, db_index=True)
    account_id = models.CharField(max_length=128)
    user_account_master = models.ForeignKey(UserAccountMaster, on_delete=models.PROTECT, null=True, db_index=True)
    account_owner = models.CharField(max_length=128, null=True)
    transaction_id = models.CharField(max_length=128, db_index=True)
    amount = models.FloatField()
    name = models.CharField(max_length=128)
    merchant_name = models.CharField(max_length=128, null=True)
    category_id = models.IntegerField()
    category = models.JSONField(null=True)
    iso_currency_code = models.CharField(max_length=128, null=True)
    unofficial_currency_code = models.CharField(max_length=128, null=True)
    location = models.JSONField()
    payment_channel = models.CharField(max_length=128)
    pending = models.BooleanField(default=True)
    payment_meta = models.JSONField()
    active = models.BooleanField(default=True)
    date = models.DateField()
    authorized_date = models.DateField(null=True)


class WebhookCallbackLogs(TimeStampMixin):
    """
    This table can be used to log all the callbacks.
    """
    payload = models.JSONField()



