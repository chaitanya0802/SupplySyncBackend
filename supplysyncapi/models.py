from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class Warehouse(models.Model):
    warehouse_id = models.CharField(max_length=50, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile') #
    warehouse_name = models.CharField(max_length=50)
    size = models.FloatField()
    location = models.CharField(max_length=150)
    email = models.EmailField()
    size_filled = models.FloatField(blank=True, null=True, default=0)   #
    total_sections = models.IntegerField(blank=True, null=True, default=0)     #
    total_racks = models.IntegerField(blank=True, null=True, default=0)    #
    warehouse_create_time = models.DateTimeField(auto_now_add=True)   #

    def __str__(self):
        return f"{self.user.username} ({self.warehouse_name})"


class Section(models.Model):
    section_id = models.AutoField(primary_key=True)     #
    warehouse_id = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    size = models.FloatField()
    total_racks = models.IntegerField(default=0)     #
    is_filled = models.BooleanField(default=False)      #
    size_filled = models.FloatField(blank=True, null=True, default=0)   #

    def __str__(self):
        return f"id: {self.section_id} for: ({self.warehouse_id})"


class Rack(models.Model):
    rack_id = models.AutoField(primary_key=True)        #
    warehouse_id = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    size = models.FloatField()
    total_products = models.IntegerField(null=True, blank=True, default=0)     #
    size_filled = models.FloatField(blank=True, null=True, default=0)      #
    is_filled = models.BooleanField(default=False)      #

    def __str__(self):
        return f"id: {self.rack_id}   in section: {self.section.section_id}   for: ({self.warehouse_id.warehouse_id})"


class ProductLot(models.Model):
    product_lot_id = models.AutoField(primary_key=True)     #
    rack = models.ForeignKey(Rack, on_delete=models.CASCADE)
    warehouse_id = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    supplier_name = models.CharField(max_length=255)
    quantity = models.IntegerField()
    category = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    lot_space = models.FloatField()
    date_added = models.DateField(auto_now_add=True)    #

    def __str__(self):
        return f"id: {self.product_lot_id} in rack: {self.rack.rack_id} for: ({self.warehouse_id.warehouse_id})"



