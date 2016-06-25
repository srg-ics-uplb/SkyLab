from django.conf import settings
from django.conf.urls import include, url

from skylab.modules.gamess.views import GamessView
from skylab.modules.ray.views import RayView
from skylab.modules.vina.views import VinaView, VinaSplitView
from .views import CreateMPIView, HomeView, ToolActivityDetail, serve_private_file

urlpatterns = [
                  # url(r'^$', views.index, name='index'),
                  # url(r'^accounts/', include('registration.backends.default.urls')),

                  # url(r'^$', views.use_impi, name='home'),

    url(r'^toolactivity/(?P<pk>\d+)/$', ToolActivityDetail.as_view(), name='toolactivity_detailview'),
    url(r'^use_gamess$', GamessView.as_view(), name='use_gamess'),
    url(r'^ray/ray$', RayView.as_view(), name='ray'),
    url(r'^vina/vina$', VinaView.as_view(), name="vina"),
    url(r'^vina/vina_split', VinaSplitView.as_view(), name="vina_split"),
    url(r'^$', HomeView.as_view(), name='skylab-home'),
    url(r'^create_mpi_cluster$', CreateMPIView.as_view(), name='create_mpi'),
    url(r'^auth/', include('registration.backends.hmac.urls')),
    url(r'^{0}(?P<path>.*(?P<filename>.*\..*))$'.format(settings.PRIVATE_MEDIA_URL.lstrip('/')), serve_private_file, ),

]  # + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
