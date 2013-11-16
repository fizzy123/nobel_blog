from django.conf.urls import patterns, url

from blog import views 

urlpatterns = patterns('blog.views',
	url(r'^$', 'display', name='index'),
	url(r'^add/$', 'add_or_edit', name='add'),
	url(r'^delete/$', 'delete', name='delete'),
	url(r'^view/(?P<post_id>\d+)/$', 'display', name='view_single_post'),
	url(r'^edit/(?P<post_id>\d+)/$', 'add_or_edit', name='edit'),
)
