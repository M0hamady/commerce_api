# Import necessary libraries
from decimal import Decimal
import json
import requests
from django.conf import settings

# Define the function to get payment token from PayMob API
def get_payment_token(amount_cents):
    headers = {
        'Content-Type': 'application/json',
    }
    # Step 1: Obtain auth token
    api_key = settings.PAYMOB_API_KEY  # Replace with your actual PayMob API key
    payment_url = 'https://accept.paymob.com/'
    step1_data = {
        "api_key": api_key
    }

    try:
        response = requests.post(f"{payment_url}api/auth/tokens", json=step1_data)
        response_data = response.json()
        first_step_token = response_data.get('token')
        print('creating step 1',first_step_token)


        if not first_step_token:
            raise ValueError('Failed to get first step token from PayMob.')

        # Step 2: Create order
        step2_data = {
            "auth_token": first_step_token,
            "amount_cents": str(Decimal(amount_cents)),
            "currency": "EGP",
            "items": [],
            "delivery_needed": "false"
        }
        # json_data = json.dumps(step2_data)

        print('------------------------------------------')
        response = requests.post(f"{payment_url}api/ecommerce/orders", json=step2_data,headers=headers)
        print('------------------------------------------')
        response_data = response.json()
        order_id = response_data.get('id')

        if not order_id:
            raise ValueError('Failed to create order on PayMob.')

        # Step 3: Obtain payment token
        step3_data = {
            "auth_token": first_step_token,
            "amount_cents": int(amount_cents),
            "expiration": 3600,
            "order_id": order_id,
            "billing_data": {
                "apartment": "803",
                "email": "claudette09@exa.com",
                "floor": "42",
                "first_name": "Clifford",
                "street": "Ethan Land",
                "building": "8028",
                "phone_number": "+86(8)9135210487",
                "shipping_method": "PKG",
                "postal_code": "01898",
                "city": "Jaskolskiburgh",
                "country": "CR",
                "last_name": "Nicolas",
                "state": "Utah"
            },
            "currency": "EGP",
            "integration_id": "3740968"
        }

        response = requests.post(f"{payment_url}api/acceptance/payment_keys", json=step3_data)
        print(f"Response JSON content: {response.json()}")
        response_data = response.json()
        final_token = response_data.get('token')
        print(3)

        if not final_token:
            raise ValueError('Failed to get final payment token from PayMob.')
        print('final token from paymob :',final_token)
        return final_token

    except Exception as e:
        # Handle exceptions as per your application's requirements
        raise e
