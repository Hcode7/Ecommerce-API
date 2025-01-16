from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from rest_framework import generics
import stripe.error
from .models import Product, Cart, CartItem, Order, OrderItem
from .serializers import ProductSerializer, CartSerializer, CartItemSerializer, OrderSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
import stripe
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.conf import settings
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets
from rest_framework.decorators import action

# Custom pagination
class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# Product List View
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['title', 'price', 'created_at']
    search_fields = ['title', 'price']
    pagination_class = CustomPageNumberPagination

    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_products = Product.objects.filter(is_featured=True)
        serializer = ProductSerializer(featured_products, many=True)
        return Response(serializer.data)
    
# Product Create View (Admin Only)
class AddProduct(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

# Cart ViewSet (Authenticated Users)
class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Cart Item ViewSet (Authenticated Users)
class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Ensure multiple items in the cart are returned
        cart = Cart.objects.filter(user=self.request.user).first()
        if cart:
            return CartItem.objects.filter(cart=cart)
        return CartItem.objects.none()

# Checkout ViewSet (Authenticated Users)
class CheckoutViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        stripe.api_key = settings.STRIPE_SEC_KEY
        
        if not request.user.is_authenticated:
            return JsonResponse({'message': 'You are not authenticated, please log in.'}, status=401)
        
        # Ensure the cart exists for the user
        cart = get_object_or_404(Cart, user=request.user)
        if cart.cartitem_set.count() == 0:
            return JsonResponse({'error': 'Your cart is empty.'}, status=400)
        
        order = Order.objects.create(customer=request.user)
        total_price = 0
        line_items = []

        # Create order items and line items for Stripe
        for item in cart.cartitem_set.all():
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
            total_price += item.product.price * item.quantity
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.product.title,
                    },
                    'unit_amount': int(item.product.price * 100),
                },
                'quantity': item.quantity,
            })

        # Create Stripe session
        try:
            stripe_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=request.build_absolute_uri(reverse('order-history')),
                cancel_url=request.build_absolute_uri(reverse('payment_cancel')),
            )
        except stripe.error.StripeError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        # Clean up the cart after checkout
        cart.cartitem_set.all().delete()
        
        return Response({
            'message': 'Checkout initiated.',
            'total_price': total_price,
            'session_url': stripe_session.url,
        })

class OrdersView(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class PaymentCancel(APIView):
    def get(self, request):
        return JsonResponse({'message': 'The payment has been canceled.'})
