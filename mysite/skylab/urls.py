from django.conf.urls import include, url

from skylab.modules.autodock4.views import AutodockView, AutogridView
from skylab.modules.dock6.views import Dock6FormView, GridFormView
from skylab.modules.gamess.views import GAMESSView
from skylab.modules.quantumespresso.views import QuantumESPRESSOView
from skylab.modules.ray.views import RayView
from skylab.modules.vina.views import VinaView, VinaSplitView
from . import views

urlpatterns = [
                  # url(r'^$', views.index, name='index'),
                  # url(r'^accounts/', include('registration.backends.default.urls')),

                  # url(r'^$', views.use_impi, name='home'),

    url(r'^task/(?P<pk>\d+)/$', views.ToolActivityDetail.as_view(), name='task_detail_view'),
    url(r'^ajax/task-detail-fragments/(?P<pk>\d+)$', views.refresh_task_detail_view, name='refresh_task_detail_view'),
    url(r'^ajax/nav-task-list-fragments$', views.refresh_nav_task_list, name='refresh_nav_task_list'),

    url(r'^gamess$', GAMESSView.as_view(), name='use_gamess'),
    url(r'^ray$', RayView.as_view(), name='use_ray'),
    url(r'^vina/vina$', VinaView.as_view(), name="use_vina"),
    url(r'^vina/vina-split$', VinaSplitView.as_view(), name="use_vina_split"),
    url(r'^autodock/autodock$', AutodockView.as_view(), name="use_autodock"),
    url(r'^autodock/autogrid$', AutogridView.as_view(), name="use_autogrid"),
    url(r'^dock6/dock6$', Dock6FormView.as_view(), name="use_dock6_dock6"),
    url(r'^dock6/grid$', GridFormView.as_view(), name="use_dock6_grid"),
    url(r'^quantum-espresso$', QuantumESPRESSOView.as_view(), name="use_quantum_espresso"),

    url(r'^$', views.HomeView.as_view(), name='skylab-home'),
    url(r'^create-mpi-cluster$', views.CreateMPIView.as_view(), name='create_mpi'),
    # skip logout confirmation
    # url(r'^accounts/logout/$', logout, {'next_page': '/'}),
    url(r'^accounts/', include('allauth.urls')),

    url(r'^files/task/(?P<task_id>\d+)/(?P<type>.+)/(?P<filename>.*\..*)$', views.serve_skylabfile,
        name="skylab_file_url"),

]  # + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
