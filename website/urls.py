# urls.py
from django.urls import path, include
from .views import ContactMessageViewSet, CreateVisitView, VisitViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'visits', VisitViewSet, basename='visit')
router.register(r'contact-messages', ContactMessageViewSet)

urlpatterns = [
    path('visits/', CreateVisitView.as_view(), name='create-visit'),
    path('', include(router.urls)),

]
