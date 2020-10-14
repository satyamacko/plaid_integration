import plaid
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

client = plaid.Client(client_id=settings.PLAID_CLIENT_ID,
                      secret=settings.PLAID_SECRET,
                      environment=settings.PLAID_ENV)


@csrf_exempt
@api_view(['POST'])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
# @permission_classes([IsAuthenticated])
def get_link_token(request):
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
    print("get_access_token::", client, request, request.user, request.user.id, request.data)
    public_token = request.data['public_token']
    exchange_response = client.Item.public_token.exchange(public_token)
    print("get_access_token:: response - ", exchange_response)
    print('access token: ' + exchange_response.get('access_token'))
    print('item ID: ' + exchange_response.get('item_id'))
    return JsonResponse(exchange_response)


@api_view(['POST'])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
# @permission_classes([IsAuthenticated])
def get_user_transactions(request):
    try:
        print("get_user_transactions - ", client, request, request.user, request.user.id, request.data)
        access_token = request.data['access_token']
        response = client.Transactions.get(access_token,
                                           start_date='2020-08-01',
                                           end_date='2020-10-01')
        print("get_user_transactions:: response - ", response)
        transactions_json = {
            "transactions": response['transactions']
        }
        return JsonResponse(transactions_json)
    except plaid.errors as e:
        print("get_user_transactions:: Exception - ", str(e))
        return JsonResponse(str(e), safe=False)


