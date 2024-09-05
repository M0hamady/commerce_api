import json
from django.db import models

from api.models import User
from django.utils import timezone



class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    inventory_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(unique=True, blank=True, null=True)  # Unique and optional

    class Meta:
        ordering = ['position']  # Add this line to order by position by default

    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        if self.position is None:
            # Automatically set the position to the next available value
            max_position = Product.objects.aggregate(models.Max('position'))['position__max']
            self.position = (max_position or 0) + 1
        super().save(*args, **kwargs)  # Corrected line
        
    def get_effective_price(self):
        return self.offer_price if self.offer_price else self.price

class KeyFeature(models.Model):
    product = models.ForeignKey(Product, related_name='key_features', on_delete=models.CASCADE)
    feature_text = models.CharField(max_length=255)

    def __str__(self):
        return self.feature_text

class Basket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Basket {self.id} - {self.user.username}"

    def total_items(self):
        return self.items.count()  # Calculate total items in basket

    def total_price(self):
        return sum(item.subtotal() for item in self.items.all())


class BasketItem(models.Model):
    basket = models.ForeignKey(Basket, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Basket {self.basket.id}"

    def subtotal(self):
        return self.product.get_effective_price() * self.quantity


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2)  # Discount as a percentage
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    def __str__(self):
        return self.code




class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    shipment_fee = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL,null=True,blank=True)
    address_line = models.CharField(max_length=255)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    lat = models.CharField(max_length=50 , null=True , blank=True)  # Geographic point
    lng = models.CharField(max_length=50 , null=True , blank=True)  # Geographic point

    def __str__(self):
        return f"{self.address_line}, {self.city}, {self.state}, {self.country}"
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('online', 'Online'),
        ('cash', 'Cash'),
        ('controller', 'Via Controller'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    received_at = models.DateTimeField(null=True, blank=True)  # Date the order was received
    delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)  # Date the order was delivered
    packaged = models.BooleanField(default=False)
    printed = models.BooleanField(default=False)
    packaged_at = models.DateTimeField(null=True, blank=True)  # Date the order was packaged
    payment_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='online')
    shipping_address = models.ForeignKey(Address, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"
    def get_address_point(self):
        if self.shipping_address and self.shipping_address.lat and self.shipping_address.lng:
            return {"id": self.shipping_address.id, "location": {'lat':self.shipping_address.lat,'lng':self.shipping_address.lat}, "address": self.shipping_address.address_line}
        return None
    def apply_coupon(self):
        if self.coupon and self.coupon.is_active:
            discount_amount = (self.total_amount * self.coupon.discount) / 100
            self.total_amount -= discount_amount
            self.save()

    def mark_as_paid(self):
        self.paid = True
        self.payment_status = 'completed'
        self.save(update_fields=['paid', 'payment_status'])  # Update only these fields

    def mark_as_received(self):
        self.received = True
        self.received_at = timezone.now()
        self.save()

    def mark_as_delivered(self):
        self.delivered = True
        self.delivered_at = timezone.now()
        self.save()

    def mark_as_packaged(self):
        self.packaged = True
        self.packaged_at = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        if self.received and self.received_at is None:
            self.received_at = timezone.now()
        if self.delivered and self.delivered_at is None:
            self.delivered_at = timezone.now()
        if self.packaged and self.packaged_at is None:
            self.packaged_at = timezone.now()
        if self.paid == True:
            self.payment_status = 'completed'
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    is_ready = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.id}"

    def subtotal(self):
        return self.price * self.quantity

    def update_inventory(self):
        if self.product.inventory_count > self.quantity:
            self.product.inventory_count -= self.quantity
            self.product.save()
        else:
            raise ValueError("Insufficient inventory for this order item")

    def save(self, *args, **kwargs):
        # self.update_inventory()
        self.price = self.product.get_effective_price()
        super().save(*args, **kwargs)

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    payment_gateway = models.CharField(max_length=255, blank=True, null=True)
    invoice_id = models.CharField(max_length=255, blank=True, null=True)
    track_id = models.CharField(max_length=255, blank=True, null=True)
    authorization_id = models.CharField(max_length=255, blank=True, null=True)
    transaction_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Payment #{self.id} for Order #{self.order.id}"
    


