from django.urls import path

from supplysyncapi.views import UserSignUpView, UserTokenLoginView, SectionCreateAPIView, SectionUpdateAPIView, \
    SectionDeleteAPIView, RackCreateAPIView, RackUpdateAPIView, RackDeleteAPIView, ProductLotCreateAPIView, \
    UpdateProductLotAPIView, DeleteProductLotAPIView, GetWarehouseDetailsView, GetSectionDetailsView, \
    GetAllSectionIdsView, CheckSectionView, GetFilledSizeAndSectionId, GetRackDetailsView, CheckRackView, \
    GetFilledSizeAndRackId, GetAllRacksIdsView, \
    index, GetPredictions

urlpatterns = [
    #auth
    path('signup', UserSignUpView.as_view(), name='signup'),
    path('login', UserTokenLoginView.as_view(), name='login'),


    #Section CUD
    path('add-section', SectionCreateAPIView.as_view(), name='add-warehouse-section'),
    path('update-section/<str:section_id>', SectionUpdateAPIView.as_view(), name='update-warehouse-section'),
    path('delete-section/<str:section_id>', SectionDeleteAPIView.as_view(), name='delete-warehouse-section'),


    #Rack CUD
    path('add-rack', RackCreateAPIView.as_view(), name='add-warehouse-rack'),
    path('update-rack/<str:rack_id>', RackUpdateAPIView.as_view(), name='update-warehouse-rack'),
    path('delete-rack/<str:rack_id>', RackDeleteAPIView.as_view(), name='delete-warehouse-rack'),


    #ProductLot CUD
    path('add-productlot', ProductLotCreateAPIView.as_view(), name='productlot-warehouse-rack'),
    path('update-productlot/<str:product_lot_id>', UpdateProductLotAPIView.as_view(), name='productlot-warehouse-rack'),
    path('delete-productlot/<str:product_lot_id>', DeleteProductLotAPIView.as_view(), name='productlot-warehouse-rack'),


    # Home Page Dashboard
    path('get-warehouse-details', GetWarehouseDetailsView.as_view(), name='get-warehouse-details'),

    path('get-section-details', GetSectionDetailsView.as_view(), name='get-section-details'),
    path('get-section-ids', GetAllSectionIdsView.as_view(), name='get-section-ids'),
    path('get-section/<str:id>', CheckSectionView.as_view(), name='get-section'),
    path('get-filledsize-sectionid', GetFilledSizeAndSectionId.as_view(), name='get-filledsize-sectionid'),

    path('get-rack-details', GetRackDetailsView.as_view(), name='get-rack-details'),
    path('get-rack-ids', GetAllRacksIdsView.as_view(), name='get-rack-ids'),
    path('get-rack/<str:id>', CheckRackView.as_view(), name='get-rack'),
    path('get-filledsize-rackid', GetFilledSizeAndRackId.as_view(), name='get-filledsize-rackid'),

    #ML prediction
    path('predict/', GetPredictions.as_view(), name='predict'),


    path('', index, name='predict'),

]
