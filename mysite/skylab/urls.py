from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.auth.views import logout

from skylab.modules.gamess.views import GamessView
from skylab.modules.ray.views import RayView
from skylab.modules.vina.views import VinaView, VinaSplitView
from skylab.modules.autodock.views import AutodockView, AutogridView
from skylab.modules.dock6.views import DockFormView, GridFormView
from .views import CreateMPIView, HomeView, ToolActivityDetail, serve_private_file, task_fragments_view, \
    display_private_file_content

urlpatterns = [
                  # url(r'^$', views.index, name='index'),
                  # url(r'^accounts/', include('registration.backends.default.urls')),

                  # url(r'^$', views.use_impi, name='home'),

    url(r'^task/(?P<pk>\d+)/$', ToolActivityDetail.as_view(), name='task_detailview'),
    url(r'^task-fragments/(?P<pk>\d+)$', task_fragments_view, name='task_fragments'),
    url(r'^use_gamess$', GamessView.as_view(), name='use_gamess'),
    url(r'^ray/ray$', RayView.as_view(), name='use_ray'),
    url(r'^vina/vina$', VinaView.as_view(), name="use_vina"),
    url(r'^vina/vina_split', VinaSplitView.as_view(), name="use_vina_split"),
    url(r'^autodock/autodock$', AutodockView.as_view(), name="use_autodock"),
    url(r'^autodock/autogrid', AutogridView.as_view(), name="use_autogrid"),
    url(r'^dock6/dock6', DockFormView.as_view(), name="use_dock6_dock6"),
    url(r'^dock6/grid', GridFormView.as_view(), name="use_dock6_grid"),
    url(r'^$', HomeView.as_view(), name='skylab-home'),
    url(r'^create_mpi_cluster$', CreateMPIView.as_view(), name='create_mpi'),
    # skip logout confirmation
    url(r'^accounts/logout/$', logout, {'next_page': '/'}),
    url(r'^accounts/', include('allauth.urls')),
    # url(r'^auth/', include('registration.backends.hmac.urls')),
                  #   url(r'^{0}(?P<path>.*(?P<filename>.*\..*))$'.format(settings.PRIVATE_MEDIA_URL.lstrip('/')), serve_private_file, ),
                  # url(r'^view/(?P<path>.*(?P<filename>.*\..*))$', display_private_file_content, )

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
