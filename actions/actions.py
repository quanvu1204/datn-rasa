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
import feedparser
from firebase_admin import credentials
from firebase_admin import db
import logging
import random

translator = Translator()
cred = credentials.Certificate("/Users/quanvu/Study/datn-rasa/beem-assistant-firebase-adminsdk-ozdxf-011253b9bc.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://beem-assistant-default-rtdb.firebaseio.com'
})

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
        val = tracker.get_slot('session_started_metadata')
        try:
            result = ''
            response = requests.get('http://localhost:4000/device/find-by-id/{}'.format(val))
            res = response.json()
            for item in res['data']['rows']:
                status = "bật" if (item['device']['status'] == "on") else "tắt"
                timer = ", sẽ được " + item['device']['timer']['status'] + " lúc " + item['device']['timer']['time'] if (item['device']['timer'] is not None) else ""
                result = result + 'Tên thiết bị: ' + item['device']['name'] + ', trạng thái: ' + status + timer + '\n'
            if result == '':
                dispatcher.utter_message('Chưa có thiết bị nào hết, bạn hãy quét thiết bị mới và thêm vào nhaaa !')
            else:
                dispatcher.utter_message(result)
        except Exception:
            logging.exception("message")
            dispatcher.utter_message("Ái chà có lỗi gì đó chăng, bạn đợi Beem xíu nha :D")
            return []
        return []

class ActionControlDevice(Action):
    def name(self) -> Text:
        return 'action_control_device'

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        device = str(tracker.get_slot('device')).lower()
        status = str(tracker.get_slot('status')).lower()
        try:
            ref = db.reference('/devices')
            devices = ref.get()
            foundDevices = False
            ip = ''
            key = ''
            for keyID in devices:
                if str(devices[keyID]['name']).lower() == device:
                    foundDevices = True
                    key = keyID
                    ip = str(devices[keyID]['ip'])
            if foundDevices == True:
                ref.child(key).update({
                    'status': status
                })
                data = {'status': 'on' if status == 'bật' else 'off', 'ip': ip }
                requests.put('http://localhost:4000/device/update', data = data)
                dispatcher.utter_message(tracker.get_slot('device') + " đã " + status + ".\nBạn có yêu cầu gì nữa không ạ?")
            else:
                dispatcher.utter_message("Không tìm thấy thiết bị bạn yêu cầu, hãy xem lại danh sách thiết bị nhé")
                
        except Exception:
            logging.exception("message")
            dispatcher.utter_message("Ái chà có lỗi gì đó chăng, bạn đợi Beem xíu nha :D")
            return []
        return []

class ActionWeather(Action):
    def name(self) -> Text:
        return 'action_get_weather'

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        city = str(tracker.get_slot('city')).lower()
        try:
            response = requests.get('http://localhost:4000/common/get-all-city', params={'name': city})
            code = response.json()['data']['locationKey']
            weatherUrl = 'http://dataservice.accuweather.com/forecasts/v1/daily/5day/{}?language=vi&apikey=MYK2ft8867WcdABYvHtHABVDOJ4Dtrrd'.format(code)
            resWeather = requests.get(weatherUrl)
            result = resWeather.json()
            dispatcher.utter_message(
                "Thời tiết hôm nay: Nhiệt độ từ " + str(round((result['DailyForecasts'][0]['Temperature']['Minimum']['Value'] - 32) * 5 / 9)) + " độ C đến " + str(round((result['DailyForecasts'][0]['Temperature']['Maximum']['Value'] - 32) * 5 / 9)) + " độ C. Ban ngày: " + result['DailyForecasts'][0]['Day']['IconPhrase'] + ", ban đêm: " + result['DailyForecasts'][0]['Night']['IconPhrase'] + ".\n" + 
                "Dự báo thời tiết ngày mai: Nhiệt độ từ " + str(round((result['DailyForecasts'][1]['Temperature']['Minimum']['Value'] - 32) * 5 / 9)) + " độ C đến " + str(round((result['DailyForecasts'][1]['Temperature']['Maximum']['Value'] - 32) * 5 / 9)) + " độ C. Ban ngày: " + result['DailyForecasts'][1]['Day']['IconPhrase'] + ", ban đêm: " + result['DailyForecasts'][1]['Night']['IconPhrase'] + ".\n" + 
                "Bonus thêm ngày hôm kia nữa nè: Nhiệt độ từ " + str(round((result['DailyForecasts'][2]['Temperature']['Minimum']['Value'] - 32) * 5 / 9)) + " độ C đến " + str(round((result['DailyForecasts'][2]['Temperature']['Maximum']['Value'] - 32) * 5 / 9)) + " độ C. Ban ngày: " + result['DailyForecasts'][2]['Day']['IconPhrase'] + ", ban đêm: " + result['DailyForecasts'][2]['Night']['IconPhrase'])
            dispatcher.utter_message("Nhớ lưu ý nè: " + result['Headline']['Text'])
        except Exception:
            logging.exception("message")
            dispatcher.utter_message("Ái chà có lỗi gì đó chăng, bạn đợi Beem xíu nha :D")
            return []
        return []

class ActionLottery(Action):
    def name(self) -> Text:
        return 'action_get_lottery'

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        url = 'https://xskt.com.vn/rss-feed/mien-bac-xsmb.rss'
        feed_cnt = feedparser.parse(url)
        first_node = feed_cnt['entries']
        return_msg = first_node[0]['title'] + "\n" + first_node[0]['description']
        dispatcher.utter_message(return_msg)
        return []

class ActionGetFood(Action):
    def name(self) -> Text:
        return 'action_get_food'

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            url = 'https://naungonmoingay.com/feed/'
            feed_cnt = feedparser.parse(url)
            first_node = feed_cnt['entries']
            food = random.choice(first_node)
            ns = food['content']
            return_msg = "Hôm nay tôi sẽ chọn cho bạn món: " + food['title']
            return_link = "Link: " + food['link']
            dispatcher.utter_message(return_msg)
            dispatcher.utter_message(image=str(ns[0]['value'].split('src="')[1].split('"')[0]))
            dispatcher.utter_message(return_link)
            return []
        except Exception:
            logging.exception("message")
            dispatcher.utter_message("Ái chà có lỗi gì đó chăng, bạn đợi Beem xíu nha :D")
        return []

class ActionGetFood(Action):
    def name(self) -> Text:
        return 'action_control_device_timer'

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            device = str(tracker.get_slot('device')).lower()
            status = str(tracker.get_slot('status')).lower()
            hour = tracker.get_slot('hour')
            minute = tracker.get_slot('minute')
            hourModified = hour.split(" giờ")[0] if (hour is not None) else "00"
            hourlastModified = hourModified if (len(hourModified) == 2) else "0" + hourModified
            minuteModified = minute.split(" phút")[0] if (minute is not None) else "00"
            minutelastModified = minuteModified if (len(minuteModified) == 2) else "0" + minuteModified
            ref = db.reference('/devices')
            devices = ref.get()
            foundDevices = False
            ip = ''
            key = ''
            for keyID in devices:
                if str(devices[keyID]['name']).lower() == device:
                    foundDevices = True
                    key = keyID
                    ip = str(devices[keyID]['ip'])
            if foundDevices == True:
                ref.child(key).update({
                    'timer': { "status": status, "time": hourlastModified + ":" + minutelastModified + ":00" }
                })
                data = {'ip': ip, 'timer': { "status": status, "time": hourlastModified + ":" + minutelastModified + ":00" } }
                headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
                requests.put('http://localhost:4000/device/update', data = json.dumps(data), headers=headers)
                dispatcher.utter_message(tracker.get_slot('device') + " sẽ " + status + " lúc " + hourlastModified  + ":" + minutelastModified + ":00" + ".\nBạn có yêu cầu gì nữa không ạ?")
            else:
                dispatcher.utter_message("Không tìm thấy thiết bị bạn yêu cầu, hãy xem lại danh sách thiết bị nhé")
        except Exception:
            logging.exception("message")
            dispatcher.utter_message("Ái chà có lỗi gì đó chăng, bạn đợi Beem xíu nha :D")
        return []