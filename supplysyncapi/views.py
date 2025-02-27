from datetime import datetime, timedelta
import joblib
import pandas as pd
from django.shortcuts import render
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from supplysyncapi.models import Section, Rack, ProductLot, Warehouse
from supplysyncapi.serializers import UserTokenLoginSerializer, UserSignUpSerializer, AddSectionSerializer, \
    UpdateSectionSerializer, AddRackSerializer, UpdateRackSerializer, AddProductLotSerializer, \
    UpdateProductLotSerializer, SectionIdsSerializer, SectionSerializer, \
    FilledSizeAndSectionIdSerializer, RackIdsSerializer, RackSerializer, FilledSizeAndRackIdSerializer


# Create your views here.

class UserSignUpView(APIView):
    """
    to sign up User - StorewayAPI
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer_instance = UserSignUpSerializer(data=request.data)
        if serializer_instance.is_valid():
            message = serializer_instance.save()  #call create
            return Response({'message': f'{message}'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer_instance.errors, status=status.HTTP_400_BAD_REQUEST)


class UserTokenLoginView(APIView):
    """
    to login User (Token-storewayapi)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer_instance = UserTokenLoginSerializer(data=request.data)
        if serializer_instance.is_valid():
            user = serializer_instance.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({'message': 'success', 'token': token.key}, status=status.HTTP_200_OK)
        else:
            return Response(serializer_instance.errors, status=status.HTTP_400_BAD_REQUEST)


#Section - CUD
class SectionCreateAPIView(APIView):
    """
    to add section for user warehouse
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer_instance = AddSectionSerializer(data=request.data, context={'request': request})
        if serializer_instance.is_valid():
            message = serializer_instance.save()
            return Response({'message': f'{message}'}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message":serializer_instance.errors}, status=status.HTTP_400_BAD_REQUEST)


class SectionUpdateAPIView(APIView):
    """
    to update section
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    #update
    def patch(self, request, section_id):
        try:
            section = Section.objects.get(section_id=section_id)
            if section.user == request.user:
                serializer_instance = UpdateSectionSerializer(section, data=request.data, partial=True)
                if serializer_instance.is_valid():
                    serializer_instance.save()
                    return Response({"message": "Section Updated Successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Unauthorised'}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SectionDeleteAPIView(APIView):
    """
    API view to delete a Section while updating Warehouse and Rack models accordingly.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, section_id):
        try:
            section = Section.objects.get(section_id=section_id)

            # Authorization check
            if section.user != request.user:
                return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch the associated Warehouse
            warehouse = Warehouse.objects.get(user=request.user)

            # Remove all racks associated with the section
            racks = Rack.objects.filter(section=section)
            for rack in racks:
                # Update warehouse total_racks
                warehouse.total_racks -= 1

                # Decrement total products and size in section
                section.total_racks = max(0, section.total_racks - 1)
                section.is_filled = section.total_racks >= section.size
                section.save()

                # Delete rack
                rack.delete()

            # Update warehouse total_sections count
            warehouse.total_sections = max(0, warehouse.total_sections - 1)
            warehouse.save()

            # Delete the section
            section.delete()

            return Response({'message': 'Section deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

        except Section.DoesNotExist:
            return Response({'error': 'Section not found'}, status=status.HTTP_404_NOT_FOUND)


#Racks CUD
class RackCreateAPIView(APIView):
    """
    to add rack for user warehouse
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer_instance = AddRackSerializer(data=request.data, context={'request': request})
        if serializer_instance.is_valid():
            message = serializer_instance.save()
            return Response({'message': f'{message}'}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": str(serializer_instance.errors)}, status=status.HTTP_400_BAD_REQUEST)


class RackUpdateAPIView(APIView):
    """
    to update rack
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, rack_id):
        try:
            return Rack.objects.get(pk=rack_id)
        except Rack.DoesNotExist:
            return None

    def put(self, request, rack_id):
        rack = self.get_object(rack_id)
        if not rack:
            return Response({"error": "Rack not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateRackSerializer(rack, data=request.data, partial=False, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Rack updated successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, rack_id):
        rack = self.get_object(rack_id)
        if not rack:
            return Response({"error": "Rack not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateRackSerializer(rack, data=request.data, partial=True, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Rack updated successfully.", "data": serializer.data},
                            status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RackDeleteAPIView(APIView):
    """
    API view to delete a rack while updating Section and Warehouse accordingly.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, rack_id):
        try:
            rack = Rack.objects.get(rack_id=rack_id)

            # Authorization check
            if rack.user != request.user:
                return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch associated Section and Warehouse
            section = rack.section
            warehouse = Warehouse.objects.get(user=request.user)

            # Reduce total racks in section and update is_filled
            section.total_racks = max(0, section.total_racks - 1)
            section.is_filled = section.total_racks >= section.size  # Update is_filled status
            section.save()

            # Update warehouse total_racks count
            warehouse.total_racks = sum(section.total_racks for section in Section.objects.filter(user=request.user))
            warehouse.save()

            # Delete the rack
            rack.delete()

            return Response({'message': 'Rack deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

        except Rack.DoesNotExist:
            return Response({'error': 'Rack not found'}, status=status.HTTP_404_NOT_FOUND)


#ProductLot CUD
class ProductLotCreateAPIView(APIView):
    """
    to add product lot for user warehouse
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer_instance = AddProductLotSerializer(data=request.data, context={'request': request})
        if serializer_instance.is_valid():
            message = serializer_instance.save()
            return Response({'message': f'{message}'}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": str(serializer_instance.errors)}, status=status.HTTP_400_BAD_REQUEST)


class UpdateProductLotAPIView(APIView):
    """
    API View to update a ProductLot
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, product_lot_id):
        try:
            # Get the ProductLot instance
            product_lot = ProductLot.objects.get(id=product_lot_id, user=request.user)

            # Serialize and validate data
            serializer = UpdateProductLotSerializer(product_lot, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "ProductLot updated successfully", "data": serializer.data},
                                status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except ProductLot.DoesNotExist:
            return Response({"error": "ProductLot not found or unauthorized access"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeleteProductLotAPIView(APIView):
    """
    API View to delete a ProductLot and update related models
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_lot_id):
        try:
            # Get the ProductLot instance
            product_lot = ProductLot.objects.get(id=product_lot_id, user=request.user)
            rack = product_lot.rack
            section = rack.section
            warehouse = Warehouse.objects.get(user=request.user)

            # Store values before deletion
            lot_space = product_lot.lot_space
            quantity = product_lot.quantity

            # Delete the ProductLot
            product_lot.delete()

            # ---- Update Rack ----
            rack.total_products = max(0, rack.total_products - quantity)
            rack.size_filled = max(0, rack.size_filled - lot_space)
            rack.is_filled = rack.size_filled >= rack.size  # Update is_filled status
            rack.save()

            # ---- Update Section ----
            section.size_filled = max(0, section.size_filled - lot_space)
            section.is_filled = section.size_filled >= section.size  # Update is_filled status
            section.save()

            # ---- Update Warehouse ----
            warehouse.size_filled = max(0, warehouse.size_filled - lot_space)
            warehouse.save()

            return Response({"message": "ProductLot deleted successfully"}, status=status.HTTP_200_OK)

        except ProductLot.DoesNotExist:
            return Response({"error": "ProductLot not found or unauthorized access"}, status=status.HTTP_404_NOT_FOUND)
        except Warehouse.DoesNotExist:
            return Response({"error": "Warehouse not found for this user"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Home Page Dashboard

# --------------- WAREHOUSE --------------------

class GetWarehouseDetailsView(APIView):
    """
    to get warehouse details
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            warehouse = Warehouse.objects.get(user=request.user)

            data = {
                "warehouse_name": warehouse.warehouse_name,
                "percent_filled": (warehouse.size_filled / warehouse.size) * 100,
                "total_sections": warehouse.total_sections,
                "total_racks": warehouse.total_racks
            }

            return Response(data, status=status.HTTP_200_OK)

        except Warehouse.DoesNotExist:
            return Response({"error": "Warehouse not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# --------------- Section --------------------

class GetSectionDetailsView(APIView):
    """
    to get section details
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            #percent sections filled
            total_sections = Section.objects.filter(user=request.user).count()
            total_filled_sections = Section.objects.filter(user=request.user,
                                                           is_filled=True).count()
            percent_section_filled = (total_filled_sections * 100) / total_sections

            #total empty sections
            total_empty_sections = Section.objects.filter(user=request.user,
                                                          size_filled=0.0).count()

            #total filled sections
            total_filled_sections = Section.objects.filter(user=request.user,
                                                           is_filled=True).count()

            data = {"percent_section_filled": percent_section_filled,
                    "total_empty_sections": total_empty_sections,
                    "total_filled_sections": total_filled_sections
                    }
            return Response(data, status=status.HTTP_200_OK)


        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetAllSectionIdsView(APIView):
    """
    to get ids of sections
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            section_ids = Section.objects.filter(user=request.user)
            serializer = SectionIdsSerializer(instance=section_ids, many=True)

            return Response(data=serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CheckSectionView(APIView):
    """"
    to check details
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        section = Section.objects.get(user=request.user, section_id=id)
        serializer = SectionSerializer(section)

        return Response(serializer.data, status=status.HTTP_200_OK)


class GetFilledSizeAndSectionId(APIView):
    """
    to get filled size and section id
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        section = Section.objects.filter(user=request.user)
        serializer = FilledSizeAndSectionIdSerializer(section, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


# --------------- Rack --------------------

class GetRackDetailsView(APIView):
    """
    to get rack details
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            #percent rack filled
            total_rack = Rack.objects.filter(user=request.user).count()
            total_filled_rack = Rack.objects.filter(user=request.user,
                                                    is_filled=True).count()
            percent_racks_filled = (total_filled_rack * 100) / total_rack

            #total empty racks
            total_empty_racks = Rack.objects.filter(user=request.user,
                                                    size_filled=0.0).count()

            #total filled racks
            total_filled_racks = Rack.objects.filter(user=request.user,
                                                     is_filled=True).count()

            data = {"percent_racks_filled": percent_racks_filled,
                    "total_empty_racks": total_empty_racks,
                    "total_filled_racks": total_filled_racks
                    }
            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetAllRacksIdsView(APIView):
    """
    to get ids of racks
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            rack_ids = Rack.objects.filter(user=request.user)
            serializer = RackIdsSerializer(instance=rack_ids, many=True)

            return Response(data=serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CheckRackView(APIView):
    """"
    to check details
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        rack = Rack.objects.get(user=request.user, rack_id=id)
        serializer = RackSerializer(rack)

        return Response(serializer.data, status=status.HTTP_200_OK)


class GetFilledSizeAndRackId(APIView):
    """
    to get filled size and rack id
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rack = Rack.objects.filter(user=request.user)
        serializer = FilledSizeAndRackIdSerializer(rack, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


#render html file
def index(request):
    return render(request, "supplysyncapi/index.html")


#load model
order_quantity_model = joblib.load("supplysyncapi/order_quantity_model_1.pkl")  # Model 1: Order Quantity Prediction
warehouse_space_model = joblib.load("supplysyncapi/warehouse_space_model_2.pkl")  # Model 2: Warehouse Space Prediction

#feature names
order_quantity_features = [
    "Year", "Month", "Day", "Product_ID", "Stock_Level",
    "Safety_Stock_Level", "Reorder_Point", "Seasonality",
    "Promotion_Flag", "Discount_Rate", "Competitor_Price", "Competitor_Promotion"
]

warehouse_space_features = [
    "Predicted_Order_Quantity", "Stock_Level", "Safety_Stock_Level",
    "Reorder_Point", "Warehouse_Location", "Region"
]

#label encodings
warehouse_location_mapping = {"Warehouse1": 0, "Warehouse2": 1, "Warehouse3": 2}
region_mapping = {"North": 0, "South": 1, "East": 2, "West": 3}


class GetPredictions(APIView):
    """
    API to predict Order Quantities and Warehouse Space for the next 7 days
    """

    def get(self, request):
        try:
            date_str = request.query_params.get('date')  # DD-MM-YYYY
            product_id = request.query_params.get('product_id')

            if not date_str or not product_id:
                return Response({"error": "Missing date or product_id"}, status=status.HTTP_400_BAD_REQUEST)

            # Convert date format
            try:
                base_date = datetime.strptime(date_str, "%d-%m-%Y")
            except ValueError:
                return Response({"error": "Invalid date format, expected DD-MM-YYYY"}, status=status.HTTP_400_BAD_REQUEST)

            product_id = int(product_id)
            predictions_list = []

            # Additional numeric features
            stock_level = 100
            safety_stock_level = 20
            reorder_point = 30
            seasonality = 1
            promotion_flag = 0
            discount_rate = 0.1
            competitor_price = 50
            competitor_promotion = 0

            # Convert categorical features to numeric using mappings
            warehouse_location = warehouse_location_mapping["Warehouse3"]
            region = region_mapping["East"]

            # Predictions for the next 7 days
            for i in range(7):
                current_date = base_date + timedelta(days=i)
                year, month, day = current_date.year, current_date.month, current_date.day

                # Prepare input features for Model 1 (Order Quantity Prediction)
                input_data_model1 = pd.DataFrame([[year, month, day, product_id, stock_level,
                                                   safety_stock_level, reorder_point, seasonality,
                                                   promotion_flag, discount_rate, competitor_price, competitor_promotion]],
                                                 columns=order_quantity_features)

                # Predict Order Quantity (Model 1)
                predicted_order_quantity = order_quantity_model.predict(input_data_model1)[0]

                # Prepare input features for Model 2 (Warehouse Space Prediction)
                input_data_model2 = pd.DataFrame([[predicted_order_quantity, stock_level, safety_stock_level,
                                                   reorder_point, warehouse_location, region]],
                                                 columns=warehouse_space_features)

                # Predict Warehouse Space (Model 2)
                warehouse_space_needed = warehouse_space_model.predict(input_data_model2)[0]

                predictions_list.append({
                    "date": current_date.strftime("%d-%m-%Y"),
                    "predicted_order_quantity": round(float(predicted_order_quantity), 2),
                    "estimated_warehouse_space_sqft": round(float(warehouse_space_needed), 2)
                })

            return Response({"predictions": predictions_list}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




