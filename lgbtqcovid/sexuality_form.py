from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect

sexual_orientations_choices = [('Bisexual', 'Bisexual'), ('Heterosexual', 'Heterosexual'), ('Homosexual','Homosexual'),
                               ('Other','Other'), ('Asked but unknown','I am not sure'), ('Unknown','I choose not to answer')]

class SexualityForm(forms.Form):
    sexuality = forms.ChoiceField(required=True,  choices =sexual_orientations_choices, widget=forms.RadioSelect(), initial='Unkown')

