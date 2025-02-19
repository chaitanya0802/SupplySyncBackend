from django.contrib import admin

from supplysyncapi.models import Warehouse, Section, ProductLot, Rack

# Register your models here.
admin.site.register(Warehouse)
admin.site.register(Section)
admin.site.register(Rack)
admin.site.register(ProductLot)