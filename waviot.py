#!/usr/bin/env python
import requests
import json

class Waviot:
    login_url='https://auth.waviot.ru/?action=user-login'
    def __init__(self, login, password):
        self.login = login
        self.password = password

    def get_login(self):
        WAVIOT_JWT=False
        payload = {"login":self.login,"password":self.password}
        header = {'Content-type': 'application/json','X-requested-with': 'XMLHttpRequest'}
        r=requests.post(self.login_url,data=json.dumps(payload),headers=header)
        if r.status_code==200:
            try:
                WAVIOT_JWT=json.loads(r.text)['WAVIOT_JWT']
                #print(WAVIOT_JWT)
                self.WAVIOT_JWT=WAVIOT_JWT
            except:
                print("no WAVIOT_JWT")
        else:
            print(r.status_code)
            print("something goes wrong",r.headers)
        #return WAVIOT_JWT

    def get_request(self,url):
        header = {'Content-type': 'application/json',
                  'X-requested-with': 'XMLHttpRequest',
                  'Authorization': 'bearer ' + self.WAVIOT_JWT}
        r=requests.get(url,headers=header)
        if r.status_code==200:
            try:
                response=json.loads(r.text)
                self.response=response
            except:
                print(f"no response {r.text}")
        else:
            print("error",r.status_code)
            print("something goes wrong - headers:\n",r.headers)
        return response

    def print_raw_response(self):
        print(self.response)


    def parse_response_roll(self):
        for modem in self.response:
            print(f"---{modem}---")
            for record in self.response[modem]:
                print("NEW RECORD {}\n {} \n===========\n".format(record['protocol'],record))
                try:
                    print("timestamp: {}, snr: {}, rssi: {}".format(
                          record['timestamp'],
                          record['snr'],record['rssi']))
                except:
                    print("no")
                if record['protocol']=='water7':
                    try:
                        for sensor in record['data'].values():
                            print("sensor:{},value:{}".format(sensor['name'],sensor['value']))
                        print("\n==========\n")
                    except:
                        print ("no")
                elif record['protocol']!='water7':
                    record['data']

            print("----------------")
        return True