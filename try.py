#!/usr/bin/env python
import os
from pprint import pprint
from datetime import datetime
import time
import logging

from ansible_vault import Vault         
from ansible.parsing.vault import VaultLib, VaultSecret
from ansible.constants import DEFAULT_VAULT_ID_MATCH

import waviot
import tg

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def get_creds_vault(vault_file,vault_password):                                         
    vault = Vault(vault_password)                                                      
    secrets = vault.load(open(vault_file).read())                                
    #####HACK for ansible version https://github.com/tomoh1r/ansible-vault/pull/34      
    #vault = VaultLib([(DEFAULT_VAULT_ID_MATCH, VaultSecret(vault_password.encode()))])  
    #secrets = yaml.safe_load(vault.decrypt(open(vault_file).read()))                    
    #####                                                                               
#    print(secrets)                                                                    
    return secrets          


def send_alarm(creds,msg):
    sender=tg.Tg(creds['tg_token'])
    chat_id=creds['chat_id']
    sender.send_msg(chat_id,msg)
    #sender.send_msg(,msg)
    logging.debug(f"send msg to {chat_id} : {msg}")
    
def lk_water_event(tg_token,event):
    modem=event['modem_id']
    event_type=event['event_type']
    dec_code=event['code']['decimal']
    descr=event['description']
    date_time=event['date_time']
    if dec_code==40:
        alarm_msg=(f"{date_time} модем: {modem} событие: {descr} ")
        print(alarm_msg)
        send_alarm(tg_token,alarm_msg)

def lk_event_parser(tg_token,response):
    #pprint(response)
    if response['status']=="ok":
        for gmt_timestamp,event in response['events'].items():
            event_type=event['event_type']
            if event_type=='water':
                lk_water_event(tg_token,event)
    else:
        print("error status in response")


def helper_list_modems(modems):
    modem_hex=[]
    modem_dec=[]
    for modem in modems.keys():
        modem_hex.append(modem)
        modem_dec.append(str(int(modem,16)))
    modems_list=[modem_hex,modem_dec]
    
    return modems_list

#def wa_search_water

def roll_event_parser(response,significant_diff):
    
    significant_diff=float(significant_diff)
    alarms=[]
    alarm={}
    for modem in response.keys():
        prev_value=0
        for record in response[modem]:
            if record['protocol']=='water7':
                current_value=record['data']['0']['value']
                timestamp=record['timestamp']
                alarm_key=f'{timestamp}-{modem}'
                diff=prev_value-current_value
                if round(current_value)>=20:
                    alarm[alarm_key]={'timestamp':timestamp,'modem_id':modem,'value':current_value,'state':'За пределами измерений'}
                    #alarms.append(alarm)
                elif round(current_value)<=4:
                    alarm[alarm_key]={'timestamp':timestamp,'modem_id':modem,'value':current_value,'state':'За пределами измерений'}
                    #alarms.append(alarm)
                elif diff>significant_diff:
                    alarm[alarm_key]={'timestamp':timestamp,'modem_id':modem,'value':current_value,'state':'Падение давления'}
                    #alarms.append(alarm)
                elif current_value<6.7:
                    alarm[alarm_key]={'timestamp':timestamp,'modem_id':modem,'value':current_value,'state':'Давление меньше 1бар'}
                elif current_value>10:
                    alarm[alarm_key]={'timestamp':timestamp,'modem_id':modem,'value':current_value,'state':'Давление больше уставки '}

                logging.debug(f"modem {modem} event water7 timestamp:{timestamp}, current_value: {current_value}, prev_value: {prev_value}, diff: {diff}")
                prev_value=current_value
            elif record['protocol']=='water6': #and record['tag']=='water6.pair.1':
                code=record['payload'][-8:-4]
                timestamp=record['timestamp']
                alarm_key=f'{timestamp}-{modem}'
                if code=='0028':
                    alarm[alarm_key]={'timestamp':timestamp,'modem_id':modem,'value':'протечка','state':'Замыкание контактов'}
                    #alarms.append(alarm)
                logging.debug(f"event water6 timestamp:{timestamp}, code: {code}")
            else:
                print(f"no parser for proto {record['data']}")
                logging.debug(f"no parser for proto {record['data']}")
    return alarm

def alarm_manage(creds,alarms,modems):
    #pprint(modems)
    utc_offset=10800
    for key,alarm in alarms.items():
        alarm_modem_id=hex(int(alarm['modem_id']))[2:]
        date_time=datetime.utcfromtimestamp(alarm['timestamp']+utc_offset).strftime('%Y-%m-%d %H:%M:%S')
        modem_name=modems[alarm_modem_id]['elem_name']
        temperature=modems[alarm_modem_id]['temperature']
        pressure=((alarm['value']-4)/16)*6
        alarm_message=f"{date_time} модем: {alarm_modem_id} ({alarm['modem_id']})) температура: {temperature}\n Место установки: {modem_name} событие: {alarm['state']} ({pressure:.2f}бар) - ток {alarm['value']}"
        if alarm_modem_id!='7a48ad':
            send_alarm(creds,alarm_message)



def main():
    now_date=int(datetime.now().timestamp())
    readabledate=datetime.utcfromtimestamp(now_date+10800).strftime('%Y-%m-%d %H:%M:%S')
    old_date=int(datetime.now().timestamp())-3600
    
    print(f"run {now_date}")
    logging.debug(f"run {now_date}({readabledate})")

    vault_pass=os.getenv('VAULT',default='unknown')
    creds=get_creds_vault('secret.yml',vault_pass)
    wa=waviot.Waviot(creds['login'],creds['password'])
    wa.get_login()
    #$modems=wa.get_modems_intree('827132')
    modems=wa.get_modems_intree('195984')
    
    mlist=helper_list_modems(modems)
    get_values=wa.get_request(f"https://api.waviot.ru/api/roll?modem_id={','.join(mlist[1])}&from={old_date}&to={now_date}")

    #response=wa.get_request("https://lk.waviot.ru/api.data/get_events/?modem_id=721D7C,7A48AC&from=1614187030&to=1614188330")
    #wa.print_raw_response()
    #wa.print_response_roll()
    alarms=roll_event_parser(get_values,0.5)
    alarm_manage(creds,alarms,modems)
    #lk_event_parser(creds['tg_token'],response)

if __name__=="__main__":
    logging.debug(f"==============START==================")
    while True:
        main()
        time.sleep(1800)
    



