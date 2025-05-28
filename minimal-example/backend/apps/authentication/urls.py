from django.urls import path
from . import views
from django.http import JsonResponse

def auth_root(request):
    """认证模块根端点"""
    return JsonResponse({
        'module': '用户认证模块',
        'endpoints': {
            'register': '/api/auth/register/',
            'login': '/api/auth/login/',
            'logout': '/api/auth/logout/',
            'profile': '/api/auth/profile/',
            'profile_update': '/api/auth/profile/update/',
            'organizations': '/api/auth/organizations/'
        }
    })

urlpatterns = [
    path('', auth_root, name='auth-root'),
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('login/', views.login_view, name='user-login'),
    path('logout/', views.logout_view, name='user-logout'),
    path('profile/', views.profile_view, name='user-profile'),
    path('profile/update/', views.UserProfileUpdateView.as_view(), name='user-profile-update'),
    path('organizations/', views.OrganizationListView.as_view(), name='organization-list'),
]
