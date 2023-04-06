"""
orthos2 URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
https://docs.djangoproject.com/en/1.10/topics/http/urls/

Examples:
    Function views
        1. Add an import:  from my_app import views
        2. Add a URL to urlpatterns:  re_path(r'^$', views.home, name='home')
    Class-based views
        1. Add an import:  from other_app.views import Home
        2. Add a URL to urlpatterns:  re_path(r'^$', Home.as_view(), name='home')
    Including another URLconf
        1. Import the include() function: from django.urls import url, include
        2. Add a URL to urlpatterns:  re_path(r'^blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, re_path

urlpatterns = [
    re_path(r'^', include('orthos2.frontend.urls', namespace='frontend')),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^api/', include('orthos2.api.urls', namespace='api')),
]
