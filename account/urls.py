
from django.urls import path , include
from . import views

urlpatterns = [
    ##previous urls
    ##path('login/' , user_login , name='user_login'),
    #
    #path('login/' , auth_views.LoginView.as_view() , name='login'),
    #path('logout/' , auth_views.LogoutView.as_view() , name='logout'),
    #
    ##==========================================================================================================
    #
    #path('change-password/' , auth_views.PasswordChangeView.as_view() , name='change_password'),
    #path('change-password/done/' , auth_views.PasswordChangeDoneView.as_view() , name='password_change_done'),
    #
    ##==========================================================================================================
    #
    #path('password-reset/' , auth_views.PasswordResetView.as_view() , name='password_reset'),
    #path('password-reset/done/' , auth_views.PasswordResetDoneView.as_view() , name='password_reset_done'),
    #path('password-reset/<uidb64>/<token>/' , auth_views.PasswordResetConfirmView.as_view() , name='password_reset_confirm'),
    #path('password-reset/complete/' , auth_views.PasswordResetCompleteView.as_view() , name='password_reset_complete'),
    
    #==========================================================================================================
    path('' , include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),
    path('', views.dashboard, name='dashboard'),
    path('edit/', views.edit, name='edit'),
    path('users/' , views.user_list , name = 'user_list'),
    path('users/<username>/' , views.user_detail , name='user_detail'),
    path('user/follow/' , views.user_follow , name="user_follow"),
    
    ]
