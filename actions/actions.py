# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from googletrans import Translator
import pycountry
import requests
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

translator = Translator()

class ActionLookUpWordDictionary(Action):
    def name(self) -> Text:
        return 'action_look_up_en'

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        word = str(tracker.get_slot('enword')).lower()
        if not word:
            dispatcher.utter_message("Ối chà chà!, từ này tớ chưa học đến rồi. Bạn tra từ khác nha :D")
            return []
        try:        
            url = 'https://api.tracau.vn/WBBcwnwQpV89/s/{}/en'.format(word)
            response = requests.get(url).text
            dispatcher.utter_message("Nghĩa của từ " + word + " là: " + json.loads(response)['sentences'][0]['fields']['vi'])
        except Exception:
            dispatcher.utter_message("Ối chà chà!, từ này tớ chưa học đến rồi. Bạn tra từ khác nha :D")
            return []
        return []

class ActionGetLatestTotalsCovidByCountry(Action):
    def name(self) -> Text:
        return 'action_get_latest_totals_by_country'

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = str(tracker.get_slot('country')).lower()
        try:
            country = translator.translate(name, src="vi", dest='en')
            country_code = pycountry.countries.search_fuzzy(country.text)
            url = "https://covid-19-data.p.rapidapi.com/country/code"
            querystring = {"code": country_code[0].alpha_2}
            headers = {
                'x-rapidapi-key': "e116b345b9msh0917524f228b7ddp1a37fdjsn11a357103197",
                'x-rapidapi-host': "covid-19-data.p.rapidapi.com"
                }
            response = requests.request("GET", url, headers=headers, params=querystring)
            dispatcher.utter_message(
                "Theo nguồn tin mật từ chính phủ " + str(tracker.get_slot('country')) + " thì tới thời điểm này: \n"
                "Số người nhiễm bệnh: " + str(json.loads(response.text)[0]['confirmed']) + " người.\n" + 
                "Số người hồi phục: " + str(json.loads(response.text)[0]['recovered']) + " người.\n" + 
                "Số người nguy kịch: " + str(json.loads(response.text)[0]['critical']) + " người.\n" + 
                "Số người chết: " + str(json.loads(response.text)[0]['deaths']) + " người.")   
        except Exception:
            dispatcher.utter_message("Ối chà chà!, có vẻ như đất nước này tớ không tra ra được rồi. Bạn tra thử nước khác nha ^^")
            return []
        return []

class ActionGetLatestTotalsCovid(Action):
    def name(self) -> Text:
        return 'action_get_latest_totals'

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            url = "https://covid-19-data.p.rapidapi.com/totals"
            querystring = {"format":"json"}
            headers = {
                'x-rapidapi-key': "e116b345b9msh0917524f228b7ddp1a37fdjsn11a357103197",
                'x-rapidapi-host': "covid-19-data.p.rapidapi.com"
                }
            response = requests.request("GET", url, headers=headers, params=querystring)
            dispatcher.utter_message(
                "Theo nguồn tin mật từ WHO thì tới thời điểm này: \n"
                "Số người nhiễm bệnh: " + str(json.loads(response.text)[0]['confirmed']) + " người.\n" + 
                "Số người hồi phục: " + str(json.loads(response.text)[0]['recovered']) + " người.\n" + 
                "Số người nguy kịch: " + str(json.loads(response.text)[0]['critical']) + " người.\n" + 
                "Số người chết: " + str(json.loads(response.text)[0]['deaths']) + " người.")
        except Exception:
            dispatcher.utter_message("Ái chà có lỗi gì đó chăng, bạn đợi Beem xíu nha :D")
            return []
        return []


class ActionGetDeviceStatus(Action):
    def name(self) -> Text:
        return 'action_get_devices_list'

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            cred = credentials.Certificate("/Users/quanvu/Study/datn-rasa/beem-assistant-firebase-adminsdk-ozdxf-011253b9bc.json")
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://beem-assistant-default-rtdb.firebaseio.com'
            })
            ref = db.reference('/devices')
            devices = ref.get()
            result = ''

            for keyID in devices:
                result = result + 'Tên thiết bị: ' + devices[keyID]['name'] + ', trạng thái: ' + devices[keyID]['status']

            if result == '':
                dispatcher.utter_message('Chưa có thiết bị nào hết, bạn hãy quét thiết bị mới và thêm vào nhaaa !')
            else:
                dispatcher.utter_message(result)
        except Exception:
            dispatcher.utter_message("Ái chà có lỗi gì đó chăng, bạn đợi Beem xíu nha :D")
            return []
        return []
