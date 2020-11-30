from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect

class PatientSearchForm(forms.Form):
    patient_id = forms.CharField(label='Patient Id')

