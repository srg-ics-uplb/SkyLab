from django.conf import settings
from django.conf.urls import include, url

from .views import CreateMPIView, HomeView, Use_Gamess_View, ToolActivityDetail, serve_private_file

urlpatterns = [
                  # url(r'^$', views.index, name='index'),
                  # url(r'^accounts/', include('registration.backends.default.urls')),

                  # url(r'^$', views.use_impi, name='home'),
    url(r'^toolactivity/(?P<pk>\d+)/$', ToolActivityDetail.as_view(), name='toolactivity_detailview'),
    url(r'^use-gamess$', Use_Gamess_View.as_view(), name='use-gamess'),
    url(r'^$', HomeView.as_view(), name='skylab-home'),
    url(r'^create-mpi-cluster$', CreateMPIView.as_view(), name='create_mpi_cluster'),
    url(r'^auth/', include('registration.backends.hmac.urls')),
    url(r'^{0}(?P<path>.*(?P<filename>.*\..*))$'.format(settings.PRIVATE_MEDIA_URL.lstrip('/')), serve_private_file, ),

]  # + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
