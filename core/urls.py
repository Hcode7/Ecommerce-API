from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, AddProduct, CartViewSet, CartItemViewSet, CheckoutViewSet, OrdersView, PaymentCancel

# Initialize router
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'cart-items', CartItemViewSet, basename='cart-item')
router.register(r'checkout', CheckoutViewSet, basename='checkout')

urlpatterns = [
    # Register the viewsets with the router
    path('', include(router.urls)),
    
    # Custom routes for adding products and orders
    path('add-product/', AddProduct.as_view(), name='add-product'),
    path('orders/', OrdersView.as_view(), name='orders'),
    
    # Stripe payment cancel route
    path('payment-cancel/', PaymentCancel.as_view(), name='payment_cancel'),
]
