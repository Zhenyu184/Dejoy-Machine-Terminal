from machine import UART, Pin
import utime,time

SSID='Zhenyu的iPhone' #Zhenyu的iPhone DJ-Guest
password = '000000000' #000000000 0227731355
ServerIP = '163.13.133.185'
Port = '3010'

uart = UART(0, 115200)

def sendCMD(cmd,ack,timeout=2000):
    uart.write(cmd+'\r\n')
    t = utime.ticks_ms()
    while (utime.ticks_ms() - t) < timeout:
        s=uart.read()
        if(s != None):
            s=s.decode()
            print(s)
            if(s.find(ack) >= 0):
                return True
    return False

uart.write('+++')
time.sleep(1)
if(uart.any()>0):uart.read()
sendCMD("AT","OK")
print("設定模式")
sendCMD("AT+CWMODE=3","OK")
print("連線到AP")
sendCMD("AT+CWJAP=\""+SSID+"\",\""+password+"\"","OK",20000)
print("回傳本機AP資訊")
sendCMD("AT+CIFSR","OK")
print("啟動TCP或UDP連接")
sendCMD("AT+CIPSTART=\"TCP\",\""+ServerIP+"\","+Port,"OK",10000)
print("用於選擇TCPIP應用模式")
sendCMD("AT+CIPMODE=1","OK")
print("設定發送的數據長度")
sendCMD("AT+CIPSEND",">")

uart.write('Hello World !!!\r\n')
uart.write('ESP8266 TCP Client\r\n')
uart.write('ESP8266 TCP Client\r\n')
while True:
    s=uart.read()
    if(s != None):
        s=s.decode()
        print(s)
