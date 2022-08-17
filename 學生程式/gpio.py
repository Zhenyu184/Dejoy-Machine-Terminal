#import library
import http.client, urllib.parse
import pprint
import json
import sys
import requests  
import RPi.GPIO as GPIO
from time import sleep
from datetime import datetime

#initial var setup
last_status = 1
data_status = 0
coin_count = 0
lotter__count = 0
switch_status = 0
lotteryPcsSec = 0.087
dict = {}
foo = {}
url = 'https://d1b7-60-248-161-128.jp.ngrok.io'
#url = 'https://b645-60-248-161-128.jp.ngrok.io'
#GPIO PIN SETUP
coin_reset = 1
coin_data  = 17


#GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(coin_reset, GPIO.IN)
GPIO.setup(coin_data , GPIO.IN)

#---------------------------#寫入timestamp#---------------------------#
def timestampWrite(): 
    now = datetime.now()
    timestamp = int(datetime.timestamp(now)*1000)
    print("timestamp =", timestamp)
    with open("config_data_1.json", "r", encoding='utf-8')as r:
        dict = json.load(r)
        dict["webhook"]["events"][0]["timestamp"] = timestamp
    with open("config_data_1.json", "w", encoding='utf-8')as w: 
        w.write(json.dumps(dict, ensure_ascii=False, indent=2))
#---------------------------#觸發投幣訊號#---------------------------#
def coinPulse():    
    headers = {'Content-type': 'application/json'}
    #讀出數值
    with open("config_data_1.json", "r", encoding='utf-8')as r:
        coinPulse = json.load(r)
        coinPulse["webhook"]["events"][0]["type"] = "coinPulse"
        coinPulse["webhook"]['events'][0]["source"]["count"] = 1
        coinPulse["coinvalue"]["count"] += 1
    #寫入type、coin變值
    print("Coin write...")
    with open("config_data_1.json", "w", encoding='utf-8')as w: 
        w.write(json.dumps(coinPulse, ensure_ascii=False, indent=2))
    #包裝
    respfoo =coinPulse["webhook"]
    json_data = json.dumps(respfoo,ensure_ascii=False, indent=2)
    #格式
    response = requests.post( url + '/webhook', json_data, headers)
    print("state: ",response.status_code ," response: " , response.json())
    print("#--------------------------------end-----------------------------#"," \n"*2)
#---------------------------#MainProgram#---------------------------#
try:
    print("#-----------------------------CoinMachineRun--------------------#")
    while True:
        #讀出json硬幣
        with open("config_data_1.json", "r", encoding='utf-8')as r:
            foo = json.load(r)
            coin_count = foo["coinvalue"]['count']
        #變數設定
        last_status = data_status
        data_status = GPIO.input(coin_data)
        switch_status = GPIO.input(coin_reset)
        '''
        if switch_status == 0:   #投幣數值歸零
            coin_count = 0
            foo["coinvalue"]['count'] = coin_count
            with open("config_data_1.json", "w", encoding='utf-8')as w: 
                w.write(json.dumps(foo, ensure_ascii=False, indent=2))
        '''
        if data_status == 0 and last_status == 1:
            timestampWrite()    #寫入timestamp
            coinPulse()         #寫入投幣數值
            print("目前總硬幣量:",coin_count)
        sleep(0.05)          
        #print("data_status=",data_status,"count=",coin_count, "switch_status=", switch_status)
finally:
    GPIO.cleanup