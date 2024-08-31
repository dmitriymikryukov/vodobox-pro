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
int _count=0;
double pc=0;
double extra=0;
unsigned long ms_ts=0;
unsigned long Fdt=0;
double Fcnt=0;
int hold=0;
int rst=0;
double current_pulse_vol=5.0;
double flow_table[10][2]={{1000000,10.00},{10000,12.50},{0,0}};
unsigned long period=0;

void calibrate(unsigned long delta){
    period=delta;
    current_pulse_vol=flow_table[9][1];
    for (int i=0;i<10;i++){
        if (flow_table[i][0]){
            if (delta>=flow_table[i][0] && i==0 || delta==flow_table[i][0]){
                current_pulse_vol=flow_table[i][1];
                break;
            }else if(!flow_table[i+1][0]){
                current_pulse_vol=flow_table[i][1];
                break;
            }else if(delta==flow_table[i+1][0]){
                current_pulse_vol=flow_table[i+1][1];                
                break;
            }else if(delta>flow_table[i+1][0]){
                double dp=flow_table[i][0]-flow_table[i+1][0];
                double dV=flow_table[i+1][1]-flow_table[i][1];
                double d=delta-flow_table[i+1][0];
                double c=d/dp;
                current_pulse_vol=c*dV+flow_table[i][1];
            }
        }else{
            current_pulse_vol=flow_table[i-1][1];
            break;
        }
    }
}

void pulse(){
    static int isodd=0;
    if (isodd){
        unsigned long ts=millis();
        unsigned long delta=ts-ms_ts;
        ms_ts=ts;
        calibrate(delta);
        if (!hold){
            if (rst){
                Fdt=0;
                Fcnt=0;
                rst=0;
            }
            Fdt+=delta;
            Fcnt+=current_pulse_vol;
        }
    }
    //printf("*");
    if (pc>=_count){
        extra+=current_pulse_vol;
        digitalWrite( PUMP_PIN,  LOW );
        digitalWrite( VALVE_PIN,  LOW );        
    }else{
        pc+=current_pulse_vol;        
    }
    isodd=!isodd;
}

void finalize(){
    digitalWrite( PUMP_PIN,  LOW );
    digitalWrite( VALVE_PIN,  LOW );
    int cnt,xtr;
    if ((pc+extra)>=count){
        cnt=count;
        xtr=(pc+extra)-count;
    }else{
        cnt=pc+extra;
        xtr=0;
    }
    printf("\nTOTAL:%dpls EXTRA:%dpls\n",cnt,xtr);
    fflush(stdout);    
}


void segmentationHandler(int sig) {
    void *array[10];
    size_t size = backtrace(array, 10);

    backtrace_symbols_fd(array, size, STDERR_FILENO);

    digitalWrite( PUMP_PIN,  LOW );
    digitalWrite( VALVE_PIN,  LOW );

    exit(2);
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
    _count=(count<80)?count:50;


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
    pc=0;
    current_pulse_vol=flow_table[0][1];
    digitalWrite( VALVE_PIN,  HIGH );
    digitalWrite( PUMP_PIN,  HIGH );
    //int xpc=0;
    //int frq;
    int failc=0;
    int ncal=-1;
    while (pc<count) {
        delay(200);
        //frq=pc-xpc;xpc=pc;
        //frq*=5;
        hold=1;
        double frq;
        if (Fdt){
            frq=Fcnt/Fdt;frq*=1000000.0;
        }else{
            frq=0;
        }
        rst=1;hold=0;
        printf("\r%05dpls %03.1fHz PV:%03.3f per:%06dms     ",(int)pc,frq,current_pulse_vol,period);
        fflush(stdout);
        if (frq<=1 || pc<15){
            failc++;
            if ((_count-pc)<ncal && ncal>=0){
                break;
            }
            if (failc>((pc<50)?40:10)){
                printf("\nTIMEOUT\n");
                break;
            }
        }else {
            failc=0;
        }
        if (pc>=_count && ncal<0){
            delay(600);
            ncal=extra;
            printf(" Extra: %dpls\n",ncal);
            extra=0;
            _count=count-ncal;
            pc+=ncal;
            digitalWrite( VALVE_PIN,  HIGH );
            digitalWrite( PUMP_PIN,  HIGH );
        }
    }
    delay(500);

    finalize();

    return 0 ;
}
