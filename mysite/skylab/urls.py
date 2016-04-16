from django.conf.urls import include, url

from .views import HomePageView

urlpatterns = [
    # url(r'^$', views.index, name='index'),
    # url(r'^accounts/', include('registration.backends.default.urls')),

	 # url(r'^$', views.use_impi, name='home'),
	url(r'^$', HomePageView.as_view(), name='index'),
	url(r'^accounts/', include('registration.backends.hmac.urls')),
]