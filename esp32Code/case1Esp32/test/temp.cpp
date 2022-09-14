#include <Arduino.h>
#include <WiFiMulti.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiUdp.h>
#include <queue>


//pins 宣告
const int  onboardLed1 = 2;
const int  coinModelCounter = 4; //投幣機計數脈衝
const int  TicketModelCounter = 16; //出票機計數脈衝
const int  TicketModelmotor = 17; //出票機馬達
enum statusFlag {
      execution = 1, connectedInternet, connectedServer
}statusFlag;

//工作執行緒宣告
TaskHandle_t taskHeartbeat, taskStatusLED, taskRealCoin, taskRealTime;

//相關全域變數
String globleId = "dj113001";
String globleServerPath = "http://163.13.133.185:3001";
QueueHandle_t globleQueue;


//[執行緒]heartbeat 2秒向server發出一次通訊
void heartbeat( void * parameter ) {
    HTTPClient http;
    String serverPath = globleServerPath + "/heartbeat";
    String httpRequestData = "{}";
    int httpResponseCode = 0;
    
    while (true) {
      if(WiFi.status()== WL_CONNECTED){
        http.begin(serverPath.c_str());
        http.setTimeout(1200);
        httpResponseCode = http.POST(httpRequestData);
        if (httpResponseCode > 0) {
          Serial.println("[heartbeat] heartbeat success!");
          statusFlag = connectedServer;
        } else {
          Serial.print("[heartbeat] heartbeat Error code: ");
          Serial.println(httpResponseCode);
          statusFlag = connectedInternet;
        }
        delay(2000); //2秒確認一次
      }else {
        Serial.println("[watchDog] WiFi Disconnected");
      } 
    }
}

//[執行緒]板子上的LED狀態改變
void statusLED( void * parameter ){
  //初始化腳位
  pinMode(onboardLed1, OUTPUT);
  
  short highTime = 1000;
  short lowTime = 0;
  while (true) {
    if(statusFlag == execution){
      highTime = 30;
      lowTime = 200;
    }else if(statusFlag == connectedInternet){
      highTime = 300;
      lowTime = 300;
    }else if(statusFlag == connectedServer){
      highTime = 1000;
      lowTime = 0;
    }else{
      highTime = 0;
      lowTime = 1000;
    }
    digitalWrite(onboardLed1, HIGH);
    delay(highTime);
    digitalWrite(onboardLed1, LOW);
    delay(lowTime);
  }
}

//[執行緒]監聽有無真實投幣
void realCoin( void * parameter ){
  //宣告
  bool lastStatus = false;
  bool preStatus = false;
  bool prepreStatus = false;
  String httpRequestData = "{\"events\": [{\"type\":\"coinPulse\",\"timestamp\": 1662455264123,\"source\": {\"vendorHwid\": \"dj11300111\",\"count\": 1,\"inputPortId\":1,\"offline\":false}}]}";

  //初始化腳位
  pinMode(coinModelCounter, INPUT_PULLUP);
  //Serial.print(digitalRead(coinModelCounter));
  
  //監聽
  while (true){
    prepreStatus = preStatus;
    preStatus = lastStatus;
    lastStatus = digitalRead(coinModelCounter);
    if( prepreStatus == true && preStatus == true && lastStatus == false){ //負緣觸發(有投幣)
      Serial.println("[realCoin] 真實投幣");
      if(WiFi.status()== WL_CONNECTED){
        WiFiClient client;
        HTTPClient http;
        http.begin(client, globleServerPath + "/webhook");
        http.addHeader("Content-Type", "application/x-www-form-urlencoded");
        int httpResponseCode = http.POST(httpRequestData);
        break;
      }
    }
    delay(5);
  }
}

//[函  式]負責校準時間
unsigned long long timeCalibration( void ){
  struct tm timeinfo;
  const long gmtOffsetSec = 8* 3600;
  const long dayLightOffsetSec = 0;
  const char* ntpServer = "pool.ntp.org";
  
  Serial.println("[timeCalibration] 時間校準");
  configTime(gmtOffsetSec, dayLightOffsetSec, ntpServer);
  if( !getLocalTime(&timeinfo) ){
    return 1;
  }
  return 0;
}

//[函  式]取得現在時間
int64_t getTimestamp() {
	struct timeval tv;
	gettimeofday(&tv, NULL);
	return (tv.tv_sec * 1000LL + (tv.tv_usec / 1000LL));
}

//[函  式]負責連上網路
void wifiConnect( void ){
  WiFiMulti wifiMulti;
  WiFi.mode(WIFI_STA);

  //wifiMulti.h方法
  //wifiMulti.addAP("威秀wifi", "12346789");
  //wifiMulti.addAP("zhenyu的iphone", "12346789"); 
  //while (wifiMulti.run() != WL_CONNECTED) {
    //statusFlag = execution;
  //}

  //WiFi.h方法
  WiFi.begin("威秀wifi", "12346789");
  while (WiFi.status() != WL_CONNECTED) {
    statusFlag = execution;
    delay(500);
  }
  
  //WiFi.h方法
  statusFlag = connectedInternet;
  Serial.println("\n[wifiConnect] Wi-Fi is connect");
  Serial.print("[wifiConnect] SSID：");
  Serial.println(WiFi.SSID());
  Serial.print("[wifiConnect] IP位址：");
  Serial.println(WiFi.localIP());
  Serial.print("[wifiConnect] WiFi RSSI: ");
  Serial.println(WiFi.RSSI());
}

//[函  式]加入工作列對push
void pushQueue( void * element ){
  xQueueSend( globleQueue, &lValueToSend, portMAX_DELAY );
}

//[函  式]移出工作列對pop
void popQueue( void ){

}

void setup() {
  //初始化
  Serial.begin(9600); //設定uart胞率
  statusFlag = execution; //設定程式狀態
  globleQueue = xQueueCreate( 16, sizeof( int ) ); //設定工作列對
  if(globleQueue == NULL){
    Serial.println("Error creating the queue");
  }

  //初始化腳位(執行緒可能會更改)
  pinMode(onboardLed1, OUTPUT); 

  //開啟「狀態燈」執行續在核心0
  xTaskCreatePinnedToCore( statusLED, "statusLED", 1024, NULL, 2, &taskStatusLED, 0);
  
  //呼叫連線
  wifiConnect( );

  //時間校準(調用pool.ntp.org)
  timeCalibration( );

  //開啟「heartbeat」執行續在核心0
  xTaskCreatePinnedToCore( heartbeat, "heartbeat", 4096, NULL, 2, &taskHeartbeat, 0);

  //開啟「realCoin」執行續在核心0
  xTaskCreatePinnedToCore( realCoin, "realCoin", 4096, NULL, 2, &taskRealCoin, 1);

}

void loop() {

}