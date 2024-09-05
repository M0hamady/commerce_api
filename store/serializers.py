from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Address, City, KeyFeature, Payment, Product, Basket, BasketItem, Order, OrderItem, Coupon
from django.db.models import OuterRef, Subquery


class KeyFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyFeature
        fields = ['id', 'feature_text','product']
class ProductSerializer(serializers.ModelSerializer):
    effective_price = serializers.SerializerMethodField()
    is_alive = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_effective_price(self, obj):
        return obj.get_effective_price()
    def get_is_alive(self,obj):
        if obj.inventory_count > 0 :
            return True
        return False
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Example: You can add more fields or manipulate existing ones here
        data['key_features'] = KeyFeatureSerializer(instance.key_features.all(), many=True).data
        return data

class BasketItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasketItem
        fields = ['product', 'quantity']

class BasketSerializer(serializers.ModelSerializer):
    items = BasketItemSerializer(many=True, read_only=True)

    class Meta:
        model = Basket
        fields = '__all__'
class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'shipment_fee','active']
class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_description = serializers.CharField(source='product.description', read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    quantity = serializers.IntegerField( read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'product_description', 'price', 'quantity', 'subtotal','product_image','is_ready']

    def create(self, validated_data):
        # Override create method if needed
        pass

 
class CheckoutSerializer(serializers.Serializer):
    status = serializers.CharField()
    invoice_url = serializers.CharField()

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'

class AddressSerializer(serializers.ModelSerializer):
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all())

    class Meta:
        model = Address
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Use CitySerializer for the city field in the response
        representation['city'] = CitySerializer(instance.city).data
        return representation

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'order',
            'amount',
            'transaction_id',
            'status',
            'created_at',
            'payment_id',
            'payment_gateway',
            'invoice_id',
            'track_id',
            'authorization_id',
            'transaction_date'
        ]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    last_payment = serializers.SerializerMethodField()
    all_payments = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = '__all__'

    def get_client_name(self, obj):
        return obj.user.username

    def get_last_payment(self, obj):
        # Subquery to fetch the latest completed payment
        latest_payment_subquery = Payment.objects.filter(
            order=OuterRef('pk'), status='completed'
        ).order_by('-created_at').values('id')[:1]
        
        latest_payment = Payment.objects.filter(id__in=Subquery(latest_payment_subquery))
        payment = latest_payment.first() if latest_payment.exists() else None
        
        return PaymentSerializer(payment).data if payment else None

    def get_all_payments(self, obj):
        # Fetch all completed payments
        payments = Payment.objects.filter(order=obj, status='completed')
        return PaymentSerializer(payments, many=True).data if payments.exists() else []
        return PaymentSerializer(payments, many=True).data if payments.exists() else []
class CreateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['user', 'total_amount']
# serializers.py

class StatisticsChartSerializer(serializers.Serializer):
    color = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    footer = serializers.CharField()
    chart = serializers.JSONField()
