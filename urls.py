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
                       url(r'^export_empty_match/$', views.export_empty_match, name='export_empty_match'),
                       url(r'^click_spin_export/$', views.click_spin_export, name='click_spin_export'),
                       url(r'^click_final_export/$', views.click_final_export, name='click_final_export'),
                       url(r'^full_docs/$', views.full_docs, name='full_docs'),
                       url(r'^tenure_ask/$', views.tenure_ask, name='tenure_ask'),
                       url(r'^show_and_match/$', views.show_and_match, name='show_and_match'),
                       url(r'^match_and_merge/$', views.match_and_merge, name='match_and_merge'),
                       url(r'^merge_and_master/$', views.merge_and_master, name='merge_and_master'),
                       url(r'^scoreboard/$', views.scoreboard, name='scoreboard'),
                       )