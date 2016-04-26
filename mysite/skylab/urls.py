from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static

from .views import CreateMPIView, HomeView, Use_Gamess_View

urlpatterns = [
    # url(r'^$', views.index, name='index'),
    # url(r'^accounts/', include('registration.backends.default.urls')),

	 # url(r'^$', views.use_impi, name='home'),
	url(r'^use-gamess', Use_Gamess_View.as_view(), name='use-gamess'),
	url(r'^$', HomeView.as_view(), name='skylab-home'),
	url(r'^create-mpi-cluster$', CreateMPIView.as_view(), name='create_mpi_cluster'),
	url(r'^accounts/', include('registration.backends.hmac.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT )