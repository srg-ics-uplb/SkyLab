from django.conf.urls import include, url
from django.views.generic import RedirectView

from . import views

urlpatterns = [

    url(r'^mpi-clusters/create$', views.CreateMPIView.as_view(), name='create_mpi'),
    url(r'^mpi-clusters$', views.MPIListView.as_view(), name='mpi_list_view'),
    url(r'^mpi-clusters/(?P<pk>\d+)$', views.MPIDetailView.as_view(), name='mpi_detail_view'),
    url(r'^mpi-clusters/(?P<cluster_name>\w+)$', views.MPIDetailView.as_view(), name='mpi_detail_view'),
    url(r'^tasks$', views.TaskListView.as_view(), name='task_list_view'),
    url(r'^tasks/(?P<pk>\d+)$', views.TaskDetailView.as_view(), name='task_detail_view'),
    url(r'^toolsets$', views.ToolsetListView.as_view(), name='toolset_list_view'),
    url(r'^toolsets/(?P<toolset_simple_name>[a-z0-9]+)$', views.ToolSetDetailView.as_view(),
        name='toolset_detail_view'),
    url(r'^toolsets/(?P<toolset_simple_name>[a-z][\w/-]+)/(?P<tool_simple_name>[a-z][\w/-]+)/$', views.tool_view,
        name="skylab_tool_view"),
    url(r'^toolsets/(?P<toolset_pk>\d+)/(?P<tool_pk>\d+)/$', views.tool_view, name='skylab_tool_view'),


    url(r'^ajax/refresh-task-list-table$', views.refresh_task_list_table, name='ajax_refresh_task_list_table'),
    url(r'^ajax/refresh-mpi-list-table$', views.refresh_mpi_list_table, name='ajax_refresh_mpi_list_table'),
    url(r'^ajax/task-detail-fragments/(?P<pk>\d+)$', views.refresh_task_detail_view,
        name='ajax_refresh_task_detail_view'),
    url(r'^ajax/nav-task-list-fragments$', views.refresh_nav_task_list, name='ajax_refresh_nav_task_list'),
    url(r'^ajax/mpi-privacy$', views.post_mpi_visibility, name='ajax_post_mpi_privacy_change'),
    url(r'^ajax/post-mpi-delete$', views.post_mpi_delete, name='ajax_post_mpi_delete'),
    url(r'^ajax/post-mpi-toolset-activate$', views.post_mpi_toolset_activate, name='ajax_post_mpi_toolset_activate'),
    url(r'ajax/post-mpi-allow-user$', views.post_allow_user_access_to_mpi, name='ajax_post_allow_user_access_to_mpi'),
    url(r'ajax/refresh-select-toolset$', views.refresh_select_toolset, name='ajax_refresh_select_toolset'),
    url(r'ajax/refresh-select-tools/(?P<toolset_simple_name>[a-z]\w+)', views.refresh_select_toolset_tool_options,
        name='ajax_refresh_select_tool'),

    # url(r'^tools/')


    url(r'^$', views.index, name='skylab-home'),


    # skip logout confirmation
    url(r'^accounts/login/$', RedirectView.as_view(url="/skylab/accounts/google/login/?process=login", permanent=False),
        name="account_login"),
    url(r'^logout_redirect$', views.logout_success, name='logout_redirect'),
    url(r'^accounts/signup/$', RedirectView.as_view(pattern_name="account_login", permanent=False)),
    url(r'^accounts/', include('allauth.urls')),

    url(r'^task/(?P<task_id>\d+)/files/(?P<type>.+)/(?P<filename>.*\..*)$', views.serve_skylabfile,
        name="skylab_file_url"),

]  # + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
