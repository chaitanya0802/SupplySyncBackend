import joblib
import matplotlib
from django.contrib.auth.models import User
from django.views import View
from rest_framework import status, generics
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
matplotlib.use('Agg')  # Use the Agg backend for non-GUI rendering
import os
import matplotlib.pyplot as plt
import pandas as pd
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from django.utils.timezone import now
from SupplySyncBackend import settings
from app.models import Section, Rack, Product
from app.serializers import UserSignUpSerializer, UserTokenLoginSerializer, SectionSerializer, RackSerializer, \
    ProductSerializer, RackUpdateSerializer, RackSearchSerializer, PredictionInputSerializer


# Create your views here.
class UserSignUp(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserSignUpSerializer

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')

        #check if user already exists
        if User.objects.filter(username=username).exists():
            return Response({'message': 'Phone no. already used (Try Login)'})

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({'message': 'success'}, status=status.HTTP_201_CREATED)


class UserTokenLogin(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserTokenLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            return Response({'message': 'Wrong username or password'})

        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'message': 'success', 'token': token.key}, status=status.HTTP_200_OK)


#todo implement at FE
class SearchRackByProductView(APIView):

    def get(self, request, product_id):
        # Filter the racks by product_id
        racks = Rack.objects.filter(product_id=product_id)

        if not racks.exists():
            return Response({"detail": "No racks found for the given product_id."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RackSearchSerializer(racks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductCreateAPIView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def perform_create(self, serializer):
        serializer.save()


class SectionCreateAPIView(generics.CreateAPIView):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RackCreateAPIView(generics.CreateAPIView):
    queryset = Rack.objects.all()
    serializer_class = RackSerializer

#update rack
class RackUpdateView(generics.UpdateAPIView):
    queryset = Rack.objects.all()
    serializer_class = RackUpdateSerializer
    lookup_field = 'rack_identifier'


#section_identifiers x total_racks bar graph
class SectionIDTRAPIView(APIView):

    def get(self, request, *args, **kwargs):
        visualization_title = 'Inventory Racks by Section'
        # Query the Section data
        sections = Section.objects.all()

        section_identifiers = [section.section_identifier for section in sections]
        total_racks = [section.total_racks for section in sections]

        plt.figure(figsize=(10, 6))
        plt.bar(section_identifiers, total_racks, color='skyblue')

        plt.xlabel('Section Identifier', fontsize=14)
        plt.ylabel('Total Racks', fontsize=14)

        #filename
        filename = f'section_inventory_{now().strftime("%Y%m%d%H%M%S")}.png'
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        plt.tight_layout()
        plt.savefig(file_path)
        plt.close()

        file_url = request.build_absolute_uri(settings.MEDIA_URL + filename)
        return JsonResponse({'title': visualization_title, 'imageurl': file_url}, status=201)


#rack_identifiers x quantities bar graph
class RackIDQAPIView(APIView):

    def get(self, request, *args, **kwargs):
        visualization_title = 'Product Quantity by Rack'
        racks = Rack.objects.all()

        rack_identifiers = [rack.rack_identifier for rack in racks]
        quantities = [rack.quantity for rack in racks]

        plt.figure(figsize=(10, 6))
        plt.bar(rack_identifiers, quantities, color='lightcoral')

        plt.xlabel('Rack Identifier', fontsize=14)
        plt.ylabel('Quantity', fontsize=14)

        filename = f'rack_inventory_{now().strftime("%Y%m%d%H%M%S")}.png'
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        plt.tight_layout()
        plt.savefig(file_path)
        plt.close()

        file_url = request.build_absolute_uri(settings.MEDIA_URL + filename)
        return JsonResponse({'title': visualization_title, 'imageurl': file_url}, status=201)


#rack_identifier x size bar graph
class RackIDSAPIView(APIView):

    def get(self, request, *args, **kwargs):
        visualization_title = 'Size by Rack'
        racks = Rack.objects.all()

        rack_identifiers = [rack.rack_identifier for rack in racks]
        size = [rack.size for rack in racks]

        plt.figure(figsize=(10, 6))
        plt.bar(rack_identifiers, size, color='red')

        plt.xlabel('Rack Identifier', fontsize=14)
        plt.ylabel('Size', fontsize=14)

        filename = f'rack_inventory_{now().strftime("%Y%m%d%H%M%S")}.png'
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        plt.tight_layout()
        plt.savefig(file_path)
        plt.close()

        file_url = request.build_absolute_uri(settings.MEDIA_URL + filename)
        return JsonResponse({'title': visualization_title, 'imageurl': file_url}, status=201)


#todo- check
#rack_identifier x is_filled bar graph
class RackIDFAPIView(APIView):

    def get(self, request, *args, **kwargs):
        visualization_title = 'IsFilled? by Rack'
        racks = Rack.objects.all()

        rack_identifiers = [rack.rack_identifier for rack in racks]
        #1 if rack is filled
        is_filled = []
        for rack in racks:
            if rack.is_filled:
                is_filled.append(1)
            else:
                is_filled.append(0)

        plt.figure(figsize=(10, 6))
        plt.ylim(0, 1)  #y axis range
        plt.bar(rack_identifiers, is_filled, color='blue')

        plt.xlabel('Rack Identifier', fontsize=14)
        plt.ylabel('Is filled?', fontsize=14)

        filename = f'rack_inventory_{now().strftime("%Y%m%d%H%M%S")}.png'
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        plt.tight_layout()
        plt.savefig(file_path)
        plt.close()

        file_url = request.build_absolute_uri(settings.MEDIA_URL + filename)
        return JsonResponse({'title': visualization_title, 'imageurl': file_url}, status=201)


#rack_identifier x date
class RackIDDAPIView(APIView):

    def get(self, request, *args, **kwargs):
        visualization_title = 'Date Added/Removed by Rack'

        racks = Rack.objects.all()

        fig, ax = plt.subplots(figsize=(10, 6))

        for rack in racks:
            dates = []
            quantities = []

            if rack.product_added_date:
                dates.append(rack.product_added_date)
                quantities.append(rack.quantity)

            if rack.product_removed_date:
                dates.append(rack.product_removed_date)
                quantities.append(0)  #Quantity =zero when product is removed

            if dates and quantities:
                ax.plot(dates, quantities, label=f'Rack {rack.rack_identifier}')

        ax.set_xlabel('Date')
        ax.set_ylabel('Quantity')
        ax.legend()

        filename = f'rack_inventory_{now().strftime("%Y%m%d%H%M%S")}.png'
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        plt.tight_layout()
        plt.savefig(file_path)
        plt.close()

        file_url = request.build_absolute_uri(settings.MEDIA_URL + filename)
        return JsonResponse({'title': visualization_title, 'imageurl': file_url}, status=201)


class QuantityVsTimeView(View):

    def get(self, request, *args, **kwargs):
        visualization_title = 'Quantity Stored in Warehouse vs Time'

        section = Section.objects.get(section_identifier=1)
        racks = Rack.objects.filter(section_identifier=section)

        # Prepare data
        dates = []
        quantities = []
        total_quantity = 0

        for rack in racks:
            if rack.product_added_date:
                dates.append(rack.product_added_date)
                total_quantity += rack.quantity
                quantities.append(total_quantity)

            if rack.product_removed_date:
                dates.append(rack.product_removed_date)
                total_quantity -= rack.quantity
                quantities.append(total_quantity)

        # Plotting
        plt.figure(figsize=(10, 6))
        plt.plot(dates, quantities, label=f'Section {section.section_identifier}', marker='o')
        plt.xlabel('Date')
        plt.ylabel('Total Quantity')
        plt.title('Quantity Stored in Warehouse vs Time')
        plt.legend()
        plt.grid(True)

        filename = f'rack_inventory_{now().strftime("%Y%m%d%H%M%S")}.png'
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        plt.tight_layout()
        plt.savefig(file_path)
        plt.close()

        file_url = request.build_absolute_uri(settings.MEDIA_URL + filename)
        return JsonResponse({'title': visualization_title, 'imageurl': file_url}, status=201)


#todo order calls view

# demand_prediction
# Load the dataset and preprocess it globally
data = pd.read_csv('app/ml_data/Historical Product Demand.csv')
data['Date'] = pd.to_datetime(data['Date'], format='%Y/%m/%d')
data = data.sort_values(by='Date')
grouped_data = data.groupby(['Product_Code', 'Date'])['Order_Demand'].sum().reset_index()
pivoted_data = grouped_data.pivot(index='Date', columns='Product_Code', values='Order_Demand').fillna(0)


def load_sarima_model(product_code):
    # Load the pre-trained model from a file
    filename = f'app/ml_data/sarima_model_{product_code}.pkl'
    sarima_result = joblib.load(filename)
    return sarima_result


def predict_demand(sarima_result, target_date):
    target_date = pd.to_datetime(target_date)
    last_date = pivoted_data.index[-1]

    if target_date > last_date:
        steps = (target_date - last_date).days
        forecast = sarima_result.get_forecast(steps=steps)
        prediction = forecast.predicted_mean.iloc[-1]
    else:
        prediction = sarima_result.get_prediction(start=target_date, end=target_date).predicted_mean.iloc[0]

    return prediction


class PredictionAPIView(APIView):
    def post(self, request):
        serializer = PredictionInputSerializer(data=request.data)
        if serializer.is_valid():
            product_code = serializer.validated_data['product_code']
            target_date = serializer.validated_data['target_date']

            sarima_result = load_sarima_model(product_code)
            predicted_demand = predict_demand(sarima_result, target_date)

            return Response({
                "predicted_demand": predicted_demand
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#todo complete
class PredictionLPAPIView(APIView):
    pass
