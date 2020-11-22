from django.shortcuts import render
from django.http import HttpResponse
from plotly.offline import plot
from plotly.graph_objs import Scatter
#from .models import Greeting

import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from fhirclient import client
import fhirclient.models.patient as p
import fhirclient.models.observation as o


# Create your views here.
def index(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "index.html")

def dashboard(request):
    #Read in Data
    #TODO:Read in the data
    covid_url = 'https://github.gatech.edu/raw/pgood7/lgbt_covid_data_analysis/master/us-states.csv?token=AAAGBYH2BAN5QUEX6PMHYI27WH6V6'
    lgbt_url = 'https://github.gatech.edu/raw/pgood7/lgbt_covid_data_analysis/master/lgbt_populations.csv?token=AAAGBYFN4A4NAOVEQAHNZFC7WH6S4'
    state_abbr = 'https://github.gatech.edu/raw/pgood7/lgbt_covid_data_analysis/master/state_abbreviations.csv?token=AAAGBYHEOGBMUXLZMZ2N3Q27WH6OE'
    covid_data_history = pd.read_csv(covid_url, dtype={"fips": str})
    lgbt_population_data = pd.read_csv(lgbt_url, thousands=',')
    state_abbreviations = pd.read_csv(state_abbr)

    # Clean and transform data

    covid_data_history['state_lower'] = covid_data_history['state'].str.lower()
    lgbt_population_data['state_lower'] = lgbt_population_data['STATE'].str.lower()
    lgbt_covid_data_history = pd.merge(covid_data_history, lgbt_population_data, how='inner', on='state_lower')
    lgbt_covid_data_history['lgbt_cases'] = lgbt_covid_data_history['cases'] * lgbt_covid_data_history[
        'LGBT POPULATION DENSITY'] // 100
    lgbt_covid_data_history['lgbt_deaths'] = lgbt_covid_data_history['deaths'] * lgbt_covid_data_history[
        'LGBT POPULATION DENSITY'] // 100
    lgbt_covid_data_history.dropna(inplace=True)
    lgbt_covid_data_history = lgbt_covid_data_history.astype(({'lgbt_cases': 'int32', 'lgbt_deaths': 'int32'}))
    lgbt_covid_data_history = pd.merge(lgbt_covid_data_history, state_abbreviations, how="inner", on='state')
    history_colums = ['date', 'state', 'abbreviation', 'fips', 'cases', 'lgbt_cases', 'deaths', 'lgbt_deaths',
                      'LGBT POPULATION DENSITY']
    current_columns = ['state', 'abbreviation', 'fips', 'cases', 'lgbt_cases', 'deaths', 'lgbt_deaths',
                       'LGBT POPULATION DENSITY']
    final_lgbt_covid_data_history = lgbt_covid_data_history[history_colums].sort_values(by=['date', 'fips'])
    final_lgbt_covid_data_history_sum = final_lgbt_covid_data_history.groupby(by=["date"])[
        'cases', 'lgbt_cases', 'deaths', 'lgbt_deaths'].sum()
    final_lgbt_covid_data_history_sum = final_lgbt_covid_data_history_sum.rename(
        columns={'cases': 'us_total_cases_for_date',
                 'lgbt_cases': 'us_total_lgbt_cases_for_date',
                 'deaths': 'us_total_deaths_for_date',
                 'lgbt_deaths': 'us_total_lgbt_deaths_for_date'}, inplace=False)
    final_lgbt_covid_data_history = pd.merge(final_lgbt_covid_data_history, final_lgbt_covid_data_history_sum,
                                             how="inner", on='date')
    final_lgbt_covid_data_history['lgbt_state_cases_density_for_date'] = final_lgbt_covid_data_history['lgbt_cases'] / \
                                                                         final_lgbt_covid_data_history[
                                                                             'us_total_lgbt_cases_for_date'] * 100
    final_lgbt_covid_data_history['lgbt_state_deaths_density_for_date'] = final_lgbt_covid_data_history['lgbt_deaths'] / \
                                                                          final_lgbt_covid_data_history[
                                                                              'us_total_lgbt_deaths_for_date'] * 100
    final_lgbt_covid_data_current = lgbt_covid_data_history[lgbt_covid_data_history['date'] == '2020-09-19']
    final_lgbt_covid_data_current = final_lgbt_covid_data_current[current_columns].sort_values(by=['fips'])
    total_lgbt_cases = final_lgbt_covid_data_current['lgbt_cases'].sum()
    total_lgbt_deaths = final_lgbt_covid_data_current['lgbt_deaths'].sum()
    final_lgbt_covid_data_current['lgbt_state_cases_density'] = final_lgbt_covid_data_current[
                                                                    'lgbt_cases'] / total_lgbt_cases * 100
    final_lgbt_covid_data_current['lgbt_state_deaths_density'] = final_lgbt_covid_data_current[
                                                                     'lgbt_deaths'] / total_lgbt_deaths * 100
    # final_lgbt_covid_data_current = final_lgbt_covid_data_current.astype(({'lgbt_state_cases_density': 'int32', 'lgbt_state_deaths_density': 'int32'}))




    # Saved transformed data to a file and saved it on git hub repo when ran from local machine.Labeled lgbt_covid_current.csv and lgbt_covid_history.csv

    # final_lgbt_covid_data_current.to_csv('data/lgbt_covid_current.csv', index=False)
    # final_lgbt_covid_data_history.to_csv('data/lgbt_covid_history.csv', index=False)





    # Choropleth showing Covid 19 Positive Cases by State Affecting LGBT Population Over Time
    hist_lgbt_cases_map_fig_div = plot(px.choropleth(final_lgbt_covid_data_history,
                                            locations="abbreviation",
                                            locationmode="USA-states",
                                            color="lgbt_cases",
                                            color_continuous_scale='reds',
                                            hover_name="state",
                                            hover_data=["cases", "lgbt_cases", "LGBT POPULATION DENSITY",
                                                        'lgbt_state_cases_density_for_date'],
                                            scope="usa",
                                            title='Covid 19 Positive Cases by State Affecting LGBT Population Over Time',
                                            labels={"abbreviation": "State Abbreviation",
                                                    "cases": "Positive Cases",
                                                    "lgbt_cases": "Positive COVID 19 Cases Affecting LGBT Population",
                                                    "LGBT POPULATION DENSITY": "Percentage of State LGBT COVID Cases out of State COVID Cases",
                                                    "lgbt_state_cases_density_for_date": "Percentage of State LGBT COVID Cases out of U.S. LGBT Cases",
                                                    "date": "Date",
                                                    "state": "State"},
                                            animation_frame="date",
                                            animation_group="abbreviation"
                                            ), output_type='div', include_plotlyjs=False)

    #TODO:TOP 10?
    # Pie Graph showing Covid 19 Positive Cases by State Affecting LGBT Population Pie Chart
    curr_lgbt_cases_pie_fig_div = plot(px.pie(final_lgbt_covid_data_current,
                                     values='lgbt_cases',
                                     names='state',
                                     title='Covid 19 Positive Cases by State Affecting LGBT Population Pie Chart',
                                     labels={"lgbt_cases": "Positive COVID 19 Cases Affecting LGBT Population",
                                             "state": "State"}
                                     ), output_type='div', include_plotlyjs=False)



    # Choropleth showing Covid 19 Deaths by State Affecting LGBT Population Over Time
    hist_lgbt_deaths_map_fig_div = plot(px.choropleth(final_lgbt_covid_data_history,
                                        locations="abbreviation",
                                        locationmode="USA-states",
                                        color="lgbt_deaths",
                                        color_continuous_scale='blues',
                                        hover_name="state",
                                        hover_data=["deaths", "lgbt_deaths", "LGBT POPULATION DENSITY",
                                                    'lgbt_state_deaths_density_for_date'],
                                        scope="usa",
                                        title='Covid 19 Deaths by State Affecting LGBT Population Over Time',
                                        labels={"abbreviation": "State Abbreviation",
                                                "deaths": "Deaths",
                                                "lgbt_deaths": "LGBT Population Deaths From COVID 19",
                                                "LGBT POPULATION DENSITY": "Percentage of State LGBT COVID Deaths out of State COVID Deaths",
                                                "lgbt_state_deaths_density_for_date": "Percentage of State LGBT COVID Deaths out of U.S. LGBT COVID Deaths",
                                                "date": "Date",
                                                "state":"State"},
                                        animation_frame="date",
                                        animation_group="abbreviation"
                                        ), output_type='div', include_plotlyjs=False)








    # Pie chart showing COVID 19 Deaths of LGBT Population By State Pie Chart
    curr_lgbt_deaths_pie_fig_div = plot(px.pie(final_lgbt_covid_data_current,
                                  values='lgbt_deaths',
                                  names='state',
                                  title='COVID 19 Deaths of LGBT Population By State Pie Chart',
                                  labels={"lgbt_deaths": "LGBT Population Deaths From COVID 19",
                                                "state":"State"}
                                  ), output_type='div', include_plotlyjs=False)

    return render(request, "dashboard.html", context={'hist_lgbt_cases_map_fig_div': hist_lgbt_cases_map_fig_div,
                                                      'curr_lgbt_cases_pie_fig_div': curr_lgbt_cases_pie_fig_div,
                                                      'hist_lgbt_deaths_map_fig_div': hist_lgbt_deaths_map_fig_div,
                                                      'curr_lgbt_deaths_pie_fig_div': curr_lgbt_deaths_pie_fig_div})


def patient(request):



    return render(request, "patient.html")











def get_patient_name(pt):
    name = pt.name
    if name:
        given = name[0].given
        if(given):
            given_name = given[0]
        if(name[0].family):
            family_name = name[0].family
        return given_name + " " + family_name
    else:
        return "anonymous"
def get_patient_marital_status(pt):
    if pt.maritalStatus:
        switcher = {
            "A": "Annulled",
            "D": "Divorced",
            "I": "Interlocutory",
            "L": "Legally Separated",
            "M": "Married",
            "C": "Common Law",
            "P": "Polygamous",
            "T": "Domestic partner",
            "U": "unmarried",
            "S": "Never Married",
            "W": "Widowed"
        }
        return switcher.get(pt.maritalStatus.coding[0].code, "Not Specified")
    else:
        return "Not Specified"
def get_patient_address(pt):
    if len(pt.address) > 0:
        address = pt.address[0]
        if address.country:
            country = address.country
        else:
            country = ""

        if address.state:
            state = address.state
        else:
            state = ""

        if address.city:
            city = address.city
        else:
            city = ""

        if address.postalCode:
            postal = address.postalCode
        else:
            postal = ""

        if address.line and len(address.line) > 0:
            line = address.line[0]
        else:
            line = ""
        return line + '<br>' + city +', ' + state +' '+ postal + '<br>' + country
    else:
        return "Not Specified"

def get_patient_geo_location(pt):
    if len(pt.address) > 0:
        address = pt.address[0]
        if address.extension and len(address.extension) > 0:
            geo_location = address.extension[0];
            if(geo_location.extension):
                lat = geo_location.extension[0].valueDecimal;
                lon = geo_location.extension[1].valueDecimal;
                return str(lat) + ',' + str(lon)
            else:
                return "Not Specified"
        return "Not Specified"
    return "Not Specified"

if __name__ == "__main__":
    settings = {
    'app_id': 'LGBTQCovidReporting',
    'api_base': 'https://r4.smarthealthit.org'
    }

    smart = client.FHIRClient(settings=settings)
    # if not smart.ready:
    #     smart.prepare()
    #     smart.ready
    #     smart.prepare()
    #     smart.authorize_url
    patient = p.Patient.read('06895d41-5937-4e83-9f3d-0af09db31c69', smart.server)
    patient_name = get_patient_name(patient)
    patient_ms = get_patient_marital_status(patient)
    patient_address = get_patient_address(patient)
    patient_geo_location = get_patient_geo_location(patient)

    patient.birthDate.isostring
