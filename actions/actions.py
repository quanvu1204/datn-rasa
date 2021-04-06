# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
import json

class ActionLookUpWordDictionary(Action):
    def name(self) -> Text:
        return 'action_look_up_en'

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        word = str(tracker.get_slot('enword')).lower()
        if not word:
            dispatcher.utter_message("Ối chà chà!, từ này tớ chưa học đến rồi. Bạn tra từ khác nha :D")
            return []
        url = 'https://api.tracau.vn/WBBcwnwQpV89/s/{}/en'.format(word)
        response = requests.get(url).text
        try:
            dispatcher.utter_message("Nghĩa của từ " + word + " là: " + json.loads(response)['sentences'][0]['fields']['vi'])
        except Exception:
            dispatcher.utter_message("Ối chà chà!, từ này tớ chưa học đến rồi. Bạn tra từ khác nha :D")
            return []
        return []
