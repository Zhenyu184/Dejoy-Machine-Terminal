#!/usr/bin/python3
from queue import Queue
from re import T
from threading import Thread
#from http.server import SimpleHTTPRequestHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import final
from urllib.parse import parse_qs, urlparse
from pyngrok import ngrok
import http.server
import requests
import RPi.GPIO as GPIO #樹梅派用
import json
import time
import sys

#外部程式呼叫
from nowTime import nowTime #nowTime.timestamp()

#---------------網路變數宣告區---------------#
globalProtocol = "HTTP/1.0"
globalHeaders = {'Content-Type': 'application/json'}
globalUrl = "163.13.133.185:3000"
globalHost = "localhost"
globalPort = 8000

#---------------終端變數宣告區---------------#
globalDeviceId = "dj113001"
globalDescription = "東海龍珠"
globalLocate = "威秀店"
globalIdDevice = "遊戲機"
globangrokUrl = "https://yyyyyy.jp.ngrok.io"
globalQueue = Queue(maxsize=32)

#---------------GPIO變數宣告區---------------#
globaCoinReset = 1 #控制投幾枚硬幣就觸發
globaCoinCounter  = 17
globaLotteryMotor = 27
globaLotteryCounter = 22

#---------------預設回傳宣告區---------------#
defaultReply = {
    "code": "Success",
    "message": "ok",
    "results": {
        "ack": 1
    } 
}
defaultWebhook = {
    "events": [{
        "type":"coinPulse",
        "timestamp": nowTime.timestamp(),
        "source": {
            "vendorHwid": globalDeviceId,
            "count": 1,
            "inputPortId":1,
            "offline":False
        } 
    }]
}

defaultupdateUrl = {
    "events": [{
        "type":"ngrokUrl",
        "timestamp": nowTime.timestamp(),
        "source": {
            "vendorHwid": globalDeviceId,
            "ngrokUrl": globangrokUrl
        } 
    }]
}


#---------------從模組id判斷意思---------------#
def modelIdToMean(_id):
    #輸入_id字串
    #輸出二個參數 1.整數(int) 2.模組名(string)
    _id = str(_id)[-2:]
    id = int(_id)
    #從_id分要求(要幹嘛)
    if _id[0] == '1':
        mode1 = "投幣口" #幾次投幣
    elif _id[0] == '2':
        mode1 = "出票口" #幾次出票
    elif _id[0] == '3':
        mode1 = "裁票口" #裁多少票
    elif _id[0] == '4':
        mode1 = "電源" #電源
    else:
        mode1 = "unknown"

    return id % 10, mode1

#---------------pyngrok產生外部網址執行續---------------#
def getngrokServer():
    http_tunnel= ngrok.connect(8000)

    try:
        while True:
            print("-----------------------------------")
            # Block until CTRL-C or some other terminating event
            #webhookNgrokUrl給中間server
            print(http_tunnel)
            print("type=", type(http_tunnel.public_url),http_tunnel.public_url)
            
            #檢查該模組機譨是否正常
            model = '11'

            #將模組的ngrok送出
            webhookRaw = defaultupdateUrl
            webhookRaw["events"][0]["type"] = "ngrokUrl"
            webhookRaw["events"][0]["timestamp"] = nowTime.timestamp()
            webhookRaw["events"][0]["source"]["vendorHwid"] = globalDeviceId + model
            webhookRaw["events"][0]["source"]["ngrokUrl"] = str(http_tunnel.public_url)
            webhookRaw = json.dumps( webhookRaw, ensure_ascii=False, indent=2)
            print("[main.internalServer] 送出Webhook:",webhookRaw)
            #Webhook送出
            #try:
            print(type(webhookRaw))
            print(type(globalHeaders), globalHeaders)
            response = requests.post( globalUrl + '/updateUrl', webhookRaw, globalHeaders, timeout=0.01)
            print("[main.internalServer] state: ",response.status_code ," response: " , response.json())
            #except:
            print("向",globalUrl + '/updateUrl'+"[main.internalServer] ngrokUrl失敗")

            time.sleep(5*60)    # sleep for 5 minutes
    finally:
        print(" Shutting down ngrok.")
        ngrok.kill()
#---------------監聽外部迴圈區---------------#
class responseServer(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        print("[main.externalServer] 接受GET要求")
        #print("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        
        #URL解析
        path = urlparse(self.path).path #拿路徑
        parameters = parse_qs(urlparse(self.path).query) #拿參數

        if path == "/request/state":
            print("[main.externalServer] 問狀態")
            
            #根據_id參數設定回內容
            MoudelId = str(parameters["_id"])[-4:-2] #取後2位數成字串
            modelNumber, model = modelIdToMean(MoudelId)

            #檢查該模組機譨是否正常

            #回應中間server
            self.send_response(200)
            self._set_response()
            replyTemp = defaultReply
            replyTemp["code"] = "Success"
            replyTemp["message"] = "ok"
            replyTemp["results"] = {
                "vendorHwid": globalDeviceId + MoudelId,
                "description": globalDescription + '-' + str(modelNumber) + '號' + model,
                "locate": globalLocate,
                "model": model
            }
            replydData = json.dumps(replyTemp, indent=4, ensure_ascii=False) #解析成JSON
            self.wfile.write(bytes(str(replydData), "utf-8"))

        elif path == "/request/power":
            print("[main.externalServer] 要求開關機")
            
            #根據_id參數設定回內容
            MoudelId = str(parameters["_id"])[-4:-2] #取後2位數成字串，用來辨識model id
            position = int(str(parameters["position"])[2]) #用來辨識要開要關的key
            modelNumber, model = modelIdToMean(MoudelId)

            #根據position進行開機或關機

            #回應中間server
            self.send_response(200)
            self._set_response()
            replyTemp = defaultReply
            replyTemp["code"] = "Success"
            replyTemp["message"] = "ok"
            replyTemp["results"] = {}
            replydData = json.dumps(replyTemp, indent=4, ensure_ascii=False) #解析成JSON
            self.wfile.write(bytes(str(replydData), "utf-8"))
        else:
            print("[main.externalServer] get非法請求")
            
            #回應中間server
            self.send_response(404)
            self._set_response()
            replyTemp = defaultReply
            replyTemp["code"] = "Fail"
            replyTemp["message"] = "Fuck"
            replydData = json.dumps(replyTemp, indent=4, ensure_ascii=False) #解析成JSON
            self.wfile.write(bytes(str(replydData), "utf-8"))

    def do_POST(self):
        
        #區域變數宣告區
        count = 0
        action = ""

        #URL解析
        path = urlparse(self.path).path #拿路徑
        parameters = parse_qs(urlparse(self.path).query) #拿參數

        #解析POST RAW
        print("[main.externalServer] 接受POST要求")
        content_length = int(self.headers['Content-Length']) #抓POST header長度
        rawData = self.rfile.read(content_length) #解析RAW內容(Python string)
        #print("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n", str(self.path), str(self.headers), rawData.decode('utf-8'))
        rawJSON = json.loads(rawData.decode('utf-8')) #解析成JSOM
        _id = rawJSON["_id"]
        count = rawJSON["count"]

        #分離_id後2碼(要幹嘛)
        _id = str(_id)[-2:]

        #把動作加入Queue
        if globalQueue.full() == False: #如果Queue沒滿
            globalQueue.put(str(_id) + ":" + str(count)) 
            print("[main.externalServer] Queue=",list(globalQueue.queue))

        #回覆中間server
        replyTemp = defaultReply
        self.send_response(200)
        self._set_response()
        replyTemp = defaultReply
        replyTemp["code"] = "Success"
        replyTemp["message"] = "ok"
        replyTemp["results"] = {}
        replydData = json.dumps(replyTemp, indent=4, ensure_ascii=False) #解析成JSON
        self.wfile.write(bytes(str(replydData), "utf-8"))

#---------------監聽外部的執行續---------------#
def externalServer( ):
    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = globalPort
    handlerClass = BaseHTTPRequestHandler
    serverClass  = HTTPServer
    serverAddress = (globalHost, port) #設定監聽
    handlerClass.protocol_version = globalProtocol #設定協定
    handlerClass = responseServer
    httpd = serverClass(serverAddress, handlerClass)
    sa = httpd.socket.getsockname()
    try:
        print("[main.externalServer] 開始監聽:", sa[0], "port =", sa[1]) #顯示執行資訊
        httpd.serve_forever() #開始執行
    except KeyboardInterrupt:
        pass

    httpd.server_close()
    print("[main.externalServer] externalServer停止執行\n") #停止執行

def webhookRequest(action, Id, count):
    #Webhook準備
    webhookRaw = defaultWebhook
    webhookRaw["events"][0]["type"] = action
    webhookRaw["events"][0]["timestamp"] = nowTime.timestamp()
    webhookRaw["events"][0]["source"]["vendorHwid"] = Id
    webhookRaw["events"][0]["source"]["count"] = count
    webhookRaw["events"][0]["source"]["inputPortId"] = 3
    webhookRaw["events"][0]["source"]["offline"] = False
    webhookRaw = json.dumps( webhookRaw, ensure_ascii=False, indent=2)
    print("[main.internalServer] 送出Webhook:",webhookRaw)
    
    #Webhook送出
    try:
        response = requests.post( globalUrl + '/webhook', webhookRaw, globalHeaders, timeout=0.01)
        print("[main.internalServer] state: ",response.status_code ," response: " , response.json())
    except:
        print("向",globalUrl + '/webhook'+"[main.internalServer] Webhook失敗")

def GPIOEmpty(CoinLastStatus, LotteryLastStatus):
    try:
        #偵測有無投幣或出票(腳位設定)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(globaCoinCounter , GPIO.IN, pull_up_down=GPIO.PUD_UP) #設定17腳位為input  
        GPIO.setup(globaLotteryMotor, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(globaLotteryCounter, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        #偵測投幣腳位有無投幣
        CoinTempStatus = CoinLastStatus #更新第二最新狀態
        reCoinLastStatus = GPIO.input(globaCoinCounter) #更新最新狀態
        
        if CoinTempStatus == 1 and reCoinLastStatus == 0: #負緣觸發(偵測投幣)
            
            #webhook資料回傳
            action = "coinPulse"
            Id = globalDeviceId + "11"
            count = 1         
            webhookRequest(action, Id, count)

        #偵測有無出票(腳位設定)        
        LotteryTempStatus = LotteryLastStatus #更新第二最新狀態
        reLotteryLastStatus = GPIO.input(globaLotteryCounter) #更新最新狀態
        MotorStatus = GPIO.input(globaLotteryMotor)
        Count_N = 0    
        if MotorStatus == 1: #馬達為高電位時
            if(LotteryTempStatus == 0 and reLotteryLastStatus == 1): #正緣觸發(偵測出票數)
                Count_N = Count_N + 1
                count = Count_N

                #webhook資料回傳
                action = "lotteryPulse"
                Id = globalDeviceId + "21"     
                webhookRequest(action, Id, count)
                print("偵測出票數:",count)
        elif MotorStatus == 0 and Count_N != 0: #偵測結束，webhook設置
            Count_N = 0

        #回傳上個狀態
        return reCoinLastStatus, reLotteryLastStatus

    finally:
        #清除腳位設定
        GPIO.cleanup() 


def GPIOPop(LotteryLastStatus, model, count):

    #初始GPIO腳位宣告區
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(globaCoinCounter , GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(globaLotteryMotor, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(globaLotteryCounter, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    #硬體投幣/出票處理
    if model == "投幣口":   #模擬投幣訊號
        
        #腳位設定
        GPIO.setup(globaCoinCounter, GPIO.OUT)        

        #GPIO輸出指定幣數  
        for i in range(int(count)):
            GPIO.output(globaCoinCounter, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(globaCoinCounter, GPIO.LOW)
            time.sleep(0.05)

        #webhook資料回傳
        action = "coinPulse"
        Id = globalDeviceId + "11"        
        webhookRequest(action, Id, count) 

    elif model == "出票口":  #模擬出票訊號
        
        #腳位設置
        GPIO.setup(globaLotteryMotor, GPIO.OUT)
        GPIO.output(globaLotteryMotor, GPIO.HIGH)
        Count_N = 0

        #指定票數出票
        while True:
            if(Count_N < int(count)):
                time.sleep(0.01) #取樣1次/1ms
                LotteryTempStatus = LotteryLastStatus #更新第二最新狀態
                LotteryLastStatus = GPIO.input(globaLotteryCounter) #更新最新狀態
                if(LotteryTempStatus == 0 and LotteryLastStatus == 1):  #正緣觸發(偵測出票數)
                    Count_N = Count_N + 1
            else:
                break
        GPIO.output(globaLotteryMotor, GPIO.LOW)

        #webhook資料回傳
        action = "lotteryPulse"
        Id = globalDeviceId + "21"      
        webhookRequest(action, Id, count)

    else:
        print(print("[main.GPIOPop] model = 無此模組"))
    
    #清除腳位設定
    GPIO.cleanup() 
    

#---------------監聽內部的執行續---------------#
def internalServer( ):
    #初始變數宣告區
    reCoinLastStatus = 0     #投幣機現在狀態
    reLotteryLastStatus = 0  #出票機現在狀態

    while True:
        time.sleep(0.01) 
        #GPIO.cleanup() #偵測

        if globalQueue.empty(): #Queue是否為空
            #print("[main.internalServer] Queue是空的") 
            CoinLastStatus = reCoinLastStatus
            LotteryLastStatus = reLotteryLastStatus
            reCoinLastStatus, reLotteryLastStatus = GPIOEmpty(CoinLastStatus, LotteryLastStatus)          

        else: #Queue有東西(pop出來)
            print("[main.internalServer] Queue=",list(globalQueue.queue))
            popTemp = globalQueue.get()
            _id = popTemp.split(':')[0]
            count = popTemp.split(':')[1]

            #解析_id意義
            modelNumber, model = modelIdToMean(_id)

            LotteryLastStatus =reLotteryLastStatus
            GPIOPop(LotteryLastStatus, model, count)

    print("[main.internalServer] internalServer停止執行\n") #停止執行
        
#---------------主執行續---------------#
if __name__=="__main__":
    Thread1 = Thread(target=externalServer)
    Thread2 = Thread(target=internalServer)
    Thread3 = Thread(target=getngrokServer)
    Thread1.start()
    Thread2.start()
    Thread3.start()
    Thread1.join()
    Thread2.join()
    Thread3.join()
else: 
    print("[main.py] 幹電腦掛了")