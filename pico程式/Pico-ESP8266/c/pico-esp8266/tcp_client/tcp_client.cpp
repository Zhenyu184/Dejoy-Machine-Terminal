#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include <string.h>

#define UART_ID uart0
#define BAUD_RATE 115200

// We are using pins 0 and 1, but see the GPIO function select table in the
// datasheet for information on which other pins can be used.
#define UART_TX_PIN 0
#define UART_RX_PIN 1

char SSID[] = "OpenWrt";
char password[] = "mywifi1213";
char ServerIP[] = "192.168.9.147";
char Port[] = "8080";
char s[50]="";
char buf[100] = {0} ;

bool sendCMD(const char * cmd,const char * act,int timeout=2000) {
	
	int i=0;
	uint64_t t = 0;
	
	uart_puts(UART_ID, cmd);
	uart_puts(UART_ID, "\r\n");
	
	t = time_us_64();
	while(time_us_64() - t < timeout*1000)
	{
		while(uart_is_readable_within_us(UART_ID,2000)){
			buf[i++] = uart_getc(UART_ID);
		}
		if(i>0){
			buf[i]='\0';
			printf("%s\r\n",buf);
			if(strstr(buf,act) != NULL){	
				return true;
			}else{
				i=0;
			}
		}
	}
	//printf("false\r\n");
	return false;
}

int main() {
	stdio_init_all();
	sleep_ms(1000);
	sleep_ms(1000);
	sleep_ms(1000);
	sleep_ms(1000);
	sleep_ms(1000);
	
    // Set up our UART with the required speed.
    uart_init(UART_ID, BAUD_RATE);

    // Set the TX and RX pins by using the function select on the GPIO
    // Set datasheet for more information on function select
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);

	uart_puts(UART_ID, "+++");
	sleep_ms(1000);
	while(uart_is_readable(UART_ID))uart_getc(UART_ID);
	
	sendCMD("AT","OK");
	sendCMD("AT+CWMODE=3","OK");
	
	sprintf(s,"AT+CWJAP=\"%s\",\"%s\"",SSID,password);
	sendCMD(s,"OK",20000);
	
	sendCMD("AT+CIFSR","OK");
	
	sprintf(s,"AT+CIPSTART=\"TCP\",\"%s\",%s",ServerIP,Port);
	sendCMD(s,"OK",10000);
	
	sendCMD("AT+CIPMODE=1","OK");
	sendCMD("AT+CIPSEND",">");
	
	uart_puts(UART_ID, "Hello World !!!\r\n");
	uart_puts(UART_ID, "ESP8266 TCP Client\r\n");
	
	int i=0;
	while (true) {
		while(uart_is_readable_within_us(UART_ID,10000)){
			buf[i++] = uart_getc(UART_ID);
		}
		if(i>0){
			buf[i]='\0';
			printf("%s\r\n",buf);
			uart_puts(UART_ID, buf);
			i=0;
		}
    }
	
}
