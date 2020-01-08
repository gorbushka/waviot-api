#!/usr/bin/env python
import requests
import json

def get_login(inlogin,inpass):
    WAVIOT_JWT=False
    payload = {"login":inlogin,"password":inpass}
    header = {'Content-type': 'application/json','X-requested-with': 'XMLHttpRequest'}
    r=requests.post('https://auth.waviot.ru/?action=user-login',data=json.dumps(payload),headers=header)
    if r.status_code==200:
        try:
            WAVIOT_JWT=json.loads(r.text)['WAVIOT_JWT']
            print(WAVIOT_JWT)
        except:
            print("no WAVIOT_JWT")
    else:
        print(r.status_code)
        print("something goes wrong",r.headers)
    return WAVIOT_JWT

def get_request(url,JWT):
    header = {'Content-type': 'application/json',
              'X-requested-with': 'XMLHttpRequest',
              'Authorization': 'bearer ' + JWT }
    r=requests.get(url,headers=header)
    if r.status_code==200:
        try:
            response=json.loads(r.text)
        except:
            print("no response")
    else:
        print("error",r.status_code)
        print("something goes wrong",r.headers)
    return response
   
def parse_response_roll(injson):
    for modem in injson:
        print(modem)
        for record in injson[modem]:
            print("NEW RECORD\n {} \n===========\n".format(record))
            try:
                print("timestamp: {}, snr: {}, rssi: {}".format(
                          record['timestamp'],
                          record['snr'],record['rssi']))
            except:
                print("no")
            try:
                for sensor in record['data'].values():
                    print("sensor:{},value:{}".format(sensor['name'],sensor['value']))
                print("\n==========\n")
            except:
                print ("no")
    return True

if __name__=="__main__":
    murl='https://api.waviot.ru/api/roll?modem_id=8013997&limit=10'
    login=""
    passw=""
    JWT=get_login(login,passw)
    resp=get_request(murl,JWT)
    parse_response_roll(resp)


