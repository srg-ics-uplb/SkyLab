from django.conf.urls import include, url
from .views import HomePageView

from . import views

urlpatterns = [
    # url(r'^$', views.index, name='index'),
    # url(r'^accounts/', include('registration.backends.default.urls')),

	url(r'^$', HomePageView.as_view(), name='home'),
	
]