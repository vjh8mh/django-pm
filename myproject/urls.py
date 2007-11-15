from django.conf.urls.defaults import *
import settings

urlpatterns = patterns('',
    # Example:
    # (r'^myproject/', include('myproject.foo.urls')),
    (r'^$', 'django.views.generic.simple.redirect_to', {'url': '/pm/inbox/'}),
    (r'^%s' % 'pm/', include('pm.urls')),
    
    # Uncomment this for admin:
    (r'^admin/', include('django.contrib.admin.urls')),
)


if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^m/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '%s/media' % settings.PROJECT_PATH}),
    )
