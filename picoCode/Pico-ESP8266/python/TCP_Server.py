from machine import UART, Pin
import utime,time

SSID='OpenWrt'
password = 'mywifi1213'
Port = '8080'

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

def sendData(ID,data):
    sendCMD('AT+CIPSEND='+str(ID)+','+str(len(data)),'>')
    uart.write(data)

def ReceiveData():
    s=uart.read()
    if(s != None):
        s=s.decode()
        print(s)
        if(s.find('+IPD') >= 0):
            n1=s.find('+IPD,')
            n2=s.find(',',n1+5)
            ID=int(s[n1+5:n2])
            n3=s.find(':')
            s=s[n3+1:]
            #print("ID="+str(ID) + ", Data="+s)
            return ID,s
    return None,None

uart.write('+++')
time.sleep(1)
if(uart.any()>0):uart.read()
sendCMD("AT","OK")
sendCMD("AT+CWMODE=3","OK")
sendCMD("AT+CWJAP=\""+SSID+"\",\""+password+"\"","OK",20000)
sendCMD("AT+CIPMUX=1","OK")
sendCMD("AT+CIPSERVER=1,"+Port,"OK")
sendCMD("AT+CIFSR","OK")

while True:
    ID,s=ReceiveData()
    if(ID != None):
        sendData(ID,s)
