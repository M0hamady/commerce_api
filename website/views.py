import time
from rest_framework import generics ,viewsets , status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.timezone import now
from django.db.models import Count
from .models import ContactMessage, Reply, Visit
from .serializers import ContactMessageSerializer, ReplySerializer, VisitSerializer
from django.utils import timezone as datetime
# import datetime
import requests
import json
from rest_framework.decorators import action

class CreateVisitView(generics.CreateAPIView):
    queryset = Visit.objects.all()
    serializer_class = VisitSerializer
    
    
    
class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.all()
    serializer_class = VisitSerializer

    @action(detail=False, methods=['get'], url_path='website-views-chart')
    def website_views_chart(self, request, *args, **kwargs):
        today = now().date()
        last_week = today - datetime.timedelta(days=6)
        
        visits = (
            Visit.objects.filter(created_at__date__gte=last_week)
            .extra(select={'day': 'date(created_at)'})
            .values('day')
            .annotate(views=Count('id'))
            .order_by('day')
        )
        
        # Initialize views data for 7 days with zero views
        views_data = {today - datetime.timedelta(days=i): 0 for i in range(7)}
        views_data = dict(sorted(views_data.items()))

        # Fill the views data
        for visit in visits:
            day = visit['day']  # 'day' is a string here
            day = datetime.datetime.strptime(day, '%Y-%m-%d').date()  # Convert to date object
            views_data[day] = visit['views']//2

        # Generate categories (days of the week)
        categories = [day.strftime('%a') for day in views_data.keys()]  # Using '%a' for abbreviated weekday names

        # Prepare the data to be returned
        series_data = list(views_data.values())

        response_data = {
            "type": "bar",
            "height": 220,
            "series": [
                {
                    "name": "Views",
                    "data": series_data,
                },
            ],
            "options": {
                "colors": "#388e3c",
                "plotOptions": {
                    "bar": {
                        "columnWidth": "16%",
                        "borderRadius": 8,
                    },
                },
                "xaxis": {
                    "categories": categories,
                },
            },
        }

        return Response(response_data, status=status.HTTP_200_OK)
    
    
class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        contact_message = self.get_object()
        reply_message = request.data.get('message')
        if reply_message:
            reply = Reply.objects.create(contact_message=contact_message, message=reply_message)
            self.send_whatsapp_message(contact_message.phone, reply_message)
            return Response({'status': 'reply sent'})
        else:
            return Response({'error': 'message content required'}, status=400)

    def send_whatsapp_message(self, phone, message):
        access_token = 'EAAR9Qk1ZCSOoBO5AvLoZB1OGrt4Vg6trBDaiWafZCLcCigu4S572hycKHBmTsZAJTLFHvNWmBmglLbDe4326RbMGHVp5tG2V9kZBvsOcdpqYLGjUIU1e8EiTgG58l4ZC0IYkB8p8hKUMDZAl35H6aziOyjwjZA9wmZB8pGMjnlOgtRJtsXP58YhLwm5o0oJX9vJdJJTVJSYGsgyV36Rt1iUs4MtEnSyjZCDLBMuaUZD'  # Replace with your actual access token
        business_account_id = '397668586757128'  # Replace with your actual business account ID
        phone_number_id = '390665374127970'  # Your Phone Number ID
        url = f'https://graph.facebook.com/v13.0/{phone_number_id}/messages'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Add phone number to the allowed list before sending the message
        self.add_allowed_phone_number(access_token, business_account_id, '+2'+phone)

        data = {
            'messaging_product': 'whatsapp',
            'to': '+2'+phone,
            'text': {
                'body': message
            }
        }
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response_data = response.json()

        # Print all keys and values from the response
        for key, value in response_data.items():
            print(f'{key}: {value}')
        
        # Extract message ID for status check
        message_id = response_data.get('messages', [{}])[0].get('id')
        if message_id:
            # Wait a few seconds before checking the status
            time.sleep(5)
            status_url = f'https://graph.facebook.com/v13.0/{message_id}'
            status_response = requests.get(status_url, headers=headers)
            status_data = status_response.json()
            
            # Print all keys and values from the status response
            for key, value in status_data.items():
                print(f'{key}: {value}')

        return response_data

    def add_allowed_phone_number(self, access_token, business_account_id, phone_number):
        url = f'https://graph.facebook.com/v13.0/{business_account_id}/phone_numbers'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        data = {
            'phone_number': phone_number,
            'verified_name': 'Test Number',
            'messaging_product': 'whatsapp'
        }
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response_data = response.json()

        # Print all keys and values from the response
        for key, value in response_data.items():
            print(f'{key}: {value}')

        return response_data    
        
    
    