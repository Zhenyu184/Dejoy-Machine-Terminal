from queue import Queue
from threading import Thread
#from http.server import SimpleHTTPRequestHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
import http.server
import requests
import json
import datetime
import time
import sys

#---------------網路變數宣告區---------------#
globalProtocol = "HTTP/1.0"
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

class responseServer(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        print("[main.py] 接受GET要求")
        #print("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        
        data = {'do_GET':666}
        self._set_response()
        json_data = json.dumps(data, indent=4, ensure_ascii=False) #解析成JSON
        self.wfile.write(bytes(str(json_data), "utf-8"))

    def do_POST(self):
        print("[main.py] 接受POST要求")
        content_length = int(self.headers['Content-Length']) #抓POST header長度
        post_data = self.rfile.read(content_length) #解析內容
        #print("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n", str(self.path), str(self.headers), post_data.decode('utf-8'))

        if globalQueue.full() == False:
            globalQueue.put("post") #加入Queue
            print(list(globalQueue.queue))

        data = {'do_POST':666}
        self._set_response()
        json_data = json.dumps(data, indent=4, ensure_ascii=False) #解析成JSON
        self.wfile.write(bytes(str(json_data), "utf-8"))

def server1( ):
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
        print("[main.py] 開始監聽:", sa[0], "port =", sa[1]) #顯示執行資訊
        httpd.serve_forever() #開始執行
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("[main.py] 停止執行\n") #停止執行


if __name__=="__main__":
    Thread1 = Thread(target=server1)
    Thread2 = Thread(target=server2)
    Thread1.start()
    Thread2.start()
    Thread1.join()
    Thread2.join()

else: 
    print("[main.py] File1 is being imported")