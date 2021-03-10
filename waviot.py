#!/usr/bin/env python
import requests
import json
from pprint import pprint

class Waviot:
    login_url='https://auth.waviot.ru/?action=user-login'
    get_tree_url='https://lk.waviot.ru/api.tree/get_tree/'
    get_modems_url='https://lk.waviot.ru/api.tree/get_modems/'
    
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
        #print(url)
        header = {'Content-type': 'application/json',
                  'X-requested-with': 'XMLHttpRequest',
                  'Authorization': 'bearer ' + self.WAVIOT_JWT}
        r=requests.get(url,headers=header)
        if r.status_code==200:
            try:
                reqresponse=json.loads(r.text)
                self.response=reqresponse
            except:
                print(f"no response {r.text}")
        else:
            print("error",r.status_code)
            print("something goes wrong - headers:\n",r.headers)
        return reqresponse

    def print_raw_response(self):
        print(self.response)


    def print_response_roll(self):
        for modem in self.response:
            print(f"---{modem}---")
            for record in self.response[modem]:
                print("===== NEW RECORD {} =======\n {} \n===========\n".format(record['protocol'],record))
                try:
                    print("timestamp: {}, snr: {}, rssi: {}, station: {}".format(
                          record['timestamp'],
                          record['snr'],record['rssi'],record['station_id']))
                except:
                    print("no")
                if record['protocol']=='water7':
                    try:
                        for sensor in record['data'].values():
                            print("sensor:{},value:{}".format(sensor['name'],sensor['value']))
                        print("\n==========\n")
                    except:
                        print ("no")
                elif record['protocol']=='water6':
                    code=record['payload'][-8:-4]
                    print(code)
                else:
                    print(f"no parser for proto {record['data']}")

            print("----------------")
        return True


    
    def get_subtree(self,elem_id):
        url=f'{self.get_tree_url}?id={elem_id}'
        reqresponse=self.get_request(url)
        subtree={}
        if reqresponse.get('tree')!=None:
            subtree=reqresponse['tree']
        return subtree

 
    def get_modems_inelem(self,elem_dict):
        elem_id=elem_dict['id']   
        url=f'{self.get_modems_url}?id={elem_id}'
        reqresponse=self.get_request(url)
        modems={}
        if reqresponse.get('modems')!=None:
            for modem in reqresponse.get('modems'):
                modems[modem['id']]={'flavor_id':modem['flavor_id'],
                                     'temperature':modem['temperature'],
                                    'battery':modem['battery'],
                                    'elem_name':elem_dict['name'],
                                    'elem_type':elem_dict['type']
                                    }
        return modems
    
    def get_modems_intree(self,elem_id):
        elements=self.get_subtree(elem_id)
        modems={}
        for element in elements.values():
           
            modems.update(self.get_modems_inelem(element))
        return modems

