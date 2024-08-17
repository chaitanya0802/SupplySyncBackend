from django.contrib.auth.models import User
from django.db import models


# for user and its data
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(verbose_name="email address", max_length=255, )
    role = models.CharField(max_length=20, default='')

    def __str__(self):
        return self.user.username


#for Products in Warehouse
class Product(models.Model):
    product_id = models.CharField(max_length=100, unique=True, primary_key=True, default='')
    sku = models.CharField(max_length=100, unique=True)  # Stock Keeping Unit
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True,
                                 blank=True)  # Optional, weight of the product

    def __str__(self):
        return self.product_id


#for section(Warehouse) of user
class Section(models.Model):
    section_identifier = models.CharField(max_length=100, unique=True, primary_key=True, default='')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    total_racks = models.IntegerField()

    def __str__(self):
        return self.section_identifier


#for Racks of Section
class Rack(models.Model):
    rack_identifier = models.CharField(primary_key=True, max_length=100, unique=True, default='')
    section_identifier = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='racks')
    size = models.CharField(max_length=50)  #Width x Depth x Height -volume
    is_filled = models.BooleanField(default=False)
    product_id = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=0)  #total number of that product stored in that rack
    product_added_date = models.DateTimeField(null=True, blank=True)
    product_removed_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.rack_identifier

#for Order calls
#todo migrate
class OrderCall(models.Model):
    order_id = models.CharField(primary_key=True, max_length=100, unique=True)
    order_date = models.DateField
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
