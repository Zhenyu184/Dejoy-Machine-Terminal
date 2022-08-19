from machine import UART, Pin
import utime,time

SSID='OpenWrt'
password = 'mywifi1213'
remote_IP = '192.168.9.147'
remote_Port = '8087'
local_Port = '1112'

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
sendCMD("AT+CWMODE=3","OK")
sendCMD("AT+CWJAP=\""+SSID+"\",\""+password+"\"","OK",20000)
sendCMD("AT+CIFSR","OK")
sendCMD("AT+CIPSTART=\"UDP\",\""+remote_IP+"\","+remote_Port+","+local_Port+",0","OK",10000)
sendCMD("AT+CIPMODE=1","OK")
sendCMD("AT+CIPSEND",">")

uart.write('Hello World !!!\r\n')
uart.write('ESP8266 TCP Client\r\n')
while True:
    s=uart.read()
    if(s != None):
        s=s.decode()
        print(s)
        uart.write(s)
