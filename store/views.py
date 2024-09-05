from datetime import date, datetime, timedelta
from decimal import Decimal
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import AuthenticationFailed
from api.models import User
from .paymentMyFatorah import check_payment_status, get_all_payments, get_payment_token
from .models import Address, City, KeyFeature, Product, Basket, BasketItem, Order, OrderItem, Coupon
from .serializers import AddressSerializer, CheckoutSerializer, CitySerializer, KeyFeatureSerializer, PaymentSerializer, ProductSerializer, BasketSerializer, BasketItemSerializer, OrderSerializer, OrderItemSerializer, CouponSerializer, CreateOrderSerializer, StatisticsChartSerializer
from rest_framework_jwt.utils import jwt_decode_handler
from .models import Order, Payment        
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

def get_user_from_token(token):
    if not token:
        # Return response if no token is provided
        return Response({"authenticated": False, "message": "Token not provided"}, status=status.HTTP_404_NOT_FOUND)

    # Decode the token
    decoded_token = jwt_decode_handler(token)
    user_id =  decoded_token['user_id']

    if not user_id:
        # Return response if no user ID is found in the token
        return Response({"authenticated": False, "message": "Token not provided"}, status=status.HTTP_404_NOT_FOUND)

    try:
        # Try to get the user from the database
        user = User.objects.get(id=user_id)
        return user
    except User.DoesNotExist:
        # Return response if user does not exist
        return Response({"authenticated": False, "message": "Token not provided"}, status=status.HTTP_404_NOT_FOUND)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(Q(inventory_count__gt=0))
    serializer_class = ProductSerializer

class ProductViewManagerSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def update(self, request, *args, **kwargs):
        try:
            product = self.get_object()
            serializer = self.get_serializer(product, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except Exception as e:
            print(f"Error updating product: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        try:
            serializer.save()
        except Exception as e:
            print(f"Error during saving the product: {e}")
            raise e 



class KeyFeatureViewSet(viewsets.ModelViewSet):
    queryset = KeyFeature.objects.all()
    serializer_class = KeyFeatureSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        try:
            token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]
            user = get_user_from_token(token)  # Decode and verify the token
            request.user = user
        except Exception as e:
            print('Token error:', e)
            raise AuthenticationFailed('Invalid token.')

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        
class BasketViewSet(viewsets.ModelViewSet):
    queryset = Basket.objects.all()
    serializer_class = BasketSerializer

    @action(detail=True, methods=['post'])
    def add_to_basket(self, request, pk=None):
        basket = self.get_object()
        product = get_object_or_404(Product, id=request.data['product_id'])
        quantity = request.data.get('quantity', 1)
        if product.inventory_count < quantity:
            return Response({'detail': 'Insufficient inventory'}, status=status.HTTP_400_BAD_REQUEST)
        basket_item, created = BasketItem.objects.get_or_create(
            basket=basket,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            basket_item.quantity += quantity
            basket_item.save()
        return Response({'detail': 'Item added to basket'})

    @action(detail=True, methods=['post'])
    def create_order(self, request, pk=None):
        basket = self.get_object()
        if basket.items.count() == 0:
            return Response({'detail': 'Basket is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        order_data = {
            'user': basket.user.id,
            'total_amount': basket.total_price()
        }
        order_serializer = CreateOrderSerializer(data=order_data)
        if order_serializer.is_valid():
            order = order_serializer.save()
            for item in basket.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.get_effective_price(),
                    quantity=item.quantity
                )
            basket.items.all().delete()
            return Response(OrderSerializer(order).data)
        return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

# class OrderViewSet(viewsets.ModelViewSet):
#     queryset = Order.objects.all()
#     serializer_class = OrderSerializer

#     @action(detail=True, methods=['post'])
#     def apply_coupon(self, request, pk=None):
#         order = self.get_object()
#         code = request.data.get('code')
#         coupon = get_object_or_404(Coupon, code=code)
#         order.coupon = coupon
#         order.apply_coupon()
#         order.save()
#         serializer = self.get_serializer(order)
#         return Response(serializer.data)

#     @action(detail=True, methods=['post'])
#     def mark_as_paid(self, request, pk=None):
#         order = self.get_object()
#         order.mark_as_paid()
#         serializer = self.get_serializer(order)
#         return Response(serializer.data)

#     @action(detail=True, methods=['post'])
#     def mark_as_received(self, request, pk=None):
#         order = self.get_object()
#         order.mark_as_received()
#         serializer = self.get_serializer(order)
#         return Response(serializer.data)

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    
    
from django.db import transaction, IntegrityError



class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def create(self, request):
        user = request.user
        print(request.data)
        products = request.data.get('products', [])
        quantities = request.data.get('quantities', [])
        shippingAddress = request.data.get('shippingAddress')
        print(shippingAddress)
        
        if not products or not quantities or len(products) != len(quantities):
            return Response({'status': 'error', 'message': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)

        total_amount = 0
        
        try:
            with transaction.atomic():
                order = Order.objects.create(user=user, total_amount=total_amount)
                print("Step 1: Order created successfully.")

                for product_id, quantity in zip(products, quantities):
                    product = Product.objects.get(id=product_id)
                    price = product.get_effective_price()
                    quantity = int(quantity)
                    
                    # Check if sufficient inventory is available (if needed)
                    if product.inventory_count < quantity:
                        raise ValueError(f"Insufficient inventory for product {product.name}")
                    
                    # Create order item and update inventory
                    try:
                        OrderItem.objects.create(order=order, product=product, price=price, quantity=quantity)
                        total_amount += price * quantity
                        product.inventory_count -= quantity
                        product.save()
                        print(f"Step 2: Order item created for product {product.name}.")
                    except IntegrityError as e:
                        # Handle database integrity errors (e.g., duplicate entries) if necessary
                        raise ValueError(f"Error creating order item: {str(e)}")
                shipment_fee = Decimal(shippingAddress['city']['shipment_fee'])
                total_amount_with_shipment_fee = total_amount + shipment_fee 
                taxes = total_amount_with_shipment_fee * Decimal('0.01')
                # print(taxes)
                order.total_amount = total_amount + taxes
                order.shipping_address = Address.objects.get(id=shippingAddress['id'])
                order.save()
                print("Step 3: Order total amount updated.")

                # # Get the final payment token
                # final_token = get_payment_token(order.total_amount*100)
                # print("Final token for payment:", final_token)
                # print("Step 4: Payment token retrieved.")
                
                # Construct the payment URL
                print(order.total_amount)
                print(order.id)
                payment_url = get_payment_token(order.total_amount*100 ,order.id, order.user.username)
                print("Step 5: Payment URL constructed.")
                
                return Response({'status': 'success','customer_name':order.user.username, 'order_id': order.id,'amount':order.total_amount*100, 'url_payment': payment_url}, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(e)
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # List orders
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # Retrieve a specific order
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({'status': 'success', 'message': 'Order deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except ValidationError   as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def initial(self, request, *args, **kwargs):
        # Override the initial method to set the request user from the token
        super().initial(request, *args, **kwargs)
        try:
            # Extract token from the request headers
            token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]
            user = get_user_from_token(token)  # Decode and verify the token
            request.user = user
        except Exception as e:
            print('token err')
            # Raise an authentication failed exception if there is an issue
            raise AuthenticationFailed('Invalid token.')
        

class OrderStatisticsViewSet(viewsets.ViewSet):
    
    def list(self, request):
        today = date.today()
        total_orders = Order.objects.count()
        todays_orders = Order.objects.filter(created_at__date=today).count()
        un_packaged_orders = Order.objects.filter(paid=False,packaged=False).count()
        un_packaged_orders_paid = Order.objects.filter(paid=True,packaged=False).count()
        un_delivered_orders = Order.objects.filter(delivered=False).count()
        un_paid_orders = Order.objects.filter(payment_status='pending').count()
        
        data = {
            "total_orders": total_orders,
            "todays_orders": todays_orders,
            "un_packaged_orders": un_packaged_orders,
            "un_packaged_orders_paid": un_packaged_orders_paid,
            "un_delivered_orders": un_delivered_orders,
            "un_paid_orders": un_paid_orders,
        }
        return Response(data)   
class CheckoutViewSet(viewsets.ViewSet):
    queryset = Order.objects.all()
    serializer_class = CheckoutSerializer  # Define the serializer class here

    # @action(detail=False, methods=['get'])
    def get(self, request):
        print(1)
        try:
            orderId = request.query_params.get('orderId')
            order = get_object_or_404(Order, id=orderId)
            
            # Perform necessary checkout operations (e.g., payment processing)
            payment_url = get_payment_token(order.total_amount * 100, order.id)
            
            # Assuming invoice_url is generated during checkout process
            invoice_url = payment_url  # Replace with actual invoice URL
            # allPayments = get_all_payments()
            # print(allPayments)
            # print("allPayments")
            # print(check_payment_status('07074106862207691773'))
            # print('check_payment_status()')
            serializer ={'status': 'success', 'invoice_url': invoice_url}
            return Response(serializer, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def create(self, request, *args, **kwargs):
        # Implement create logic if needed
        pass
    
    def retrieve(self, request, *args, **kwargs):
        # Implement retrieve logic if needed
        pass
    
    def update(self, request, *args, **kwargs):
        # Implement update logic if needed
        pass
    
    def destroy(self, request, *args, **kwargs):
        # Implement destroy logic if needed
        pass
    
    def initial(self, request, *args, **kwargs):
        # Override the initial method to set the request user from the token
        super().initial(request, *args, **kwargs)
        try:
            # Extract token from the request headers
            token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]
            user = get_user_from_token(token)  # Decode and verify the token
            request.user = user
        except Exception as e:
            # Raise an authentication failed exception if there is an issue
            raise AuthenticationFailed('Invalid token.')
        
        
        

@method_decorator(csrf_exempt, name='dispatch')
class MyFatoorahCallbackView(View):

    def get(self, request, *args, **kwargs):
        try:
            print('try to get status')
            payment_id = request.GET.get('paymentId')
            order_id = request.GET.get('order_id')
            transaction_id = request.GET.get('id')
            print(order_id,'order id')
            if not payment_id or not transaction_id:
                return JsonResponse({'status': 'error', 'message': 'Missing paymentId or Id'}, status=400)

            # Simulate an API call to fetch payment details using payment_id and transaction_id
            # Replace this with actual API call
            try:
                order = Order.objects.get(id=order_id)
                print(order)
            except Order.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)

            response = self.fetch_payment_details(payment_id, transaction_id,order_id,order.total_amount)
            print(response)  # Debugging: print the response

            if not response.get('IsSuccess'):
                return JsonResponse({'status': 'error', 'message': 'Failed to fetch payment details'}, status=400)

            data = response.get('Data')
            invoice_id = data.get('InvoiceId')
            transaction_id = data.get('TransactionId')
            payment_status = data.get('InvoiceStatus')
            amount = data.get('InvoiceValue')
            print(order_id)
            try:
                order = Order.objects.get(id=order_id)
                print(order)
            except Order.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)

            payment, created = Payment.objects.get_or_create(order=order, defaults={'amount': amount, 'transaction_id': transaction_id,'invoice_id':invoice_id})
            print(payment)

            if payment_status == "Paid":
                order.mark_as_paid()
                payment.status = 'completed'
            elif payment_status == "Failed":
                payment.status = 'failed'
            
            payment.save()

            return JsonResponse({'status': 'success'}, status=200)

        except Payment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Payment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def fetch_payment_details(self, payment_id, transaction_id,user_defined_field,order_amount):
        # Mocked response for demonstration
        # Replace with actual API call to fetch payment details
        return {
            'IsSuccess': True,
            'Data': {
                'InvoiceId': 4105704,
                'TransactionId': transaction_id,
                'InvoiceStatus': 'Paid',
                'InvoiceValue': order_amount,
                'UserDefinedField': user_defined_field  # Replace with actual order ID
            }
        }

from rest_framework.views import APIView

class PaymentResponseViewSet(viewsets.ModelViewSet):
    def create(self, request):
        payment_data = request.data

        # Log the received payment data for debugging
        print("Received payment data:", payment_data)

        try:
            # Extract necessary information from the payment data
            order_id = payment_data.get('order_id')
            payment_status = payment_data.get('status')
            amount_cents = payment_data.get('amount_cents')

            # Extract additional security information from headers
            request_id = request.headers.get('ID')
            request_success = request.headers.get('Success')
            request_hmac = request.headers.get('HMAC')
            print(order_id,payment_status)
            # Validate the HMAC to ensure the request is from your agency
            secret_key = settings.SECRET_KEY  # or another key used for HMAC generation
            message = f'{request_id}{request_success}'
            # calculated_hmac = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()

            # if calculated_hmac != request_hmac:
            #     return Response({'status': 'error', 'message': 'Invalid HMAC'}, status=status.HTTP_403_FORBIDDEN)

            # Find the corresponding order
            order = Order.objects.get(id=order_id)

            # Update order status based on payment status
            if payment_status == "paid":
                order.status = 'PAID'
                order.payment_amount = amount_cents / 100  # Convert cents to the actual amount
                order.save()
                return Response({'status': 'success', 'message': 'Payment processed successfully'}, status=status.HTTP_200_OK)
            else:
                order.status = 'FAILED'
                order.save()
                # return Response({'status': 'error', 'message': 'Payment failed'}, status=status.HTTP_400_BAD_REQUEST)

        except Order.DoesNotExist:
            return Response({'status': 'error', 'message': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
        
        
        
        
# views.py


class StatisticsChartsDataViewSet(viewsets.ViewSet):

    def get_queryset(self):
        return Order.objects.all()

    @action(detail=False, methods=['get'])
    def statistics_charts_data(self, request):
        today = date.today()
        first_day_of_current_month = today.replace(day=1)
        end_date = first_day_of_current_month - timedelta(days=1)
        start_date = end_date.replace(day=1) - timedelta(days=243)

        # Query for daily sales data
        daily_sales_data = Order.objects.filter(payment_status='completed', created_at__range=[start_date, end_date]) \
            .annotate(month=TruncMonth('created_at')) \
            .values('month') \
            .annotate(total_sales=Sum('total_amount')) \
            .order_by('month')

        # Query for completed orders data
        completed_orders_data = Order.objects.filter(payment_status='completed', created_at__range=[start_date, end_date]) \
            .annotate(month=TruncMonth('created_at')) \
            .values('month') \
            .annotate(count=Count('id')) \
            .order_by('month')
        
        # Prepare months list for x-axis categories
        months = []
        for i in range(7, -1, -1):
            month_date = today - timedelta(days=30*i)
            month_name = month_date.strftime('%b')
            months.append(month_name)

        # Initialize lists to store data with zeros for each month
        daily_sales_values = [0] * len(months)
        completed_orders_values = [0] * len(months)

        # Fill in actual data where available
        for index, month_name in enumerate(months):
            print(month_name)
            month_date = datetime.strptime(month_name, '%b')
            month_number = month_date.month
            orders_count = Order.objects.filter(payment_status='completed', created_at__month=month_number)
            completed_orders_values[index] = orders_count.count()
            budget=0
            for total in orders_count:
                budget+=total.total_amount
            daily_sales_values[index] = budget

            # print(orders_count)
            # for daily_sales_entry in daily_sales_data:
            #     if daily_sales_entry['month'].strftime('%b') == month_name:
            #         daily_sales_values[index] = daily_sales_entry['total_sales']
                    
            #         break
            
        # Prepare response structure
        statistics_charts_data = [
            {
                "color": "white",
                "title": "monthly Sales",
                "description": "12% increase in today sales",
                "footer": "updated 4 min ago",
                "chart": {
                    "type": "line",
                    "height": 220,
                    "series": [
                        {
                            "name": "Sales",
                            "data": daily_sales_values,
                        }
                    ],
                    "options": {
                        "colors": ["#0288d1"],
                        "stroke": {
                            "lineCap": "round",
                        },
                        "markers": {
                            "size": 5,
                        },
                        "xaxis": {
                            "categories": months,
                        },
                    },
                },
            },
            {
                "color": "white",
                "title": "Completed orders",
                "description": "monthly orders",
                "footer": "updated in morning only",
                "chart": {
                    "type": "line",
                    "height": 220,
                    "series": [
                        {
                            "name": "Tasks",
                            "data": completed_orders_values,
                        }
                    ],
                    "options": {
                        "colors": ["#388e3c"],
                        "stroke": {
                            "lineCap": "round",
                        },
                        "markers": {
                            "size": 5,
                        },
                        "xaxis": {
                            "categories": months,
                        },
                    },
                },
            },
        ]

        return Response(statistics_charts_data)
    
    
    
    
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def initial(self, request, *args, **kwargs):
        # Override the initial method to set the request user from the token
        super().initial(request, *args, **kwargs)
        try:
            # Extract token from the request headers
            token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]
            user = get_user_from_token(token)  # Decode and verify the token
            request.user = user
        except Exception as e:
            print('Token error:', e)
            # Raise an authentication failed exception if there is an issue
            raise AuthenticationFailed('Invalid token.')

    def perform_create(self, serializer):
        # Custom behavior on creation if needed
        serializer.save()
        
        
        
class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    
    
    def create(self,request):
        address_data = request.data
        address_data['user']=request.user.id
        request.data['user']=request.user.id
        print(address_data)
        serializer = AddressSerializer(data=address_data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'message': 'Address created successfully','data':serializer.data}, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response({'status': 'error', 'message': 'Invalid address data', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        
    
    
    
    def initial(self, request, *args, **kwargs):
        # Override the initial method to set the request user from the token
        super().initial(request, *args, **kwargs)
        try:
            # Extract token from the request headers
            token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]
            user = get_user_from_token(token)  # Decode and verify the token
            request.user = user
        except Exception as e:
            print('Token error:', e) 
            # Raise an authentication failed exception if there is an issue
            raise AuthenticationFailed('Invalid token')
        
class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer        
        
        
        
class MyFatoorahWebhookViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['post'], url_path='myfatoorah-webhook', url_name='myfatoorah_webhook')
    def handle_webhook(self, request):
        try:
            payload = request.data
            print('____________________________________________________')
            print(payload)
            print('____________________________________________________')
            event_type = payload.get('EventType')
            event_data = payload.get('Data')

            event_handlers = {
                1: self.handle_transaction_status_changed,
                2: self.handle_refund_status_changed,
                3: self.handle_balance_transferred,
                4: self.handle_supplier_status_changed,
                5: self.handle_recurring_status_changed,
            }

            handler = event_handlers.get(event_type, self.handle_unknown_event)
            handler(event_data)

            return Response({'status': 'success'}, status=200)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=400)

    def handle_transaction_status_changed(self, data):
        order_id = data.get('OrderId')
        payment_id = data.get('PaymentId')
        status = data.get('PaymentStatus')
        transaction_id = data.get('TransactionId')

        try:
            order = Order.objects.get(id=order_id)
            payment = Payment.objects.get(order=order)

            payment.status = status
            payment.transaction_id = transaction_id
            payment.save()

            if status.lower() == 'paid':
                order.mark_as_paid()
            elif status.lower() == 'failed':
                order.payment_status = 'failed'
                order.save()

        except Order.DoesNotExist:
            print(f"Order with ID {order_id} does not exist.")
        except Payment.DoesNotExist:
            print(f"Payment for order ID {order_id} does not exist.")

    def handle_refund_status_changed(self, data):
        # Implement refund status handling logic
        pass

    def handle_balance_transferred(self, data):
        # Implement balance transferred handling logic
        pass

    def handle_supplier_status_changed(self, data):
        # Implement supplier status handling logic
        pass

    def handle_recurring_status_changed(self, data):
        # Implement recurring status handling logic
        pass

    def handle_unknown_event(self, data):
        # Implement logic for unknown events
        pass


        
        