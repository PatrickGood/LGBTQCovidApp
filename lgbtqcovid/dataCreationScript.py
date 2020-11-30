#Developed by Patrick Good
#GATECH ID: pgood7
import json
import random
from datetime import datetime, timedelta

import fhirclient.models.address as a
import fhirclient.models.bundle as b
import fhirclient.models.condition as c
import fhirclient.models.fhirdate as fd
import fhirclient.models.humanname as hn
import fhirclient.models.observation as o
import fhirclient.models.patient as p
import pandas as pd
import requests
from fhirclient import client
from pandas.io.common import urlopen
from plotly.offline import plot
import plotly.express as px
#import fhirclient.models.identifier as identifier

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
    "performer" : [{"reference": ""}],
    "valueString": ""

}
base_condition = {
    "resourceType": "Condition",
      "clinicalStatus": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
          "code": "resolved"
        }]
      },
      "verificationStatus": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
          "code": "confirmed"
        } ]
      },
      "category": [{
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/condition-category",
          "code": "encounter-diagnosis",
          "display": "Encounter Diagnosis"
        }]
      } ],
      "code": {
        "coding": [{
          "system": "http://snomed.info/sct",
          "code": "840539006",
          "display": "COVID-19"
        }],
        "text": "COVID-19"
      },
      "subject": {
        "reference": ""
      },
      "onsetDateTime": "2020-03-16T03:45:42+05:30",
      "abatementDateTime": "2020-03-30T03:45:42+05:30",
      "recordedDate": "2020-03-16T03:45:42+05:30"
}

def create_data():
    covid_historic_county_data_url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
    lgbt_population_data_url = 'https://raw.githubusercontent.com/PatrickGood/lgbt-covid-data/main/lgbt_populations.csv'
    state_abbr_data_url = 'https://raw.githubusercontent.com/PatrickGood/lgbt-covid-data/main/state_abbreviations.csv'

    covid_historic_county_data = pd.read_csv(covid_historic_county_data_url, dtype={"fips": str})
    yesterday_date = str((datetime.utcnow()-timedelta(2)).date())
    #latest_covid_historic_county_data = covid_historic_county_data[covid_historic_county_data['date'] == yesterday_date]

    lgbt_population_data = pd.read_csv(lgbt_population_data_url, thousands=',')[["STATE", "LGBT POPULATION DENSITY"]]

    state_abbreviations = pd.read_csv(state_abbr_data_url)

    covid_historic_county_data['state_lower'] = covid_historic_county_data['state'].str.lower()
    lgbt_population_data['state_lower'] = lgbt_population_data['STATE'].str.lower()
    lgbt_covid_data_history = pd.merge(covid_historic_county_data, lgbt_population_data, how='inner', on='state_lower')
    lgbt_covid_data_history['lgbt_cases'] = lgbt_covid_data_history['cases'] * lgbt_covid_data_history['LGBT POPULATION DENSITY'] // 100
    lgbt_covid_data_history['lgbt_deaths'] = lgbt_covid_data_history['deaths'] * lgbt_covid_data_history['LGBT POPULATION DENSITY'] // 100
    lgbt_covid_data_history.dropna(inplace=True)
    lgbt_covid_data_history = lgbt_covid_data_history.astype(({'lgbt_cases':'int32', 'lgbt_deaths':'int32'}))
    lgbt_covid_data_history = pd.merge(lgbt_covid_data_history, state_abbreviations, how="inner", on='state')
    history_columns = ['date', 'state', 'county' 'abbreviation', 'fips', 'cases', 'lgbt_cases', 'deaths', 'lgbt_deaths', 'LGBT POPULATION DENSITY']
    current_columns = ['state', 'county', 'abbreviation', 'fips', 'cases', 'lgbt_cases', 'deaths', 'lgbt_deaths', 'LGBT POPULATION DENSITY']
    # final_lgbt_covid_data_history = lgbt_covid_data_history[history_columns].sort_values(by=['date','fips'])
    # final_lgbt_covid_data_history_sum = final_lgbt_covid_data_history.groupby(by=["date"])['cases', 'lgbt_cases', 'deaths', 'lgbt_deaths'].sum()
    # final_lgbt_covid_data_history_sum = final_lgbt_covid_data_history_sum.rename(columns = {'cases': 'us_total_cases_for_date',
    #                                                                                         'lgbt_cases': 'us_total_lgbt_cases_for_date',
    #                                                                                         'deaths': 'us_total_deaths_for_date',
    #                                                                                         'lgbt_deaths': 'us_total_lgbt_deaths_for_date'}, inplace = False)
    # final_lgbt_covid_data_history = pd.merge(final_lgbt_covid_data_history, final_lgbt_covid_data_history_sum,
    #                                          how="inner", on='date')
    # final_lgbt_covid_data_history['lgbt_state_cases_density_for_date'] = final_lgbt_covid_data_history['lgbt_cases'] / final_lgbt_covid_data_history['us_total_lgbt_cases_for_date'] * 100
    # final_lgbt_covid_data_history['lgbt_state_deaths_density_for_date'] = final_lgbt_covid_data_history['lgbt_deaths'] / final_lgbt_covid_data_history['us_total_lgbt_deaths_for_date'] * 100
    final_lgbt_covid_data_current = lgbt_covid_data_history[lgbt_covid_data_history['date'] == yesterday_date]
    final_lgbt_covid_data_current = final_lgbt_covid_data_current[current_columns].sort_values(by=['fips'])
    # total_lgbt_cases = final_lgbt_covid_data_current['lgbt_cases'].sum()
    # total_lgbt_deaths = final_lgbt_covid_data_current['lgbt_deaths'].sum()
    # final_lgbt_covid_data_current['lgbt_state_cases_density'] = final_lgbt_covid_data_current['lgbt_cases'] / total_lgbt_cases * 100
    # final_lgbt_covid_data_current['lgbt_state_deaths_density'] = final_lgbt_covid_data_current['lgbt_deaths'] / total_lgbt_deaths * 100
    #

    final_current_columns = ['state', 'county', 'abbreviation', 'fips', 'lgbt_cases', 'cases']
    final_lgbt_covid_data_current = final_lgbt_covid_data_current[final_current_columns].sort_values(by=['fips'])

    settings = {
        'app_id': 'LGBTQCovidReporting',
        'api_base': 'https://r4.smarthealthit.org'
    }

    smart = client.FHIRClient(settings=settings)




    new_patients = []
    new_observations = []
    new_conditions = []
    # for index, row in final_lgbt_covid_data_current.iterrows():
    #     for i in range(row['lgbt_cases']):
    #         patient_obj = Patient(i, row['fips'], row['state'], row['county'])
    #         new_patients.append(patient_obj)
    #         new_patient = patient_obj.to_fhir_obj()
    #         new_patient_return = new_patient.create(smart.server)
    #         patient_id = new_patient_return['id']
    #         observation_obj = Observation(i, row['fips'], patient_id)
    #         condition_obj = Condition(i, row['fips'], patient_id)
    #         new_observations.append(Observation(i, row['fips'], patient_id))
    #         new_conditions.append(Condition(i, row['fips'], patient_id))
    #         new_observation = observation_obj.to_fhir_obj()
    #         new_condition = condition_obj.to_fhir_obj()
    #         new_observation_return = new_observation.create(smart.server)
    #         new_condition_return = new_condition.create(smart.server)
    #
    #         if i == 1:
    #             break
    #     if len(new_patients) > 1:
    #         break


    # if not smart.ready:
    #     smart.prepare()
    #     smart.ready
    #     smart.prepare()
    #     smart.authorize_url
    #patient = p.Patient.read('06895d41-5937-4e83-9f3d-0af09db31c69', smart.server)
    # patient_name = get_patient_name(patient)
    # patient_ms = get_patient_marital_status(patient)
    # patient_address = get_patient_address(patient)
    # patient_geo_location = get_patient_geo_location(patient)
    # patient.birthDate.isostring
    # patient.name[0].given[0] = 'Patrick'
    # patient.update(smart.server)
    # patient2 = p.Patient.read('06895d41-5937-4e83-9f3d-0af09db31c69', smart.server)

    # patient3 = new_patients[0].to_fhir_obj()
    # patient2.id = None
    #patient2.create(smart.server)
    # patient3.create(smart.server)
    #'836089'

    # patient3observation = new_observations[0].to_fhir_obj()
    # patient3conditon = new_conditions[0].to_fhir_obj()
    #'837492'
    # p3o = patient3observation.create(smart.server)
    #'837493'
    # p3c = patient3conditon.create(smart.server)
    end = "end"
    #   https: // r4.smarthealthit.org / Patient?_has: Condition:patient: code = 840539006 & _has:Observation: patient:code = http: // loinc.org | 76690 - 7  # valueString=Other

    #p.Patient.where({'identifier': '2020-11-28pgood7patientpositive0100100000000000000000'}).perform(smart.server)
    #o.Observation.read('837492', smart.server)
    #b.Bundle.read_from('Patient?_has:Condition:patient:code=840539006&_has:Observation:patient:code=http://loinc.org|76690-7&&_revinclude=Observation:patient&_revinclude=Condition:patient', smart.server)



    fip_list =[]
    fip_data_url="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
    # python 3.x
    r = requests.get(fip_data_url)
    for item in r.json()['features']:
        item_properties = item['properties']
        fip_list.append([item['id'], item_properties['STATE'], item_properties['COUNTY'], item_properties['NAME']])
    fip_data_pd = pd.DataFrame(fip_list, columns=['id', 'state_id', 'county_id', 'county'])



    cat = 'a'
    fips_state_data_url = 'https://raw.githubusercontent.com/PatrickGood/lgbt-covid-data/main/fips_state.csv'
    fips_state_data_df = pd.read_csv(fips_state_data_url, dtype={"fips_code": str}, error_bad_lines=False)


    fips_df = pd.merge(fip_data_pd, fips_state_data_df, 'inner', left_on='state_id', right_on='fips_code')
    fips_df['lookup_key'] = fips_df['state'] + fips_df['county']


    bundle = b.Bundle.read_from(
        '/Patient?_has:Condition:patient:code=http://snomed.info/sct|840539006&_has:Condition:patient:verification-status=http://terminology.hl7.org/CodeSystem/condition-ver-status|confirmed&_has:Observation:patient:code=http://loinc.org|76690-7&_has:Observation:patient:value-string=Other,Homosexual,Bisexual',
        smart.server)
    fhir_positive_lgbt_cases_df = pd.DataFrame(columns=['key', 'count'])
    fhir_positive_lgbt_cases_lst = []
    if bundle.entry is not None and len(bundle.entry) > 0:
        for entry in bundle.entry:
            patient = None
            if(entry.resource.resource_type == 'Patient'):
                patient = entry.resource
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
        fhir_positive_lgbt_cases_fips_df = pd.merge(fhir_positive_lgbt_cases_df, fips_df, how='inner', left_on='key', right_on='lookup_key')
        final_stats = fhir_positive_lgbt_cases_fips_df.groupby('id')['count'].sum()
        final_stats_states = pd.merge(final_stats, fips_df, how='inner', on='id')
        final_stats_states = final_stats_states[['id', 'count', 'fips_code', 'post_code', 'lookup_key']]
        final_stats_states_population = pd.merge(final_stats_states, final_lgbt_covid_data_current, how='inner', left_on='id', right_on='fips')
        final_data_frame = final_stats_states_population[['fips', 'state', 'county', 'post_code', 'count', 'cases', 'lgbt_cases']]




        with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
            counties = json.load(response)

        # Choropleth showing Covid 19 Positive Cases by State Affecting LGBT Population Over Time

        live_lgbt_cases_map_fig_div = plot(px.choropleth(final_data_frame,
                                                         geojson=counties,
                                                         locations="fips",
                                                         color="count",
                                                         color_continuous_scale='reds',
                                                         hover_name="county",
                                                         hover_data=["count", "cases", "state", "county"],
                                                         scope="usa",
                                                         title='Current Live Covid 19 Total Positive Cases affecting LGBT Population',
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
                                                         },
                                                         ))
    end = "almost"





class Condition:
    def __init__(self, condition_number, fips, patient_id):
        self.id = str(datetime.utcnow().date()) + "pgood7condition" + fips + f'{condition_number:016}' + '0'
        self.subject_reference = "Patient/" + patient_id
        self.date = datetime.utcnow().isoformat()

    def to_fhir_obj(self):
        condition = c.Condition(base_condition)
        #observation.subject_reference = self.subject_reference
        condition.subject.reference = self.subject_reference
        return condition
class Observation:
    def __init__(self, observation_number, fips, patient_id):
        self.id = str(datetime.utcnow().date()) + "pgood7observation" + fips + f'{observation_number:016}' + '0'
        self.subject_reference = "Patient/" + patient_id
        self.date = datetime.utcnow().isoformat()
        #sexual_orientations = ['Bisexual', 'Heterosexual', 'Homosexual', 'Other', 'Asked but unknown', 'Unknown']
        sexual_orientations = ['Bisexual', 'Homosexual', 'Other']
        self.sexual_orientation = random.choice(sexual_orientations)

    def to_fhir_obj(self):
        observation = o.Observation(base_observation)
        #observation.subject_reference = self.subject_reference
        observation.subject.reference = self.subject_reference
        observation.performer[0].reference = self.subject_reference
        observation.effectiveDateTime = fd.FHIRDate(str(datetime.utcnow().isoformat()))
        observation.issued = fd.FHIRDate(str(datetime.utcnow().isoformat()))
        observation.valueString = self.sexual_orientation
        return observation

class Patient:
    def __init__(self, patient_number,fips, state, district):
        first_names = ["Avery", "Riley", "Jordan", "Angel", "Parker", "Sawyer", "Peyton", "Quinn", "Blake", "Hayden",
                       "Taylor", "Alexis", "Emerson", "Harley", "Emery", "Elliot", "Spencer", "Skyler", "Rylan"]
        self.first_name = random.choice(first_names)
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Good",
                      "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore",
                      "Jackson", "Martin", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez",
                      "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen",
                      "Hill", "Adams", "Nelson Baker", "Hall", "Mitchell", "Roberts", "Phillips", "Evans"]
        self.last_name = random.choice(last_names)
        sexs = ["male", "female", "other"]
        self.sex = random.choice(sexs)
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=365*100)
        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days
        random_number_of_days = random.randrange(days_between_dates)
        random_date = start_date + timedelta(days=random_number_of_days)

        self.birth_date = random_date
        self.id = str(datetime.utcnow().date()) + "pgood7patientpositive" + fips + f'{patient_number:016}' + '0'
        self.district = district
        self.state = state
    def to_fhir_obj(self):
        patient = p.Patient()
        identifier = p.identifier.Identifier()
        identifier.value = self.id
        patient.identifier = [identifier]
        name = hn.HumanName()
        name.given = [self.first_name]
        name.family = self.last_name
        patient.name = [name]
        patient.gender = self.sex
        patient.birthDate =fd.FHIRDate(str(datetime.utcnow().date()))
        # prints patient's JSON representation, now with id and name
        address = a.Address()
        address.state = self.state
        address.district = self.district
        patient.address = [address]
        json = patient.as_json()
        return patient






if __name__ == "__main__":
    create_data()
