import json
from datetime import timedelta
from urllib.request import urlopen
from lgbtqcovid.data_creation_script import *
import requests
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from plotly.offline import plot
from plotly.graph_objs import Scatter
# from .models import Greeting
import fhirclient.models.fhirabstractbase as fab
import fhirclient.models.fhirabstractresource as far

import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from fhirclient import client
import fhirclient.models.patient as p
import fhirclient.models.observation as o
import fhirclient.models.bundle as b

# Create your views here.
from lgbtqcovid.patient_form import PatientSearchForm
from lgbtqcovid.sexuality_form import SexualityForm


def index(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "index.html")


def get_dashboard_historical_data():
    # Read in Data
    covid_url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
    lgbt_url = 'https://raw.githubusercontent.com/PatrickGood/lgbt-covid-data/main/lgbt_populations.csv'
    state_abbr = 'https://raw.githubusercontent.com/PatrickGood/lgbt-covid-data/main/state_abbreviations.csv'

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

    return final_lgbt_covid_data_history, final_lgbt_covid_data_current


def get_choropleth_positive_cases(data):
    # Choropleth showing Covid 19 Positive Cases by State Affecting LGBT Population Over Time
    return plot(px.choropleth(data,
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


def get_choropleth_deaths(data):
    # Choropleth showing Covid 19 Deaths by State Affecting LGBT Population Over Time
    return plot(px.choropleth(data,
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
                                      "state": "State"},
                              animation_frame="date",
                              animation_group="abbreviation"
                              ), output_type='div', include_plotlyjs=False)


def get_pie_chart_positive_cases(data):
    # TODO:TOP 10?
    # Pie Graph showing Covid 19 Positive Cases by State Affecting LGBT Population Pie Chart
    return plot(px.pie(data,
                       values='lgbt_cases',
                       names='state',
                       title='Covid 19 Positive Cases by State Affecting LGBT Population Pie Chart',
                       labels={"lgbt_cases": "Positive COVID 19 Cases Affecting LGBT Population",
                               "state": "State"}
                       ), output_type='div', include_plotlyjs=False)


def get_pie_chart_deaths(data):
    # Pie chart showing COVID 19 Deaths of LGBT Population By State Pie Chart
    return plot(px.pie(data,
                       values='lgbt_deaths',
                       names='state',
                       title='COVID 19 Deaths of LGBT Population By State Pie Chart',
                       labels={"lgbt_deaths": "LGBT Population Deaths From COVID 19",
                               "state": "State"}
                       ), output_type='div', include_plotlyjs=False)


def dashboard_cases(request):
    final_lgbt_covid_data_history, final_lgbt_covid_data_current = get_dashboard_historical_data()
    hist_lgbt_cases_map_fig_div = get_choropleth_positive_cases(final_lgbt_covid_data_history)
    curr_lgbt_cases_pie_fig_div = get_pie_chart_positive_cases(final_lgbt_covid_data_current)
    return render(request, "dashboard_cases.html", context={'hist_lgbt_cases_map_fig_div': hist_lgbt_cases_map_fig_div,
                                                      'curr_lgbt_cases_pie_fig_div': curr_lgbt_cases_pie_fig_div})


def dashboard_deaths(request):
    final_lgbt_covid_data_history, final_lgbt_covid_data_current = get_dashboard_historical_data()
    hist_lgbt_deaths_map_fig_div = get_choropleth_deaths(final_lgbt_covid_data_history)
    curr_lgbt_deaths_pie_fig_div = get_pie_chart_deaths(final_lgbt_covid_data_current)
    return render(request, "dashboard_deaths.html", context={'hist_lgbt_deaths_map_fig_div': hist_lgbt_deaths_map_fig_div,
                                                      'curr_lgbt_deaths_pie_fig_div': curr_lgbt_deaths_pie_fig_div})


def dashboard_all(request):
    final_lgbt_covid_data_history, final_lgbt_covid_data_current = get_dashboard_historical_data()

    hist_lgbt_cases_map_fig_div = get_choropleth_positive_cases(final_lgbt_covid_data_history)
    curr_lgbt_cases_pie_fig_div = get_pie_chart_positive_cases(final_lgbt_covid_data_current)
    hist_lgbt_deaths_map_fig_div = get_choropleth_deaths(final_lgbt_covid_data_history)
    curr_lgbt_deaths_pie_fig_div = get_pie_chart_deaths(final_lgbt_covid_data_current)

    return render(request, "dashboard_all.html", context={'hist_lgbt_cases_map_fig_div': hist_lgbt_cases_map_fig_div,
                                                      'curr_lgbt_cases_pie_fig_div': curr_lgbt_cases_pie_fig_div,
                                                      'hist_lgbt_deaths_map_fig_div': hist_lgbt_deaths_map_fig_div,
                                                      'curr_lgbt_deaths_pie_fig_div': curr_lgbt_deaths_pie_fig_div})

def get_dashboard_FHIR_current_data():
    settings = {
        'app_id': 'LGBTQCovidReporting',
        'api_base': 'https://r4.smarthealthit.org'
    }

    smart = client.FHIRClient(settings=settings)

    covid_historic_county_data_url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
    lgbt_population_data_url = 'https://raw.githubusercontent.com/PatrickGood/lgbt-covid-data/main/lgbt_populations.csv'
    state_abbr_data_url = 'https://raw.githubusercontent.com/PatrickGood/lgbt-covid-data/main/state_abbreviations.csv'

    covid_historic_county_data = pd.read_csv(covid_historic_county_data_url, dtype={"fips": str})
    yesterday_date = str((pd.datetime.utcnow() - timedelta(2)).date())
    # latest_covid_historic_county_data = covid_historic_county_data[covid_historic_county_data['date'] == yesterday_date]

    lgbt_population_data = pd.read_csv(lgbt_population_data_url, thousands=',')[["STATE", "LGBT POPULATION DENSITY"]]

    state_abbreviations = pd.read_csv(state_abbr_data_url)

    covid_historic_county_data['state_lower'] = covid_historic_county_data['state'].str.lower()
    lgbt_population_data['state_lower'] = lgbt_population_data['STATE'].str.lower()
    lgbt_covid_data_history = pd.merge(covid_historic_county_data, lgbt_population_data, how='inner', on='state_lower')
    lgbt_covid_data_history['lgbt_cases'] = lgbt_covid_data_history['cases'] * lgbt_covid_data_history[
        'LGBT POPULATION DENSITY'] // 100
    lgbt_covid_data_history['lgbt_deaths'] = lgbt_covid_data_history['deaths'] * lgbt_covid_data_history[
        'LGBT POPULATION DENSITY'] // 100
    lgbt_covid_data_history.dropna(inplace=True)
    lgbt_covid_data_history = lgbt_covid_data_history.astype(({'lgbt_cases': 'int32', 'lgbt_deaths': 'int32'}))
    lgbt_covid_data_history = pd.merge(lgbt_covid_data_history, state_abbreviations, how="inner", on='state')
    current_columns = ['state', 'county', 'abbreviation', 'fips', 'cases', 'lgbt_cases', 'deaths', 'lgbt_deaths',
                       'LGBT POPULATION DENSITY']
    final_lgbt_covid_data_current = lgbt_covid_data_history[lgbt_covid_data_history['date'] == yesterday_date]
    final_lgbt_covid_data_current = final_lgbt_covid_data_current[current_columns].sort_values(by=['fips'])


    final_current_columns = ['state', 'county', 'abbreviation', 'fips', 'lgbt_cases', 'cases']
    final_lgbt_covid_data_current = final_lgbt_covid_data_current[final_current_columns].sort_values(by=['fips'])








    fip_list =[]
    fip_data_url="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
    # python 3.x
    r = requests.get(fip_data_url)
    for item in r.json()['features']:
        item_properties = item['properties']
        fip_list.append([item['id'], item_properties['STATE'], item_properties['COUNTY'], item_properties['NAME']])
    fip_data_pd = pd.DataFrame(fip_list, columns=['id', 'state_id', 'county_id', 'county'])


    fips_state_data_url = 'https://raw.githubusercontent.com/PatrickGood/lgbt-covid-data/main/fips_state.csv'
    fips_state_data_df = pd.read_csv(fips_state_data_url, dtype={"fips_code": str}, error_bad_lines=False)


    fips_df = pd.merge(fip_data_pd, fips_state_data_df, 'inner', left_on='state_id', right_on='fips_code')
    fips_df['lookup_key'] = fips_df['state'] + fips_df['county']

    query_url ='/Patient?_has:Condition:patient:code=http://snomed.info/sct|840539006&_has:Condition:patient:verification-status=http://terminology.hl7.org/CodeSystem/condition-ver-status|confirmed&_has:Observation:patient:code=http://loinc.org|76690-7&_has:Observation:patient:value-string=Other,Homosexual,Bisexual&_count=250'
    result = smart.server.request_json(query_url)
    fhir_positive_lgbt_cases_df = pd.DataFrame(columns=['key', 'count'])
    fhir_positive_lgbt_cases_lst = []
    #p.Patient(smart.server.request_json(bundle_url_next)['entry'][000]['resource'])
    if result is not None and 'entry' in result.keys():
        for entry in result['entry']:
            if entry['resource']['resourceType'] == 'Patient':
                patient = p.Patient(entry['resource'])
                state = None
                district = None
                if len(patient.address) > 0:
                    address = patient.address[0]
                    if address.state:
                        state = address.state
                    if address.district:
                        district = address.district
                key = state + district
                fhir_positive_lgbt_cases_lst.append([key, 1])
        while(any(obj['relation'] == 'next' for obj in result['link']) and len(fhir_positive_lgbt_cases_lst) < 10000):
            query_url = result['link'][-1]['url']
            result = smart.server.request_json(query_url)
            if result is not None and 'entry' in result.keys():
                for entry in result['entry']:
                    if entry['resource']['resourceType'] == 'Patient':
                        patient = p.Patient(entry['resource'])
                        state = None
                        district = None
                        if len(patient.address) > 0:
                            address = patient.address[0]
                            if address.state:
                                state = address.state
                            if address.district:
                                district = address.district
                        key = state + district
                        fhir_positive_lgbt_cases_lst.append([key, 1])

        fhir_positive_lgbt_cases_df = pd.DataFrame(fhir_positive_lgbt_cases_lst, columns=['key', 'count'])
        fhir_positive_lgbt_cases_fips_df = pd.merge(fhir_positive_lgbt_cases_df, fips_df, how='inner',
                                                    left_on='key', right_on='lookup_key')
        final_stats = fhir_positive_lgbt_cases_fips_df.groupby('id')['count'].sum()
        final_stats_states = pd.merge(final_stats, fips_df, how='inner', on='id')
        final_stats_states = final_stats_states[['id', 'count', 'fips_code', 'post_code', 'lookup_key']]

        final_stats_states_population = pd.merge(final_stats_states, final_lgbt_covid_data_current, how='inner',
                                                 left_on='id', right_on='fips')
        final_data_frame = final_stats_states_population[
            ['fips', 'state', 'county', 'post_code', 'count', 'cases', 'lgbt_cases']]

        return final_data_frame
    else:
        return pd.DataFrame(columns=[['fips', 'state', 'county', 'post_code', 'count', 'cases', 'lgbt_cases']])
def get_choropleth_FHIR_current_cases(data):
    # Choropleth showing Covid 19 Positive Cases by State and County Affecting LGBT Population from FHIR
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)
    live_lgbt_cases_map_fig_div = plot(px.choropleth(data,
                                                     geojson=counties,
                                                     locations="fips",
                                                     color="count",
                                                     color_continuous_scale='reds',
                                                     hover_name="county",
                                                     hover_data=["count", "cases", "state", "county"],
                                                     scope="usa",
                                                     title='Current FHIR Covid 19 Total Positive Cases affecting LGBT Population',
                                                     labels={
                                                         # "abbreviation": "State Abbreviation",
                                                         "count": "Positive LGBT Cases",
                                                         "cases": "Positive Cases",
                                                         # "lgbt_cases": "Positive COVID 19 Cases Affecting LGBT Population",
                                                         # "LGBT POPULATION DENSITY": "Percentage of State LGBT COVID Cases out of State COVID Cases",
                                                         # "lgbt_state_cases_density_for_date": "Percentage of State LGBT COVID Cases out of U.S. LGBT Cases",
                                                         # "date": "Date",
                                                         "state": "State",
                                                         "county": "County",
                                                         'fips': "FIPS"
                                                     }), output_type='div', include_plotlyjs=False)
    return live_lgbt_cases_map_fig_div
def dashboard_fhir(request):

    current_live_covid_data = get_dashboard_FHIR_current_data()
    #current_live_covid_data = pd.DataFrame(columns=[['fips', 'state', 'county', 'post_code', 'count', 'cases', 'lgbt_cases']])
    #current_live_FHIR_lgbt_cases_map_fig_div = None
    if(len(current_live_covid_data) > 0):
        current_live_FHIR_lgbt_cases_map_fig_div = get_choropleth_FHIR_current_cases(current_live_covid_data)
    return render(request, "dashboard_fhir.html", context={'fhir_cases_map_fig_div': current_live_FHIR_lgbt_cases_map_fig_div})



def insert_data(request):
    #create_data_if_FHIR_Server_returns()
    return render(request, "all-data.html")
def insert_data_subset(request):
    #create_data_if_FHIR_Server_returns()
    return render(request, "subset-data.html")











def get_patient_name(pt):
    name = pt.name
    if name:
        given = name[0].given
        if (given):
            given_name = given[0]
        if (name[0].family):
            family_name = name[0].family
        return given_name + " " + family_name
    else:
        return "anonymous"

def get_patient_address(pt):
    state = ''
    district = ''
    if len(pt.address) > 0:
        address = pt.address[0]
        if address.state:
            state = address.state
        if address.district:
            district = address.district
        return state + ', ' + district
    else:
        return "Not Specified"

#def get_patient_information(request):

def get_patients_example():
    settings = {
        'app_id': 'LGBTQCovidReporting',
        'api_base': 'https://r4.smarthealthit.org'
    }

    smart = client.FHIRClient(settings=settings)
    bundle_covid = p.Patient.where({
                 '_has:Condition:patient:code':'http://snomed.info/sct|840539006',
                 '_has:Condition:patient:verification-status':'http://terminology.hl7.org/CodeSystem/condition-ver-status|confirmed'
                }
                ).perform(smart.server)
    patient_covid_id = "Please load data to see example patient id"
    if(bundle_covid.entry):
        patient_covid_id = bundle_covid.entry[0].resource.id
    return patient_covid_id





def get_patient_info(patient_id):
    settings = {
        'app_id': 'LGBTQCovidReporting',
        'api_base': 'https://r4.smarthealthit.org'
    }

    smart = client.FHIRClient(settings=settings)
    patient = p.Patient.read(patient_id, smart.server)
    patient_name = get_patient_name(patient)
    patient_address = get_patient_address(patient)
    patient_birthdate = str(patient.birthDate.date)
    patient_gender = patient.gender

    tested_positive = False
    bundle = p.Patient.where({'_id': str(patient_id),
                 '_has:Condition:patient:code':'http://snomed.info/sct|840539006',
                 '_has:Condition:patient:verification-status':'http://terminology.hl7.org/CodeSystem/condition-ver-status|confirmed'},
                ).perform(smart.server)
    if bundle.entry:
        if len(bundle.entry) > 0:
            tested_positive = True
    sexuality = "I choose not to answer"
    bundle = o.Observation.where({'subject': str(patient_id),
                 'code':'http://loinc.org|76690-7',
                                  '_sort':'-date',
                                  '_count':'1'}
                ).perform(smart.server)
    if bundle.entry:
        if len(bundle.entry) > 0:
            sexuality = bundle.entry[0].resource.valueString
    return [patient_id, patient_name, patient_gender, patient_birthdate, patient_address, tested_positive, sexuality]
def update_patients_sexuality(patient_id, sexual_orientation):
    base_observation = {
        "resourceType": "Observation",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "social-history",
                        "display": "social-history"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "76690-7",
                    "display": "Sexual orientation"
                }
            ],
            "text": "Sexual orientation"
        },
        "subject": {
            "reference": ""
        },
        "performer": [{"reference": ""}],
        "valueString": ""

    }
    settings = {
        'app_id': 'LGBTQCovidReporting',
        'api_base': 'https://r4.smarthealthit.org'
    }

    smart = client.FHIRClient(settings=settings)
    #id = str(datetime.utcnow().date()) + "pgood7userobservation" + "1"
    subject_reference = "Patient/" + patient_id
    #date = datetime.utcnow().isoformat()
    #sexual_orientations = ['Bisexual', 'Heterosexual', 'Homosexual', 'Other', 'Asked but unknown', 'Unknown']
    observation = o.Observation(base_observation)
    #observation.subject_reference = subject_reference
    observation.subject.reference = subject_reference
    observation.performer[0].reference = subject_reference
    observation.effectiveDateTime = fd.FHIRDate(str(datetime.utcnow().isoformat()))
    observation.issued = fd.FHIRDate(str(datetime.utcnow().isoformat()))
    observation.valueString = sexual_orientation
    new_observation = observation.create(smart.server)
    if(new_observation):
        return 200
    else:
        return 400


def patient_search(request):
    example_patient_id = get_patients_example()
    # submitted = False
    if request.method == 'POST':
        form = PatientSearchForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # assert False
            # return HttpResponseRedirect('/patient-search?submitted=True')
            pt = get_patient_info(cd['patient_id'])
            pt_dic = {'patient_id': pt[0],
                          'patient_name': pt[1],
                          'patient_gender': pt[2],
                           'patient_birthdate': pt[3],
                           'patient_address': pt[4],
                           'tested_positive': pt[5],
                           'sexuality': pt[6]
                           }
            if request.session.get('_patient_info'):
                del request.session['_patient_info']
            request.session['_patient_info'] = pt_dic
            return HttpResponseRedirect('/patient')

    else:
        form = PatientSearchForm()
    return render(request,
                  'patient-search.html',
                  {'form': form, 'example_patient_id':example_patient_id}
                  )
def patient(request):
    # submitted = False
    if request.method == 'POST':
        form = SexualityForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # assert False
            # return HttpResponseRedirect('/patient-search?submitted=True')
            pt_id = None
            if request.session.get('_patient_info'):
                patient_info = request.session.get('_patient_info')

                status = update_patients_sexuality(patient_info['patient_id'], cd['sexuality'])
                if(status == 200):
                    patient_info['sexuality'] = cd['sexuality']
                    request.session['_patient_info'] = patient_info
                    return HttpResponseRedirect('/patient-search')
        return HttpResponseBadRequest()
    else:
        patient_info = request.session.get('_patient_info')
        if patient_info:
            return render(request, 'patient.html',
                          {'patient_id': patient_info['patient_id'],
                          'patient_name': patient_info['patient_name'],
                          'patient_gender': patient_info['patient_gender'],
                           'patient_birthdate': patient_info["patient_birthdate"],
                           'patient_address': patient_info['patient_address'],
                           'tested_positive': patient_info['tested_positive'],
                           'sexuality': patient_info['sexuality'],
                           'form': SexualityForm()
                           })
        else:
            return HttpResponseRedirect('/patient-search')
        #form = SexualityForm()
        # if 'submitted' in request.GET:
        #     submitted = True
    # return render(request,
    #               'patient-search.html',
    #               {'form': PatientSearchForm()}
    #               )








if __name__ == "__main__":
    get_patient_info('909819')
    #update_patients_sexuality('909819', 'Bisexual')

