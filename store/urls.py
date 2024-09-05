from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import  AddressViewSet, CheckoutViewSet, CityViewSet, KeyFeatureViewSet, MyFatoorahCallbackView, MyFatoorahWebhookViewSet, OrderStatisticsViewSet, PaymentResponseViewSet, PaymentViewSet, ProductViewManagerSet, ProductViewSet, BasketViewSet, OrderViewSet, OrderItemViewSet, CouponViewSet, StatisticsChartsDataViewSet
router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'key-features', KeyFeatureViewSet)
router.register(r'products-manager', ProductViewManagerSet)
router.register(r'baskets', BasketViewSet)
router.register(r'orders', OrderViewSet,basename='order')
router.register(r'order-items', OrderItemViewSet)
router.register(r'coupons', CouponViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'payment-response', PaymentResponseViewSet, basename='payment-response')
router.register(r'checkout', CheckoutViewSet, basename='order-checkout')
router.register(r'order-statistics', OrderStatisticsViewSet, basename='order-statistics')
router.register(r'statistics', StatisticsChartsDataViewSet, basename='statistics-charts-data')
router.register(r'addresses', AddressViewSet)
router.register(r'webhooks', MyFatoorahWebhookViewSet, basename='webhooks')
router.register(r'cities', CityViewSet)


# router = DefaultRouter()
# router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('baskets/<int:pk>/add-to-basket/', BasketViewSet.as_view({'post': 'add_to_basket'}), name='add-to-basket'),
    path('baskets/<int:pk>/create-order/', BasketViewSet.as_view({'post': 'create_order'}), name='create-order'),
    path('orders/<int:pk>/apply-coupon/', OrderViewSet.as_view({'post': 'apply_coupon'}), name='apply-coupon'),
    path('orders/<int:pk>/mark-as-paid/', OrderViewSet.as_view({'post': 'mark_as_paid'}), name='mark-as-paid'),
    path('orders/<int:pk>/mark-as-received/', OrderViewSet.as_view({'post': 'mark_as_received'}), name='mark-as-received'),
    path('Orders/payment/status/', MyFatoorahCallbackView.as_view(), name='myfatoorah_callback'),


        # path('api/payment-response/', PaymentResponseViewSet.as_view(), name='payment-response'),

    # path('create_order/', create_order, name='create_order'),

]
