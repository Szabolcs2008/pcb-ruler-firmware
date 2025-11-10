#include "builtin_systemStats.h"
#include "driver/adc.h"
#include "esp_adc_cal.h"
#include <LittleFS.h>

bool syss_exit = false;
bool JustStarted = false;
uint8_t lastButtonState = 0;
int info_text_row = 0;
const int numberOfStats = 5;

uint16_t voltageHistory[VOLTAGE_HISTORY_BUFFER_SIZE];
int voltageHistoryIndex = 0;

uint16_t arrayavg(uint16_t *array, int size) {
    unsigned long long sum = 0;
    for (int i = 0; i < size; i++) {
        sum += array[i];
    }
    return (uint16_t)(sum/size);
}

bool SysStats::loop() {
    display.clearDisplay();
    display.setCursor(0, 7-(info_text_row*FONT.yAdvance));
    voltageHistory[voltageHistoryIndex] = (uint16_t)adc1_get_raw(ADC1_CHANNEL_0);
    voltageHistoryIndex = (voltageHistoryIndex + 1) % VOLTAGE_HISTORY_BUFFER_SIZE;
    uint32_t voltage_mV = esp_adc_cal_raw_to_voltage(arrayavg(voltageHistory, VOLTAGE_HISTORY_BUFFER_SIZE), &adcCharacteristics);
    

    String infoStr;
    infoStr.reserve(384);
    infoStr += "Firmware: ";
    infoStr += VERION_STRING;
    infoStr += "\n";
    
    if (voltage_mV > 2850) {
        infoStr += "Battery voltage: >2850mV\n";
    } else {
        infoStr += "Battery voltage: ";
        infoStr += String(voltage_mV, 10);
        infoStr += "mV\n";
    }
    infoStr += "Free RAM: ";
    infoStr += String(ESP.getFreeHeap(), 10);
    infoStr += " bytes\n";

    infoStr += "Storage: ";
    infoStr += String(LittleFS.usedBytes());
    infoStr += "/";
    infoStr += String(LittleFS.totalBytes());
    infoStr += " bytes\n";
    

    infoStr += "Power on time: ";
    infoStr += String(millis()/1000);
    infoStr += "s\n";
    
    display.print(infoStr);
    display.drawFastHLine(0, 0, 128, BLACK);
    display.drawFastHLine(0, 1, 128, WHITE);
    display.fillRect(0, 23, 127, 21, BLACK);
    display.drawFastHLine(0, 24, 128, WHITE);
    renderButtonsHorizontal(display, "Up", "Down", "", "Exit", false);
    display.display();
    return syss_exit;
}

void SysStats::reset() {
    syss_exit = false;
    JustStarted = true;
    uint16_t n = (uint16_t)adc1_get_raw(ADC1_CHANNEL_0);
    for (size_t i = 0; i < VOLTAGE_HISTORY_BUFFER_SIZE; i++) {
        voltageHistory[i] = n;
    }
}

void SysStats::handleButtons(uint8_t buttons) {
    if (JustStarted) {lastButtonState = buttons; JustStarted = false; return;}
    if (lastButtonState != buttons) {
        if (buttons == bit(3) && !lastButtonState) {
            syss_exit = true;
        } else if (buttons == bit(0) && !lastButtonState) {
            info_text_row--;
            if (info_text_row < 0) info_text_row = 0; 
        } else if (buttons == bit(1) && !lastButtonState) {
            
            info_text_row++;
            if (info_text_row > numberOfStats-3) info_text_row = numberOfStats-3; 
        }
        lastButtonState = buttons;
    }
}