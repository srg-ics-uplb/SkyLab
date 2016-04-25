from django.conf.urls import include, url

from .views import CreateMPIView

urlpatterns = [
    # url(r'^$', views.index, name='index'),
    # url(r'^accounts/', include('registration.backends.default.urls')),

	 # url(r'^$', views.use_impi, name='home'),
	url(r'^$', CreateMPIView.as_view(), name='create_mpi_cluster'),
	url(r'^accounts/', include('registration.backends.hmac.urls')),
]