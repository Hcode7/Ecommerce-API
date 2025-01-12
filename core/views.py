from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from rest_framework import generics
import stripe.error
from .models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework.views import APIView
import stripe
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.conf import settings
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination

# Create your views here.

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['title' , 'price', 'created_at']
    search_fields = ['title', 'price']
    pagination_class = CustomPageNumberPagination

class ProductDetailView(generics.RetrieveAPIView):
    def get(self, *args, **kwargs):
        slug = kwargs.get('slug')
        product = get_object_or_404(Product, slug=slug)
        serializer = ProductSerializer(product)
        return Response(serializer.data)
    

class AddProduct(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]


class CartView(APIView):
    def get(self, request):
        cart = Cart.objects.filter(user=request.user).first()
        if not cart:
            return JsonResponse({'error': 'Cart not found'}, status=404)

        items = cart.cartitem_set.all().values('product__title', 'quantity', 'product__price')
        total = sum(item['product__price'] * item['quantity'] for item in items)
        return JsonResponse({'items': list(items), 'total': total})


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cartitem, created = CartItem.objects.get_or_create(cart=cart, product=product)

            if not created:
                cartitem.quantity += 1
                cartitem.save()
        return redirect('home')
    

class UpdateCart(APIView):
    def post(self, request, cart_id):
        quantity = int(request.data.get('quantity', 1))
        cart = get_object_or_404(Cart, user=request.user)
        try:
            cartitem = get_object_or_404(CartItem, cart=cart, id=cart_id)
        except CartItem.DoesNotExist:
            return Response({'detail' : "No CartItem matches the given query."}, status=status.HTTP_404_NOT_FOUND)
        if quantity > 0:
            cartitem.quantity = quantity
            cartitem.save()
            return Response({'message': 'Cart updated successfully'}, status=status.HTTP_200_OK)

        else:
            cartitem.delete()
            return Response({'message': 'Cart item removed successfully'}, status=status.HTTP_200_OK)

class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        stripe.api_key = settings.STRIPE_SEC_KEY
        if not request.user.is_authenticated:
            return JsonResponse({'message' : 'Your not authenitcate , you need to Login'}, status=401)
        
        cart = get_object_or_404(Cart, user=request.user)
        if not cart:
            return JsonResponse({'error' : 'CartItem is empty'}, status=400)
        
        cartitem = cart.cartitem_set.all()
        order = Order.objects.create(customer=request.user)

        total_price = 0
        for item in cartitem:
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
            total_price += item.product.price * item.quantity

        line_items = []
        for item in cartitem:
            new_data = {
                'price_data' : {
                    'currency' : 'usd',
                    'product_data' : {
                        'name' : item.product.title
                    },
                    'unit_amount' : int(item.product.price * 100)
                },
                'quantity' : item.quantity
            }
            line_items.append(new_data)
        try:
            stripe_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=request.build_absolute_uri(reverse('order-history')),
                cancel_url=request.build_absolute_uri(reverse('payment_cancel')),
            )
        except stripe.error.StripeError as e:
            return JsonResponse({'error' : str(e)}, status=400)
        
        cartitem.delete()
        cart.delete()

        return Response({
            'message': 'Checkout initiated',
            'total_price': total_price,
            'session_url': stripe_session.url,
        })
    
    
class OrdersView(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class PaymentCancel(APIView):
    def get(self):
        return JsonResponse({'message' : 'The payment is canceled'})