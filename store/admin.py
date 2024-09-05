# api/admin.py

from django.contrib import admin
from .models import Address, City, KeyFeature, Payment, Product, Basket, BasketItem, Coupon, Order, OrderItem


class BasketItemInline(admin.TabularInline):
    model = BasketItem
    extra = 0


class KeyFeatureInline(admin.TabularInline):
    model = KeyFeature

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'offer_price', 'inventory_count', 'is_active', 'effective_price','position')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('effective_price',)

    inlines = [
        KeyFeatureInline,
    ]

    def effective_price(self, obj):
        return obj.get_effective_price()
    effective_price.short_description = 'Effective Price'

admin.site.register(KeyFeature)


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'total_items', 'total_price')
    list_filter = ('user', 'created_at')
    search_fields = ('user__username',)
    inlines = [BasketItemInline]

    def total_items(self, obj):
        return obj.total_items()
    
    def total_price(self, obj):
        return obj.total_price()


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount', 'is_active', 'valid_from', 'valid_to')
    list_filter = ('is_active', 'valid_from', 'valid_to')
    search_fields = ('code',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'created_at', 'payment_status', 'paid', 'received')
    list_filter = ('user', 'created_at', 'payment_status', 'paid', 'received')
    search_fields = ('user__username',)
    inlines = [OrderItemInline]
    actions = ['mark_as_paid', 'mark_as_received']

    def mark_as_paid(self, request, queryset):
        queryset.update(paid=True, payment_status='completed')
    
    mark_as_paid.short_description = 'Mark selected orders as paid'

    def mark_as_received(self, request, queryset):
        queryset.update(received=True)
    
    mark_as_received.short_description = 'Mark selected orders as received'

# admin.site.register(Address)
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'price', 'quantity', 'subtotal')
    list_filter = ('order__user', 'product')
    search_fields = ('order__user__username', 'product__name')
    readonly_fields = ('subtotal',)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'amount', 'transaction_id', 'status', 'created_at')
    search_fields = ('order__id', 'transaction_id', 'status')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at',)
    
    # If you want to make fields editable only when adding a new payment, you can override the get_readonly_fields method
    def get_readonly_fields(self, request, obj=None):
        if obj:  # If editing an existing object
            return self.readonly_fields + ('order', 'amount', 'transaction_id')
        return self.readonly_fields

    # If you want to customize how the form looks, you can use fieldsets
    fieldsets = (
        (None, {
            'fields': ('order', 'amount', 'transaction_id', 'status', 'created_at')
        }),
    )

# Register the Payment model with the admin class
admin.site.register(Payment, PaymentAdmin)


# Register all other models here if needed
# admin.site.register(Product, ProductAdmin)
# admin.site.register(Basket, BasketAdmin)
# admin.site.register(Coupon, CouponAdmin)
# admin.site.register(Order, OrderAdmin)
# admin.site.register(OrderItem, OrderItemAdmin)
@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'shipment_fee']
    search_fields = ['name']

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['address_line', 'city', 'state', 'country', 'postal_code']
    search_fields = ['address_line', 'city__name', 'state', 'country', 'postal_code']