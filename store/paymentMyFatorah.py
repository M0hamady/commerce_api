import json
from decimal import Decimal
from django.conf import settings
import requests

import logging

logger = logging.getLogger(__name__)

def get_payment_token(amount, order_id, customer_name):
    """
    Function to get payment token from MyFatoorah API.

    :param amount: The amount in cents
    :param order_id: The order ID
    :param customer_name: The name of the customer
    :return: Payment URL or None if an error occurs
    """
    base_url = settings.MYFATOORAH_API_URL
    api_key = settings.MYFATOORAH_API_KEY
    invoice_value = Decimal(amount) / Decimal('100.00')  # Convert amount to decimal format

    callback_url = f"https://luxury-sophia-cosmetics.com/payment/status/{order_id}/"  # Replace with your actual callback URL

    request_data = {
        "CustomerName": customer_name,
        "NotificationOption": "LNK",  # Replace with actual notification option if needed
        "InvoiceValue": str(invoice_value),  # Invoice value as a string
        "CurrencyIso": "EGP",  # Currency ISO code for Egyptian Pound
        "CallBackUrl": callback_url,  # Callback URL for payment status
        "UserDefinedField": str(order_id),  # Include the order ID
        "CustomerCountry": "Egypt"  # Customer's country
    }

    def call_api(api_url, api_key, request_data, request_type="POST"):
        """
        Helper function to call MyFatoorah API.

        :param api_url: API URL
        :param api_key: API key
        :param request_data: Data to send in the request
        :param request_type: Type of the request (GET, POST, etc.)
        :return: Response data or raises an exception on failure
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        try:
            response = requests.request(request_type, api_url, data=json.dumps(request_data), headers=headers)
            response_data = response.json()
            print(response_data)
            
            if response.status_code == 200 and response_data.get("IsSuccess"):
                return response_data["Data"]["InvoiceURL"]
            else:
                error_message = response_data.get('ErrorMessage', 'Unknown error')
                raise Exception(f"Failed to get payment token: {error_message}")
        
        except Exception as e:
            logger.error(f"API call failed: {str(e)}")
            print(f"API call failed: {str(e)}")
            
            raise Exception(f"API call failed: {str(e)}")

    api_url = f"{base_url}/v2/SendPayment"
    try:
        payment_url = call_api(api_url, api_key, request_data)
        print(payment_url)
        return payment_url
    except Exception as e:
        logger.error(f"Error in get_payment_token: {str(e)}")
        return None
def get_all_payments():
    """
    Function to get all payments from MyFatoorah API.

    :return: JSON response of all payments
    """
    url = f"{settings.MYFATOORAH_API_URL}/v2/GetAllPayments"
    headers = {
        'Authorization': f'Bearer {settings.MYFATOORAH_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    return response.json()

def check_payment_status(invoice_id):
    """
    Function to check payment status by invoice ID.

    :param invoice_id: The invoice ID to check status for
    :return: JSON response of payment status
    """
    url = f"{settings.MYFATOORAH_API_URL}/v2/GetPaymentStatus"
    headers = {
        'Authorization': f'Bearer {settings.MYFATOORAH_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "Key": invoice_id,
        "KeyType": "InvoiceId"
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()
