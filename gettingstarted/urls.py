"""LGBTQCovidProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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

from django.urls import path, include

from django.contrib import admin

admin.autodiscover()

import hello.views
import lgbtqcovid.views

# To add a new path, first import the app:
# import blog
#
# Then add the new path:
# path('blog/', blog.urls, name="blog")
#
# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/

urlpatterns = [
    path("", lgbtqcovid.views.index, name="index"),
    path("patient/", lgbtqcovid.views.patient, name="patient"),
    path("dashboard/", lgbtqcovid.views.dashboard, name="dashboard"),
    path("old/", hello.views.index, name="oldindex"),
    path("old/db/", hello.views.db, name="db"),
    path("admin/", admin.site.urls),
]




# from django.urls import path
# from . import views
#
# app_name = 'post'
# urlpatterns=[
#     path('', views.index , name='index'),
#     path('blog/', views.blog , name='blog'),]

# from django.urls import path, include
#
# urlpatterns=[
# path('post/', include('post.urls'),]
# <a href="{% url 'post:index' %}">Index</a>
# <a href="{% url 'post:blog' %}">Blog</a>
