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
import lgbtqcovid.patient_form
# To add a new path, first import the app:
# import blog
#
# Then add the new path:
# path('blog/', blog.urls, name="blog")
#
# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/

urlpatterns = [
    path("", lgbtqcovid.views.index, name="index"),
    path("dashboard-all/", lgbtqcovid.views.dashboard_all, name="dashboard-all"),
    path("dashboard-fhir/", lgbtqcovid.views.dashboard_fhir, name="dashboard-fhir"),
    path("dashboard-cases/", lgbtqcovid.views.dashboard_cases, name="dashboard-cases"),
    path("dashboard-deaths/", lgbtqcovid.views.dashboard_deaths, name="dashboard-deaths"),
    path("data-insert-all/", lgbtqcovid.views.insert_data, name="data-insert-all"),
    path("data-insert-subset/", lgbtqcovid.views.insert_data_subset, name="data-insert-subset"),
    path("patient-search/", lgbtqcovid.views.patient_search, name='patient-search'),
    path("patient/", lgbtqcovid.views.patient, name="patient"),
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
