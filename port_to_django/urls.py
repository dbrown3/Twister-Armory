__author__ = 'pgilmore'


from django.conf.urls import patterns, url, include

from twister import views

urlpatterns = patterns('',
                       url(r'^$', views.index, name='index'),
                       url(r'^user_start/$', views.user_start, name='user_start'), 
                       url(r'^user_start2/$', views.user_start2, name='user_start2'),
                       url(r'^rater_conf/$', views.rater_conf, name='rater_conf'),
                       url(r'^create_new_study/$', views.create_new_study, name='create_new_study'),                        
                       url(r'^export_empty_eval/$', views.export_empty_eval, name='export_empty_eval'),
                       url(r'^full_docs/$', views.full_docs, name='full_docs'),
                       )