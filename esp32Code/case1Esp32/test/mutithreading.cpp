#include <Arduino.h>
#include <WiFi.h>

TaskHandle_t Task1, Task2, Task3;

void codeForTask1( void * parameter ) {
   for (;;) {
      delay(500);
      Serial.print("Task1 on Core:");Serial.println( xPortGetCoreID());
      
   }
}

void codeForTask2( void * parameter ) {
   for (;;) {
      delay(500);
      Serial.print("                         Task2 on Core:");Serial.println( xPortGetCoreID());
      
   }
}

void codeForTask3( void * parameter ) {
   for (;;) {
      delay(500);
      Serial.print("                                                  Task3 on Core:");Serial.println( xPortGetCoreID());
      
   }
}

void setup() {
   Serial.begin(115200);
   /*Syntax for assigning task to a core:
   xTaskCreatePinnedToCore(
                    coreTask,   // Function to implement the task
                    "coreTask", // Name of the task 
                    10000,      // Stack size in words 
                    NULL,       // Task input parameter 
                    0,          // Priority of the task 
                    NULL,       // Task handle. 
                    taskCore);  // Core where the task should run 
   */
   xTaskCreatePinnedToCore(    codeForTask1,    "FibonacciTask",    4096,      NULL,    2,    &Task1,    0);
   delay(500);  // needed to start-up task1
   xTaskCreatePinnedToCore(    codeForTask2,    "SumTask",    5000,    NULL,    2,    &Task2,    1);
   xTaskCreatePinnedToCore(    codeForTask3,    "SumTask",    5000,    NULL,    2,    &Task3,    1);
}

void loop() {}