from queue import Queue
from threading import Thread
#from http.server import SimpleHTTPRequestHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
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
globalHeaders = {'Content-type': 'application/json'}
globalUrl = ""
globalHost = "localhost"
globalPort = 8000

#---------------終端變數宣告區---------------#
globalId = "dj12300111"
globalDescription = "東海龍珠-左投幣口"
globalLocate = "淡水店"
globalIdDevice = "遊戲機"
globalIdModel = "投幣模組"
globalQueue = Queue(maxsize=32)

#---------------GPIO變數宣告區---------------#
globaCoinReset = 1 #控制投幾枚硬幣就觸發
globaCoinTempStatus = 0 #投幣機暫時狀態
globaCoinLastStatus = 0 #投幣機現在狀態
globaLotteryTempStatus = 0 #投幣機暫時狀態
globaLotteryLastStatus = 0 #投幣機現在狀態
globaCount_N = 0           #投幣正緣計數
globaCoinCounter  = 17
globaLotteryMotor = 22
globaLotteryCounter = 27

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False) #清除之前的腳位設定
GPIO.setup(globaCoinCounter , GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(globaLotteryMotor, GPIO.OUT)
GPIO.setup(globaLotteryCounter, GPIO.IN)

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
            "vendorHwid": globalId,
            "count": 1,
            "inputPortId":1,
            "offline":False
        } 
    }]
}

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
            
            #回應中間server
            self.send_response(200)
            self._set_response()
            replyTemp = defaultReply
            replyTemp["code"] = "Success"
            replyTemp["message"] = "ok"
            replyTemp["results"] = {
                "vendorHwid": globalId,
                "description": globalDescription,
                "locate": globalLocate,
                "model": globalIdModel
            }
            replydData = json.dumps(replyTemp, indent=4, ensure_ascii=False) #解析成JSON
            self.wfile.write(bytes(str(replydData), "utf-8"))

        elif path == "/request/power":
            print("[main.externalServer] 要求開關機")
            
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
        _id = globalId
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

        #從_id分要求(要幹嘛)
        if _id[8] == '1':
            action = "coinPulse" #幾次投幣
        elif _id[8] == '2':
            action = "lotteryPulse" #幾次出票
        elif _id[8] == '3':
            action = "shredPulse" #裁多少票
        elif _id[8] == '4':
            action = "powerPulse" #電源
        else:
            action = "unknownPulse"

        #把動作加入Queue
        if globalQueue.full() == False: #如果Queue沒滿
            globalQueue.put(action + ":" + str(count)) 
            print("[main.externalServer] Queue=",list(globalQueue.queue))

        #回覆中間server
        replyTemp = defaultReply
        self.send_response(200)
        self._set_response()
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

#---------------監聽內部的執行續---------------#
def internalServer( ):
    globaCoinTempStatus = 0 #投幣機暫時狀態
    globaCoinLastStatus = 0 #投幣機現在狀態
    globaLotteryTempStatus = 0 #投幣機暫時狀態
    globaLotteryLastStatus = 0 #投幣機現在狀態
    globaCount_N = 0           #投幣負緣計數
    while True:
        time.sleep(0.01) 
        if globalQueue.empty(): #Queue是空的
            print("[main.internalServer] Queue是空的")
            
            #偵測有無投幣(腳位設定)              
            globaCoinTempStatus = globaCoinLastStatus #更新第二最新狀態
            globaCoinLastStatus = GPIO.input(globaCoinCounter) #更新最新狀態
            if globaCoinLastStatus == 0 and globaCoinTempStatus == 1:#負緣觸發   
                action =  "lotteryPulse"
                count = 1

                #Webhook準備
                webhookRaw = defaultWebhook
                webhookRaw["events"][0]["type"] = action
                webhookRaw["events"][0]["timestamp"] = nowTime.timestamp()
                webhookRaw["events"][0]["source"]["vendorHwid"] = globalId
                webhookRaw["events"][0]["source"]["count"] = count
                webhookRaw["events"][0]["source"]["inputPortId"] = globalId[9]
                webhookRaw["events"][0]["source"]["offline"] = False
                webhookRaw = json.dumps( webhookRaw, ensure_ascii=False, indent=2)
                print("[main.internalServer] 送出Webhook:",webhookRaw)
                
                #Webhook送出
                try:
                    response = requests.post( globalUrl + '/webhook', webhookRaw, globalHeaders, timeout=0.01)
                    print("[main.internalServer] state: ",response.status_code ," response: " , response.json())
                except:
                    print("[main.internalServer] Webhook失敗")

            #偵測有無出票(腳位設定)
            GPIO.setup(globaLotteryMotor, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            globaLotteryTempStatus = globaLotteryLastStatus #更新第二最新狀態
            globaLotteryLastStatus = GPIO.input(globaLotteryCounter) #更新最新狀態

            if globaLotteryMotor == 0:
                if(globaLotteryLastStatus == 0 and globaLotteryTempStatus == 1):  #負緣觸發
                    globaCount_N = globaCount_N + 1
                    count = globaCount_N

            elif globaLotteryMotor == 1 and globaCount_N != 0:                
                globaCount_N = 0
                action =  "lotteryPulse"

                #Webhook準備
                webhookRaw = defaultWebhook
                webhookRaw["events"][0]["type"] = action
                webhookRaw["events"][0]["timestamp"] = nowTime.timestamp()
                webhookRaw["events"][0]["source"]["vendorHwid"] = globalId
                webhookRaw["events"][0]["source"]["count"] = count
                webhookRaw["events"][0]["source"]["inputPortId"] = globalId[9]
                webhookRaw["events"][0]["source"]["offline"] = False
                webhookRaw = json.dumps( webhookRaw, ensure_ascii=False, indent=2)
                print("[main.internalServer] 送出Webhook:",webhookRaw)
                
                #Webhook送出
                try:
                    response = requests.post( globalUrl + '/webhook', webhookRaw, globalHeaders, timeout=0.01)
                    print("[main.internalServer] state: ",response.status_code ," response: " , response.json())
                except:
                    print("[main.internalServer] Webhook失敗")


        else: #Queue有東西(pop出來)
            print("[main.internalServer] Queue=",list(globalQueue.queue))
            popTemp = globalQueue.get()
            action = popTemp.split(':')[0]
            count = popTemp.split(':')[1]

            #硬體投幣/出票處理
            if action == "coinPulse":
                pass
            elif action == "lotteryPulse":
                GPIO.setup(globaLotteryMotor, GPIO.OUT)
                #GPIO輸出票
                GPIO.output(globaLotteryMotor, GPIO.HIGH)
                globaCount_N = 0
                while True:
                    if(globaCount_N < count):
                        time.sleep(0.01) #取樣1次/1ms
                        globaLotteryTempStatus = globaLotteryLastStatus #更新第二最新狀態
                        globaLotteryLastStatus = GPIO.input(globaLotteryCounter) #更新最新狀態

                        if(globaLotteryLastStatus == 1 and globaLotteryTempStatus == 0):  #正緣觸發
                            globaCount_N = globaCount_N + 1
                    else:
                        break
                GPIO.output(globaLotteryMotor, GPIO.LOW)
            else:
                pass

            #Webhook準備
            webhookRaw = defaultWebhook
            webhookRaw["events"][0]["type"] = action
            webhookRaw["events"][0]["timestamp"] = nowTime.timestamp()
            webhookRaw["events"][0]["source"]["vendorHwid"] = globalId
            webhookRaw["events"][0]["source"]["count"] = count
            webhookRaw["events"][0]["source"]["inputPortId"] = globalId[9]
            webhookRaw["events"][0]["source"]["offline"] = False
            webhookRaw = json.dumps( webhookRaw, ensure_ascii=False, indent=2)
            print("[main.internalServer] 送出Webhook:",webhookRaw)
            
            #Webhook送出
            try:
                response = requests.post( globalUrl + '/webhook', webhookRaw, globalHeaders, timeout=0.01)
                print("[main.internalServer] state: ",response.status_code ," response: " , response.json())
            except:
                print("[main.internalServer] Webhook失敗")

    print("[main.internalServer] internalServer停止執行\n") #停止執行
        
#---------------主執行續---------------#
if __name__=="__main__":
    Thread1 = Thread(target=externalServer)
    Thread2 = Thread(target=internalServer)
    Thread1.start()
    Thread2.start()
    Thread1.join()
    Thread2.join()
else: 
    print("[main.py] 幹電腦掛了")