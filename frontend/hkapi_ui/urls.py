"""
URL configuration for hkapi_ui project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),  
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('namespaces/create/', views.create_namespace, name='create_namespace'),
    path('namespaces/<int:namespace_id>/delete/', views.delete_namespace, name='delete_namespace'),
    path('api/v1/helm/releases', views.list_helm_releases, name='list_helm_releases'),
    path('api/v1/helm/releases/create', views.create_helm_release, name='create_helm_release'),
    path('api/v1/helm/releases/<str:release_name>', views.get_helm_release, name='get_helm_release'),
    path('api/v1/helm/releases/<str:release_name>/delete', views.delete_helm_release, name='delete_helm_release'),
    path('api/v1/helm/releases/<str:release_name>/rollback', views.rollback_helm_release, name='rollback_helm_release'),
]
