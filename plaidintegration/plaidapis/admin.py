from django.contrib import admin

# Register your models here.
import plaidapis.models as m

admin.site.register(m.WebhookCallbackLogs)


@admin.register(m.UserPlaidMaster)
class UserPlaidMasterAdmin(admin.ModelAdmin):
    list_display = ("user", "institution_id")
    list_filter = ("institution_id",)
    search_fields = ("user", "institution_id")


@admin.register(m.UserAccountMaster)
class UserAccountMasterAdmin(admin.ModelAdmin):
    list_display = ("user_plaid_master", "account_name", "account_official_name", "type")
    list_filter = ("user_plaid_master", "account_name", "account_official_name", "type")
    search_fields = ("user_plaid_master", "account_name", "account_official_name", "type")


@admin.register(m.UserTransactionMaster)
class UserTransactionMasterAdmin(admin.ModelAdmin):
    list_display = ("user_plaid_master", "user_account_master", "name", "amount", "transaction_id")
    list_filter = ("user_plaid_master", "category_id")
    search_fields = ("user_plaid_master",)
