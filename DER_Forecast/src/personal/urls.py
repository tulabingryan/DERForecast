from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^settings/$', views.settings, name='settings'),
    url(r'^contact/$', views.contact, name='contact'),
    url(r'^charts/$', views.charts, name='charts'),
    url(r'^simplechart/$', views.simplechart, name='simplechart'),
]
