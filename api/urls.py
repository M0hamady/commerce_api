from django.urls import include, path
from .views import  CustomLoginView, CustomObtainTokenView, LogoutView, UserFileView, VerifyTokenView, RefreshTokenView, UserRegistrationView
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('token/', CustomObtainTokenView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('token/verify/', VerifyTokenView.as_view(), name='token_verify'),
    path('register/user/',UserRegistrationView.as_view(), name='user-registration'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user-file/', UserFileView.as_view(), name='user-file'),
    path('login/', CustomLoginView.as_view(), name='custom-login'),
    path('', include(router.urls)),

]