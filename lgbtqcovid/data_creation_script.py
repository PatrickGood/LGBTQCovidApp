#Developed by Patrick Good
#GATECH ID: pgood7
import json
import random
from datetime import datetime, timedelta
from time import time

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

def create_data(smart):

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
    current_columns = ['state', 'county', 'abbreviation', 'fips', 'cases', 'lgbt_cases', 'deaths', 'lgbt_deaths', 'LGBT POPULATION DENSITY']
    final_lgbt_covid_data_current = lgbt_covid_data_history[lgbt_covid_data_history['date'] == yesterday_date]
    final_lgbt_covid_data_current = final_lgbt_covid_data_current[current_columns].sort_values(by=['fips'])

    final_current_columns = ['state', 'county', 'abbreviation', 'fips', 'lgbt_cases', 'cases']
    final_lgbt_covid_data_current = final_lgbt_covid_data_current[final_current_columns].sort_values(by=['fips'])

    sorted_final_lgbt_covid_data_current = final_lgbt_covid_data_current.sort_values(['lgbt_cases'], ascending=False)
    sorted_final_lgbt_covid_data_current.reset_index(inplace=True)

    timeb = time()
    for index, row in sorted_final_lgbt_covid_data_current.iterrows():
        for i in range(row['lgbt_cases']):
            patient_obj = Patient(i, row['fips'], row['state'], row['county'])
            new_patient = patient_obj.to_fhir_obj()
            new_patient_return = new_patient.create(smart.server)
            patient_id = new_patient_return['id']
            observation_obj = Observation(i, row['fips'], patient_id)
            condition_obj = Condition(i, row['fips'], patient_id)
            new_observation = observation_obj.to_fhir_obj()
            new_condition = condition_obj.to_fhir_obj()
            new_observation_return = new_observation.create(smart.server)
            new_condition_return = new_condition.create(smart.server)
        row_end = "end"
    timee = time() - timeb
    end = "end"



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




def create_data_if_FHIR_Server_returns_none():
    settings = {
        'app_id': 'LGBTQCovidReporting',
        'api_base': 'https://r4.smarthealthit.org'
    }

    smart = client.FHIRClient(settings=settings)

    bundle = b.Bundle.read_from(
        '/Patient?_has:Condition:patient:code=http://snomed.info/sct|840539006&_has:Condition:patient:verification-status=http://terminology.hl7.org/CodeSystem/condition-ver-status|confirmed&_has:Observation:patient:code=http://loinc.org|76690-7&_has:Observation:patient:value-string=Other,Homosexual,Bisexual',
        smart.server)
    if bundle.entry is None or len(bundle.entry) < 1:
        create_data(smart)

if __name__ == "__main__":
    settings = {
        'app_id': 'LGBTQCovidReporting',
        'api_base': 'https://r4.smarthealthit.org'
    }

    smart = client.FHIRClient(settings=settings)
    #create_data_if_FHIR_Server_returns_none()
    create_data(smart)
