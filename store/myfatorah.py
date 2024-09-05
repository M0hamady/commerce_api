from django.conf import settings
import requests
import json
import sys

# Define Functions
base_url = settings.MYFATOORAH_API_URL
api_key = settings.MYFATOORAH_API_KEY
def check_data(key, response_data):
    return key in response_data.keys() and response_data[key] is not None

# Error Handle Function
def handle_response(response):
    if response.text == "":  # In case of empty response
        raise Exception("API key is not correct")

    response_data = response.json()
    response_keys = response_data.keys()

    if "IsSuccess" in response_keys and response_data["IsSuccess"] is True:
        return  # Successful
    elif check_data("ValidationErrors", response_data):
        error = []
        for error_detail in response_data["ValidationErrors"]:
            error.append([error_detail.get(key) for key in ["Name", "Error"]])
        raise Exception(f"Validation Errors: {error}")
    elif check_data("ErrorMessage", response_data):
        raise Exception(response_data["ErrorMessage"])
    elif check_data("Message", response_data):
        raise Exception(response_data["Message"])
    elif check_data("Data", response_data) and check_data("ErrorMessage", response_data["Data"]):
        raise Exception(response_data["Data"]["ErrorMessage"])
    else:
        raise Exception("An Error has occurred. API response: " + response.text)

# Call API Function
def call_api(api_url, api_key, request_data, request_type="POST"):
    request_data = json.dumps(request_data)
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + api_key}
    response = requests.request(request_type, api_url, data=request_data, headers=headers)
    handle_response(response)
    return response

# Send Payment endpoint Function
def send_payment(sendpay_data):
    api_url = base_url + "/v2/SendPayment"
    sendpay_response = call_api(api_url, api_key, sendpay_data).json()  # Receiving the response of MyFatoorah

    invoice_id = sendpay_response["Data"]["InvoiceId"]
    invoice_url = sendpay_response["Data"]["InvoiceURL"]
    # Send Payment output if successful
    print("InvoiceId: ", invoice_id,
          "\nInvoiceURL: ", invoice_url)
    return invoice_id, invoice_url

# Test Environment

# Live Environment
# base_url = "https://api.myfatoorah.com"
# api_key = "MyTokenValue" # Live token value to be placed here: https://myfatoorah.readme.io/docs/live-token

# SendPayment Request
sendpay_data = {
    "CustomerName": "mohammed",  # Mandatory Field ("string")
    "NotificationOption": "LNK",  # Mandatory Field ("LNK", "SMS", "EML", or "ALL")
    "InvoiceValue": 100,  # Mandatory Field (Number)
    # Optional Fields
    # "MobileCountryCode": "965",
    # "CustomerMobile": "12345678", # Mandatory if the NotificationOption = SMS or ALL
    # "CustomerEmail": "mail@company.com", # Mandatory if the NotificationOption = EML or ALL
    # "DisplayCurrencyIso": "KWD",
    # "CallBackUrl": "https://yoursite.com/success",
    # "ErrorUrl": "https://yoursite.com/error",
    # "Language": "en",
    # "CustomerReference": "noshipping-nosupplier",
    # "CustomerAddress": {
    #     "Block": "string",
    #     "Street": "string",
    #     "HouseBuildingNo": "string",
    #     "Address": "address",
    #     "AddressInstructions": "string"
    # },
    # "InvoiceItems": [
    #     {
    #         "ItemName": "string",
    #         "Quantity": 20,
    #         "UnitPrice": 5
    #     }
    # ]
}

try:
    send_payment(sendpay_data)
except Exception as e:
    ex_type, ex_value, ex_traceback = sys.exc_info()
    print("Exception type : %s " % ex_type.__name__)
    print("Exception message : %s" % ex_value)
