from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from django.utils import timezone
from rest_framework import serializers

from app.models import UserProfile, Section, Product, Rack


#serializer for user sign up
class UserSignUpSerializer(serializers.ModelSerializer):
    #validate the data
    email = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=[('Company', 'Company'),
                                            ('DistributionCentre', 'DistributionCentre'),
                                            ('LogisticsProvider', 'LogisticsProvider'),
                                            ('RetailStore', 'RetailStore')
                                            ])

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'role']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    # create user, assign permissions, add to group and add data toProfile
    def create(self, validated_data):
        email = validated_data.pop('email')
        role = validated_data.pop('role')

        #create user in User
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
        )

        #add user to group
        user_group = Group.objects.get(name=role)
        user.groups.add(user_group)

        #create user profile in UserProfile
        UserProfile.objects.create(user=user, email=email, role=role)
        return user


class UserTokenLoginSerializer(serializers.ModelSerializer):
    # data to validate
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

    class Meta:
        model = User
        fields = ['username', 'password']

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(request=self.context.get('request'), username=username, password=password)

        if not user:
            raise serializers.ValidationError('Wrong username or password', code='authorization')

        attrs['user'] = user
        return attrs


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['product_id', 'name', 'sku', 'description', 'value', 'weight']


class RackSearchSerializer(serializers.ModelSerializer):
    section_identifier = serializers.CharField(source='section_identifier.section_identifier')

    class Meta:
        model = Rack
        fields = ['rack_identifier', 'section_identifier']


class SectionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Section
        fields = ['section_identifier', 'description', 'total_racks']

    def create(self, validated_data):
        # Get the user from the context
        user = self.context['request'].user
        # Create the section with the user
        section = Section.objects.create(user=user,
                                         section_identifier=validated_data['section_identifier'],
                                         description=validated_data['description'],
                                         total_racks=validated_data['total_racks'],)
        return section


class RackSerializer(serializers.ModelSerializer):
    section_identifier = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all())
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Rack
        fields = ['rack_identifier', 'section_identifier', 'size', 'is_filled', 'product_id', 'quantity', 'product_added_date', 'product_removed_date']

    def create(self, validated_data):
        si = validated_data['section_identifier']
        pi = validated_data['product_id']

        # Get the User object based on the username
        section_identifier = Section.objects.get(section_identifier=si)
        product_id = Product.objects.get(product_id=pi)

        if validated_data.get('product_id') and validated_data.get('quantity') > 0:
            validated_data['product_added_date'] = timezone.now()

            # If no product, set the product_removed_date
        if validated_data.get('quantity') == 0:
            validated_data['product_removed_date'] = timezone.now()

        rack = Rack.objects.create(
            rack_identifier=validated_data['rack_identifier'],
            section_identifier=section_identifier,
            size=validated_data['size'],
            is_filled=validated_data['is_filled'],
            product_id=product_id,
            quantity=validated_data['quantity'],
            product_added_date=validated_data['product_added_date'],
            product_removed_date=validated_data['product_removed_date']
        )
        return rack


class RackUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rack
        fields = ['is_filled', 'product_id', 'quantity']


#demand prediction
class PredictionInputSerializer(serializers.Serializer):
    product_code = serializers.CharField(max_length=100, help_text="The code of the product for which demand is to be predicted.")
    target_date = serializers.DateField(help_text="The date for which the prediction is to be made, format YYYY-MM-DD.")

