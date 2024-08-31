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

using namespace std;

const unsigned int msPerHour = 3600000;
const unsigned int maxWatts = 6000;
const unsigned int secondsPerDay = 24*60*60;
const unsigned int minPulseDelta = msPerHour / maxWatts;
const string logPath = "/var/pulseCount/";

unsigned int lastPulse = 0;
unsigned int lastPulseUp = 0;

void pulseUp() {
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
}

void segmentationHandler(int sig) {
    void *array[10];
    size_t size = backtrace(array, 10);

    backtrace_symbols_fd(array, size, STDERR_FILENO);
    exit(1);
}  

int main ()
{
    signal(SIGSEGV, segmentationHandler);
    printf("Setup...\n");
    wiringPiSetup ();

    int pin = 25;

    printf("pullUpDnControl\n");
    pullUpDnControl(pin, PUD_DOWN);
    printf("wiringPiISR RISING\n");
    wiringPiISR (pin, INT_EDGE_RISING, &pulseUp);
    printf("wiringPiISR FALLING\n");
    wiringPiISR (pin, INT_EDGE_FALLING, &pulseDown); 
    
    while (true) {
        delay(1000); 
    }

    return 0 ;
}
