from django.shortcuts import render
from django.http import HttpResponse
from plotly.offline import plot
from plotly.graph_objs import Scatter
from .models import Greeting

# Create your views here.
def index(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "index.html")


def db(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, "db.html", {"greetings": greetings})

def dashboard(request):
    x_data = [0, 1, 2, 3]
    y_data = [x ** 2 for x in x_data]
    plot_div = plot([Scatter(x=x_data, y=y_data,
                             mode='lines', name='test',
                             opacity=0.8, marker_color='green')],
                    output_type='div')
    return render(request, "dashboard.html", context={'plot_div': plot_div})

