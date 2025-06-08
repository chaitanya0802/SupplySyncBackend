from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Sum
from rest_framework import serializers
from supplysyncapi.models import Warehouse, Section, Rack, ProductLot


class UserSignUpSerializer(serializers.Serializer):
    """
    Serializer for user SignUp and create warehouse model - for manager
    """
    #validate the data type
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

    warehouseid = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    warehouse_name = serializers.CharField(max_length=50)
    location = serializers.CharField(max_length=150)
    size = serializers.FloatField()

    # Validate if the username(phoneno) or email already exists
    def validate(self, attrs):
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Username already exists"})

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists"})

        return attrs

    def create(self, validated_data):
        user = User.objects.create(username=validated_data['username'])
        user.set_password(validated_data['password'])
        user.save()

        #Create Warehouse (by manager)
        Warehouse.objects.create(
            user=user,
            warehouse_name=validated_data['warehouse_name'],
            warehouse_id=validated_data['warehouseid'],
            location=validated_data['location'],
            email=validated_data['email'],
            size=validated_data['size']
        )

        return 'success'


class SubordinateUserSignUpSerializer(serializers.Serializer):
    """
    for subordinate
    """
    # validate the data type
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

    # Validate if the username(phoneno) or email already exists
    def validate(self, attrs):
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Username already exists"})

        return attrs

    def create(self, validated_data):
        user = User.objects.create(username=validated_data['username'])
        user.set_password(validated_data['password'])
        user.save()

        return 'success'


class UserTokenLoginSerializer(serializers.Serializer):
    """
    Serializer for user Login
    """
    #data type - validate
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

    #validate if username and password exists
    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise serializers.ValidationError({"credentials": "Invalid username or password"})
            else:
                attrs['user'] = user

        return attrs


#Section
class AddSectionSerializer(serializers.ModelSerializer):
    """
    Serializer to add a Section only if the warehouse has enough space for it.
    """
    warehouse_id = serializers.CharField(max_length=150)
    size = serializers.IntegerField()

    class Meta:
        model = Section
        fields = ['warehouse_id', 'size']

    def create(self, validated_data):
        try:
            warehouse = Warehouse.objects.get(warehouse_id=validated_data['warehouse_id'])

            # Get total size of existing sections in the warehouse
            total_section_size = \
            Section.objects.filter(warehouse_id=validated_data['warehouse_id']).aggregate(total_size=Sum('size'))[
                'total_size'] or 0

            # Check if adding this section exceeds warehouse capacity
            if total_section_size + validated_data['size'] > warehouse.size:
                return "Not enough space in the warehouse for this section."

            # Create Section
            Section.objects.create(warehouse_id=warehouse,
                                   size=validated_data['size'])

            # Update Warehouse total_sections
            warehouse.total_sections = Section.objects.filter(warehouse_id=validated_data['warehouse_id']).count()
            warehouse.save()

            return f"Section added successfully"

        except Warehouse.DoesNotExist:
            raise serializers.ValidationError({"error": "No warehouse found"})

        except Exception as e:
            raise serializers.ValidationError(e)


class UpdateSectionSerializer(serializers.ModelSerializer):
    """
    Serializer to update a Section while ensuring Warehouse size constraints are maintained.
    """

    class Meta:
        model = Section
        fields = ['size']

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError({"error": "Request context is missing."})

        user = request.user
        warehouse = Warehouse.objects.get(user=user)

        # New section size
        new_size = validated_data.get('size', instance.size)

        # Calculate total section size if updated
        total_existing_size = sum(section.size for section in Section.objects.filter(user=user))
        total_new_size = total_existing_size - instance.size + new_size

        # Ensure warehouse size constraint is met
        if total_new_size > warehouse.size:
            return "Updating this section exceeds warehouse capacity."

        # Update section size
        instance.size = new_size
        instance.save()

        # Update warehouse total section size
        warehouse.total_sections = Section.objects.filter(user=user).count()
        warehouse.save()

        return instance


#Rack
class AddRackSerializer(serializers.ModelSerializer):
    """
    Serializer to add a Rack only if the section has enough space for it.
    """
    warehouse_id = serializers.CharField(max_length=150, write_only=True)
    section = serializers.IntegerField()
    size = serializers.IntegerField()

    class Meta:
        model = Rack
        fields = ['warehouse_id', 'section', 'size']

    def create(self, validated_data):
        try:
            # Retrieve the Section instance
            section = Section.objects.get(section_id=validated_data['section'])

            # Calculate total existing rack sizes in the section
            total_rack_size = Rack.objects.filter(section=section).aggregate(
                total_size=Sum('size')
            )['total_size'] or 0

            # Check if adding this rack exceeds section capacity
            if total_rack_size + validated_data['size'] > section.size:
                raise serializers.ValidationError({"error": "Not enough space in the section for this rack."})

            # Retrieve the Warehouse instance
            warehouse = Warehouse.objects.get(warehouse_id=validated_data['warehouse_id'])

            # Create the Rack (Pass instances, not IDs)
            Rack.objects.create(
                warehouse_id=warehouse,
                section=section,
                size=validated_data['size'],
            )

            # Update total racks in Section
            section.total_racks = Rack.objects.filter(section=section).count()
            section.save()

            # Update total racks in Warehouse
            warehouse.total_racks = Rack.objects.filter(warehouse_id=warehouse).count()
            warehouse.save()

            return f"Rack added successfully"

        except Section.DoesNotExist:
            raise serializers.ValidationError({"error": "Section does not exist."})

        except Warehouse.DoesNotExist:
            raise serializers.ValidationError({"error": "No warehouse found for this user."})

        except Exception as e:
            raise serializers.ValidationError(e)


class UpdateRackSerializer(serializers.ModelSerializer):
    """
    Serializer to update a Rack while updating Section & Warehouse accordingly.
    """

    class Meta:
        model = Rack
        fields = ['section', 'size']

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError({"error": "Request context is missing."})

        user = request.user
        warehouse = Warehouse.objects.get(user=user)

        # Store old section before updating
        old_section = instance.section

        # Update section if changed
        new_section = validated_data.get('section', instance.section)
        if new_section != old_section:
            if new_section.user != user:
                raise serializers.ValidationError({"error": "Unauthorized section change."})

            # Update Section Model: Reduce count from old section, add to new
            old_section.total_racks = max(0, old_section.total_racks - 1)
            old_section.is_filled = old_section.total_racks >= old_section.size  # Update is_filled status
            old_section.save()

            new_section.total_racks += 1
            new_section.is_filled = new_section.total_racks >= new_section.size
            new_section.save()

            # Assign new section to rack
            instance.section = new_section

        # Update Rack size
        instance.size = validated_data.get('size', instance.size)
        instance.save()

        # Update Warehouse total_racks count
        warehouse.total_racks = sum(section.total_racks for section in Section.objects.filter(user=user))
        warehouse.save()

        return instance


#ProductLot
class AddProductLotSerializer(serializers.ModelSerializer):
    """
    Serializer to add a product lot and update Rack & Section details
    """
    warehouse_id = serializers.CharField(max_length=150, write_only=True)
    rack = serializers.IntegerField()
    product_name = serializers.CharField(max_length=150)
    supplier_name = serializers.CharField(max_length=150)
    quantity = serializers.IntegerField()
    category = serializers.CharField(max_length=150)
    price = serializers.DecimalField(max_digits=100000 , decimal_places=2)
    lot_space = serializers.FloatField()

    class Meta:
        model = ProductLot
        fields = ['warehouse_id', 'rack', 'product_name', 'supplier_name', 'quantity',
                  'category', 'price', 'lot_space']

    def create(self, validated_data):
        try:
            rack = Rack.objects.get(rack_id=validated_data['rack'])
            section = rack.section  # Get the section associated with the rack

            # Check if rack has enough space
            if rack.size_filled + validated_data['lot_space'] > rack.size:
                return f'message": "Rack size is not enough for the given lot.'

            warehouse = Warehouse.objects.get(warehouse_id=validated_data['warehouse_id'])
            #Create ProductLot instance
            ProductLot.objects.create(warehouse_id=warehouse,
                                      rack=rack,
                                      product_name=validated_data['product_name'],
                                      supplier_name=validated_data['supplier_name'],
                                      quantity=validated_data['quantity'],
                                      category=validated_data['category'],
                                      price=validated_data['price'],
                                      lot_space=validated_data['lot_space']
                                      )

            # ---- Update Rack ----
            rack.total_products += validated_data.get('quantity', 0)
            rack.size_filled += validated_data.get("lot_space", 0)
            rack.is_filled = rack.size_filled == rack.size
            rack.save()

            # ---- Update Section ----
            section.size_filled += validated_data.get("lot_space", 0)
            section.is_filled = section.size_filled >= section.size
            section.save()

            # ---- Update Warehouse ----
            warehouse = Warehouse.objects.get(warehouse_id=validated_data['warehouse_id'])
            warehouse.size_filled += validated_data.get("lot_space", 0)
            warehouse.save()

            return f'ProductLot Added Successfully'

        except Exception as e:
            print(str(e))
            raise serializers.ValidationError(e)


class UpdateProductLotSerializer(serializers.ModelSerializer):
    """
    Serializer to update a ProductLot and adjust Rack & Section details accordingly
    """

    class Meta:
        model = ProductLot
        fields = ['product_name', 'supplier_name', 'quantity', 'category', 'price', 'lot_space']

    def update(self, instance, validated_data):
        try:
            request = self.context.get('request')

            if instance.user != request.user:
                raise serializers.ValidationError({"error": "Unauthorized access to this ProductLot."})

            rack = instance.rack
            section = rack.section
            warehouse = Warehouse.objects.get(user=request.user)

            # Calculate changes in quantity and lot space
            prev_quantity = instance.quantity
            prev_lot_space = instance.lot_space

            new_quantity = validated_data.get('quantity', instance.quantity)
            new_lot_space = validated_data.get('lot_space', instance.lot_space)

            lot_space_diff = new_lot_space - prev_lot_space

            # Check if the updated lot_space exceeds the rack capacity
            if rack.size_filled + lot_space_diff > rack.size:
                return "Not enough space in the rack for this update."

            # ---- Update ProductLot ----
            instance.product_name = validated_data.get('product_name', instance.product_name)
            instance.supplier_name = validated_data.get('supplier_name', instance.supplier_name)
            instance.quantity = new_quantity
            instance.category = validated_data.get('category', instance.category)
            instance.price = validated_data.get('price', instance.price)
            instance.lot_space = new_lot_space
            instance.save()

            # ---- Update Rack ----
            rack.total_products += (new_quantity - prev_quantity)
            rack.size_filled += lot_space_diff
            rack.is_filled = rack.size_filled >= rack.size
            rack.save()

            # ---- Update Section ----
            section.size_filled += lot_space_diff
            section.is_filled = section.size_filled >= section.size
            section.save()

            # ---- Update Warehouse ----
            warehouse.size_filled += lot_space_diff
            warehouse.save()

            return instance

        except Warehouse.DoesNotExist:
            raise serializers.ValidationError({"error": "No warehouse found for this user."})
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})


# Home Page Dashboard

# --------------- WAREHOUSE --------------------

class GetWarehouseDetailsSerializer(serializers.ModelSerializer):
    """
    to get warehouse details
    """
    percent_filled = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse
        fields = ['warehouse_name', 'percent_filled']

    def get_percent_filled(self, obj):
        if obj.size > 0:
            return (obj.size_filled / obj.size) * 100
        return 0


# --------------- Section --------------------

class SectionIdsSerializer(serializers.ModelSerializer):
    """
    to get section ids
    """

    class Meta:
        model = Section
        fields = ['section_id']


class SectionSerializer(serializers.ModelSerializer):
    """
    to get section details
    """

    class Meta:
        model = Section
        fields = ['section_id', 'size', 'total_racks', 'is_filled', 'size_filled']


class FilledSizeAndSectionIdSerializer(serializers.ModelSerializer):
    """
    filled-size vs section id
    """

    class Meta:
        model = Section
        fields = ['section_id', 'size_filled']


# --------------- Rack --------------------

class RackIdsSerializer(serializers.ModelSerializer):
    """
    to get rack ids
    """

    class Meta:
        model = Rack
        fields = ['rack_id']


class RackSerializer(serializers.ModelSerializer):
    """
    to get rack details
    """

    class Meta:
        model = Rack
        fields = ['rack_id', 'section', 'size', 'total_products', 'is_filled', 'size_filled']


class FilledSizeAndRackIdSerializer(serializers.ModelSerializer):
    """
    filled-size vs rack id
    """

    class Meta:
        model = Rack
        fields = ['rack_id', 'size_filled']


class ProductLotIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLot
        fields = ['product_lot_id']