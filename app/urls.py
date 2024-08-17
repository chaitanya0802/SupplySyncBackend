from django.urls import path
from django.conf.urls.static import static
from SupplySyncBackend import settings
from app.views import UserTokenLogin, UserSignUp, SectionCreateAPIView, RackCreateAPIView, \
    SectionIDTRAPIView, RackIDQAPIView, RackIDSAPIView, RackUpdateView, RackIDFAPIView, RackIDDAPIView, \
    SearchRackByProductView, QuantityVsTimeView, PredictionAPIView, PredictionLPAPIView

urlpatterns = [
    path('signUp/', UserSignUp.as_view(), name='signUp'),
    path('login/', UserTokenLogin.as_view(), name='login'),
    path('addSection/', SectionCreateAPIView.as_view(), name='section-create'),
    path('addRack/', RackCreateAPIView.as_view(), name='rack-create'),
    path('updateRack/<str:rack_identifier>/', RackUpdateView.as_view(), name='rack-update'),
    path('searchProduct/<int:product_id>/', SearchRackByProductView.as_view(), name='search_rack_by_product'),

    path('getSectionIDTRViz/', SectionIDTRAPIView.as_view(), name='sectiontr-visualization'),
    path('getRackIDQViz/', RackIDQAPIView.as_view(), name='rackq-visualization'),  #quantity of prod.
    path('getRackIDSViz/', RackIDSAPIView.as_view(), name='racks-visualization'), #size
    path('getRackIDFViz/', RackIDFAPIView.as_view(), name='rackf-visualization'), #filled
    path('getRackIDDViz/', RackIDDAPIView.as_view(), name='rackd-visualization'), #AddedRemoved
    path('getQTYvsT/', QuantityVsTimeView.as_view(), name='rackd-visualization'), #AddedRemoved

    path('predictDemand/',PredictionAPIView.as_view(),name='predict-demand'),  #prediction
    path('predictLPDemand/',PredictionLPAPIView.as_view(),name='predict-demand'),  #lppredictionLP

    #todo order calls
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
