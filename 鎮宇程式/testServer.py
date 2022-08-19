from queue import Queue
from threading import Thread
#from http.server import SimpleHTTPRequestHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import http.server
import requests
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
        self._set_response()
        replydData = json.dumps(replyTemp, indent=4, ensure_ascii=False) #解析成JSON
        self.wfile.write(bytes(str(replydData), "utf-8"))

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

def internalServer( ):
    while True:
        time.sleep(2.05) 
        if globalQueue.empty(): #Queue是空的
            print("[main.internalServer] Queue是空的")
            
            #偵測有無投幣/出票

        else: #Queue有東西(pop出來)
            print("[main.internalServer] Queue=",list(globalQueue.queue))
            popTemp = globalQueue.get()
            action = popTemp.split(':')[0]
            count = popTemp.split(':')[1]

            #硬體投幣/出票處理


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
        

if __name__=="__main__":
    Thread1 = Thread(target=externalServer)
    Thread2 = Thread(target=internalServer)
    Thread1.start()
    Thread2.start()
    Thread1.join()
    Thread2.join()

else: 
    print("[main.py] 幹電腦掛了")