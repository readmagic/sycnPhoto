import hashlib
import json
import time
from urllib.parse import urlparse, parse_qsl
import requests


class MiClient:

    def __init__(self, username, password,device_id):
        self._username = username
        self._password = password
        self._agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36'
        self._device_id=device_id
        self._session = requests.session()
        self._sign = None
        self._ssecurity = None
        self._userId = None
        self._cUserId = None
        self._passToken = None
        self._location = None
        self._code = None
        self._serviceToken = None

    def __to_json(self, response_text):
        try:
            return json.loads(response_text.replace("&&&START&&&", ""))
        except Exception as e:
            print(e)
            print(response_text)
            return response_text

    def __login_step_1(self):
        url = 'https://i.mi.com/api/user/login?ts=%d&followUp=https://i.mi.com/&_locale=zh_CN' % (time.time() * 1000)
        headers = {
            "User-Agent": self._agent,
            "Content-Type": "application/x-www-form-urlencoded",
            'Referer': 'https://i.mi.com/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',

        }
        response = self._session.get(url, headers=headers, verify=False)
        valid = response.status_code == 200 and "data" in self.__to_json(response.text) and "loginUrl" in self.__to_json(response.text)['data']
        if valid:
            self._loginUrl = self.__to_json(response.text)['data']['loginUrl']
        else:
            return False
        r=self._session.get(self._loginUrl,headers=headers,verify=False)
        u = urlparse(r.url)
        valid=r.status_code==200 and u
        if valid:
            self.params = dict(parse_qsl(u.query))
        return valid


    def __login_step_2(self):
        url = "https://account.xiaomi.com/pass/serviceLoginAuth2"
        headers = {
            "User-Agent": self._agent,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        fields = {
            "hash": hashlib.md5(str.encode(self._password)).hexdigest().upper(),
            "serviceParam": self.params.get('serviceParam'),
            "callback": self.params.get('callback'),
            "qs": self.params.get('qs'),
            "sid": self.params.get('sid'),
            "user": self._username,
            "_sign": self._sign,
            "_json": "true"
        }
        response = self._session.post(url, headers=headers, data=fields, verify=False)
        valid = response.status_code == 200 and "ssecurity" in self.__to_json(response.text)
        if valid:
            json_resp = self.__to_json(response.text)
            self._ssecurity = json_resp["ssecurity"]
            self._userId = json_resp["userId"]
            self._cUserId = json_resp["cUserId"]
            self._passToken = json_resp["passToken"]
            self._location = json_resp["location"]
            self._code = json_resp["code"]
        return valid

    def __login_step_3(self):
        headers = {
            "User-Agent": self._agent,
            'Referer': 'https://i.mi.com/',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
        }
        cookie={
            'iplocale' :'zh_CN',
            'uLocale':'zh_CN',
        }
        response = self._session.get(self._location, headers=headers,cookies=cookie,verify=False)
        if response.status_code == 200:
            self._serviceToken = response.cookies.get("serviceToken")
        return response.status_code == 200

    def login(self):
        self._session.cookies.set("deviceId", self._device_id, domain="mi.com")
        self._session.cookies.set("deviceId", self._device_id, domain="xiaomi.com")
        if self.__login_step_1() and self.__login_step_2() and self.__login_step_3():
            return True
        return False







