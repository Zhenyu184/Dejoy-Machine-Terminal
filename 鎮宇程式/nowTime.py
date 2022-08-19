#參考:https://blog.csdn.net/BIT_666/article/details/112968334
#呼叫這個程式會給出時間戳(string)
import time

class nowTime:
    
    def timestamp():
        now = time.time()
        #print(int(round(now*1000)))
        return round(now*1000)



