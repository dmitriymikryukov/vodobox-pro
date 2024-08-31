#include <iostream>
#include <ctime>
#include <cstdio>
#include <string>
#include <fstream>
#include <sstream>
#include <wiringPi.h>
#include <sys/time.h>
#include <signal.h>
#include <execinfo.h>
#include <stdlib.h>

#define PUMP_PIN 11
#define VALVE_PIN 0
#define PULSE_PIN 6


using namespace std;

const unsigned int msPerHour = 3600000;
const unsigned int maxWatts = 6000;
const unsigned int secondsPerDay = 24*60*60;
const unsigned int minPulseDelta = msPerHour / maxWatts;
const string logPath = "/var/pulseCount/";

unsigned int lastPulse = 0;
unsigned int lastPulseUp = 0;

/*void pulseUp() {
    lastPulseUp = millis();    
}

void pulseDown() {
    unsigned int time = millis();
    if (time - lastPulseUp < 50) {
        return;
    }
    if (lastPulse == 0) {
        lastPulse = time;
        return;
    }
    
    if (time - lastPulse < minPulseDelta) {
        return;
    }
   
    timeval daytime;
    gettimeofday(&daytime, 0);
    
    int watts = msPerHour / (time - lastPulse);
    time_t t = std::time(0);
    tm * now = localtime(&t) ;
    printf("%d-%d-%d %d:%d:%d %dW\n", now->tm_year + 1900, now->tm_mon + 1, now->tm_mday, now->tm_hour, now->tm_min, now->tm_sec, watts);

    lastPulse = time;
}*/

int count=0;
int pc=0;
int extra=0;

void pulse(){
    //printf("*");
    if (pc>=count){
        extra++;
        digitalWrite( PUMP_PIN,  LOW );
        digitalWrite( VALVE_PIN,  LOW );        
    }else{
        pc++;        
    }
}

void finalize(){
    digitalWrite( PUMP_PIN,  LOW );
    digitalWrite( VALVE_PIN,  LOW );    
    printf("\nTOTAL:%dpls EXTRA:%dpls\n",pc,extra);
    fflush(stdout);    
}


void segmentationHandler(int sig) {
    void *array[10];
    size_t size = backtrace(array, 10);

    backtrace_symbols_fd(array, size, STDERR_FILENO);

    digitalWrite( PUMP_PIN,  LOW );
    digitalWrite( VALVE_PIN,  LOW );

    exit(1);
}  

void stopHandler(int sig) {
    printf("\nBREAK\n");
    finalize();
    exit(1);
}  

void pizda(const char* s){
    digitalWrite( PUMP_PIN,  LOW );
    digitalWrite( VALVE_PIN,  LOW );
    printf("\n%s\n",s);
    printf("Usage:\n");
    printf("flow <pulses>\n");

    exit(1);
}


int main (int argc, char **argv)
{
    signal(SIGSEGV, segmentationHandler);
    signal(SIGKILL, stopHandler);
    signal(SIGTERM, stopHandler);
    signal(SIGINT, stopHandler);
    if (wiringPiSetup ()==-1){
        printf("PIZDEC!\n");
        exit(1);
    }

    if (argc>1){
        count=atoi(argv[1]);
        if (count<5){
            pizda("Too less pulses required");
        }
    }else{
        pizda("Too less arguments");
    }


    pinMode( PUMP_PIN, OUTPUT );
    digitalWrite( PUMP_PIN,  LOW );
    pinMode( VALVE_PIN, OUTPUT );
    digitalWrite( VALVE_PIN,  LOW );

    int pin = PULSE_PIN;

    pullUpDnControl(pin, PUD_DOWN);
    //printf("wiringPiISR RISING\n");
    //wiringPiISR (pin, INT_EDGE_RISING, &pulseUp);
    //printf("wiringPiISR FALLING\n");
    //wiringPiISR (pin, INT_EDGE_FALLING, &pulseDown); 
  
    wiringPiISR (pin, INT_EDGE_BOTH, &pulse); 

    printf("READY\n");
    fflush(stdout);
    digitalWrite( VALVE_PIN,  HIGH );
    digitalWrite( PUMP_PIN,  HIGH );
    pc=0;
    int xpc=0;
    int frq;
    int failc=0;
    while (pc<count) {
        delay(200);
        frq=pc-xpc;xpc=pc;
        frq*=5;
        printf("\r%05dpls %03dHz",pc,frq);
        fflush(stdout);
        if (frq<=10 || pc<15){
            failc++;
            if (failc>((pc<50)?40:10)){
                printf("\nTIMEOUT\n");
                break;
            }
        }else {
            failc=0;
        }
    }
    delay(300);

    finalize();

    return 0 ;
}
