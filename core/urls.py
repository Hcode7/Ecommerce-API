from django.urls import path
from . import views


urlpatterns = [
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('create/', views.AddProduct.as_view(), name='create'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<slug:slug>/', views.AddToCartView.as_view(), name='cart-add'),
    path('cart/update/<int:cart_id>/', views.UpdateCart.as_view(), name='cart-update'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('orders/', views.OrdersView.as_view(), name='order-history'),
    path('payment-cancel/', views.PaymentCancel.as_view(), name='payment_cancel'),
]
