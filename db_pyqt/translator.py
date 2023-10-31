import json

import requests

API_URL = "https://clients5.google.com/translate_a/t"
API_URL = "https://translate.googleapis.com/translate_a/single"
CLIENT = 'dict-chrome-ex'
CLIENT = 'gtx'


class Translator:

    def __init__(self, translate_from, translate_to, filename='translations.json'):
        self.payload = {
            "client": CLIENT,
            "dt": "t",

            "sl": translate_from,
            "tl": translate_to,
            "q": ""
        }
        self.filename = filename
        with open(filename, 'a+', encoding='utf-8') as file:
            if file.read():
                self.translated = json.load(file)
            else:
                self.translated = {}

    def translate(self, word):

        if word in self.translated:
            return self.translated[word]
        else:
            return word

        self.payload['q'] = word
        with requests.Session() as session:
            request = session.post(API_URL, self.payload)
            if request.status_code == 200:
                translation = request.json()[0][0][0]
                self.translated[word] = translation
                with open(self.filename, 'w+', encoding='utf-8') as file:
                    json.dump(self.translated, file)
                return translation
            return word
