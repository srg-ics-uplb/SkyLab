from django.conf.urls import url

from . import views

app_name = 'skylab'
urlpatterns = [
	 # ex: /skylab/
    url(r'^$', views.IndexView.as_view(), name='index'),
    # ex: /skylab/5/
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    # ex: /skylab/5/results/
    url(r'^(?P<pk>[0-9]+)/results/$', views.ResultsView.as_view(), name='results'),
    # ex: /skylab/5/vote/
    url(r'^(?P<question_id>[0-9]+)/vote/$', views.vote, name='vote'),

]

