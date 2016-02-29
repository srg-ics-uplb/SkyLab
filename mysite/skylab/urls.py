from django.conf.urls import url

from .views import *

app_name = 'skylab'
urlpatterns = [
	 # ex: /skylab/
    #url(r'^$', views.IndexView.as_view(), name='index'),
    # ex: /skylab/5/
    url(r'^(?P<pk>[0-9]+)/$', DetailView.as_view(), name='detail'),
    # ex: /skylab/5/results/
    url(r'^(?P<pk>[0-9]+)/results/$', ResultsView.as_view(), name='results'),
    # ex: /skylab/5/vote/
    url(r'^(?P<question_id>[0-9]+)/vote/$', vote, name='vote'),

    # url('^$', HomePageView.as_view(), name='home'),
    # url(r'^register/$', SignUpView.as_view(), name='signup'),
    # url(r'^login/$', LoginView.as_view(), name='login'),
    # url(r'^logout/$', LogOutView.as_view(), name='logout'),
]

