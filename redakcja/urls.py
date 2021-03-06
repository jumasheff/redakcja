# -*- coding: utf-8 -*-

from django.conf.urls import include, patterns, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView


admin.autodiscover()

urlpatterns = patterns('',
    # Auth
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.login', name='logout'),
    url(r'^admin/login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^admin/logout/$', 'django.contrib.auth.views.logout', name='logout'),

    # Admin panel
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),

    (r'^comments/', include('django.contrib.comments.urls')),

    url(r'^$', RedirectView.as_view(url= '/documents/')),
    url(r'^documents/', include('catalogue.urls')),
    url(r'^apiclient/', include('apiclient.urls')),
    url(r'^editor/', include('wiki.urls')),
    url(r'^images/', include('wiki_img.urls')),
    url(r'^cover/', include('cover.urls')),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
