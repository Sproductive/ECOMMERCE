from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
# class Hash_table(models.Model): customer
class User(AbstractUser):
    # User = AbstractUser
    is_email_verified = models.BooleanField(default=False)
    cash = models.DecimalField(max_digits=10, default=1000, decimal_places=2)
    profile_pic = models.ImageField(upload_to="profile_pics/", default="profile_pics/default_image.png")
    buyer = models.BooleanField(default=False)
    cart = models.ManyToManyField('Products', related_name="cart_items", blank=True, default=None)
    # hash = models.CharField(primary_key=True, max_length=64)

#  the browser stores the cookies in it's cookie storage and therefore we can access the account from there
# the login function takes a the request and user object as parameters then checks if the uer object is an instance of the user model in django then it creates a session for the user by setting a session key in the request session this session key is a unique identifier associated with user's session
    # the login function the marks the user as aucthnticated for the currenct session by by setting a pecific attribute in the session like request.session[''] which holds the userid


class Notifications(models.Model):
    class NotificationType(models.TextChoices):
        BID_PLACED = "BS", "bid_placed"
        OUTBIDDED = "OB", "outbidded"
        DEFAULT = "D", "default"
        DELIVERED = "DEL", "delivered"
        ORDER_PLACED = "OP", "order_placed"
        DELIVERY_STATUS = "DS", "delivered_status"
        AUCTION_ITEM_WON = "AIW", "auction_item_won"
        AUCTION_ITEM_LOST = "AIL", "auction_item_lost"

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")    
    type = models.CharField(max_length=3,
                                         choices=NotificationType.choices,
                                         default=NotificationType.DEFAULT
                                        )
    data = models.CharField(max_length=100,default=None)
    seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Products(models.Model):
    product_id = models.BigAutoField(primary_key=True)
    seller_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="seller")
    # product_hash = models.ManyToManyField(Hash_table, blank=True)
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='item_images/')
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=8, decimal_places=2)
    max_bid = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    current_bid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0, null=True)
    Sold = models.BooleanField(default=False)
    current_bid_user = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True, related_name="current_buyer")
    last_bidding_datetime = models.DateTimeField(
        default=None,                # Make the field non-editable once set
        null=True,       # Allow the field to be null initially (if needed)
        blank=True,      # Allow the field to be blank initially (if needed)
    )


class Reviews(models.Model):
    review_id = models.BigAutoField(primary_key=True)
    product_id = models.ForeignKey(Products, on_delete=models.CASCADE, related_name="product")
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="User")
    rating = models.SmallIntegerField(
        validators = [MinValueValidator(0), MaxValueValidator(10)]
    )
    comments = models.CharField(max_length=500)
    verifed = models.BooleanField()

class Payment(models.Model):
    # the first value is stored in the database and the second is the human readable version
    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = 'CC', 'Credit Card'
        DEBIT_CARD = 'DC', 'Debit Card'
        PAYPAL = 'PP', 'PayPal'
        NET_BANKING = 'NB' , 'NetBanking'
        UPI = 'UPI', 'UPI/ Google Pay/ Phone pe/ Paytm'
        CASH_ON_DELIVERY = 'COD', 'Cash on Delivery'

    class StatusChoices(models.TextChoices):
        pending = "pending"
        in_progress = "in progress"
        completed = "completed"
        processing = "processing"
        cancelled = "cancelled"

    payment_id = models.BigAutoField(primary_key=True)
    product_id = models.ForeignKey(Products, on_delete=models.DO_NOTHING)
    user_id = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        choices=PaymentMethod.choices, 
        default=PaymentMethod.CREDIT_CARD, 
        max_length=3
    )
    # sometimes data bases get corrupt then ch
    payment_status = models.CharField(
        choices=StatusChoices.choices,
        default=StatusChoices.pending,
        max_length=40
    )

class Bids(models.Model):
    bid_id = models.IntegerField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Products, on_delete=models.CASCADE)
    bid = models.DecimalField(max_digits=10, decimal_places=2)
    bid_time = models.DateTimeField(default=timezone.now, editable=False)
    # user_bid = models.(User, )

class Orders(models.Model):
    OrderID = models.BigAutoField(primary_key=True)
    OrderItemID = models.ForeignKey(Products ,on_delete=models.PROTECT)
    buyerID =  models.ForeignKey(User, on_delete=models.CASCADE)
    OrderDate = models.DateTimeField(auto_now_add=True)
    OrderPrice = models.DecimalField(max_digits=10, decimal_places=2)
    Quantity = models.IntegerField(
        # validators are used in integer fields
        validators = [MinValueValidator(1), MaxValueValidator(300)]
    )
    # decimal must have max_digits and decimal_places
    TotalAmount = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    def save(self, *args, **kwargs):
        TotalAmount = self.OrderPrice * self.Quantity
        super().save(*args, **kwargs)






