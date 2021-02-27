#!/usr/bin/env python
import requests
import json

class Tg:
    base_url="https://api.telegram.org/bot"
    def __init__(self, token):
        self.token = token
    
    def send_msg(self,tgid,msg):
        construct_url=f"{self.base_url}{self.token}/sendMessage" 
        header = {'Content-type': 'application/json'}
        payload = {"chat_id":tgid,"text":msg}
        r=requests.post(construct_url,data=json.dumps(payload),headers=header)
        if r.status_code==200:
            print("msg send")
        else:
            print(r.status_code)
            print("something goes wrong",r.headers)
        
