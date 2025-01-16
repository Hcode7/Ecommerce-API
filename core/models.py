from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from enum import Enum

# Create your models here.

User = get_user_model()

class SlugMixin(models.Model):
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)
    
    class Meta:
        abstract = True

class Category(SlugMixin):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150)

    def __str__(self):
        return self.name
    
class Product(SlugMixin):
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title 
    
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user.username}"
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Product {self.product} by {self.cart.user.username}"
    

class OrderStatus(Enum):
    PENDING = 'Pending'
    PAID = 'Paid'
    FAILED = 'Failed'

class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=250, default='Pending', choices=[(tag.name , tag.value ) for tag in OrderStatus])
    is_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.customer}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"OrderItem {self.id}"