#pragma once

#include <Arduino.h>
#include <Adafruit_SSD1306.h>
#include <Wire.h>
#include "LittleFS.h"
#include "apps/baseApplication.h"
#include "font/my_3x5_tiny_mono_pixel_font3pt7b.h"
#include "driver/adc.h"
#include <esp_adc_cal.h>

#define FONT my_3x5_tiny_mono_pixel_font3pt7b

#define VERION_STRING "v2.1.0+release"

#define BUTTON_A 3
#define BUTTON_B 4
#define BUTTON_C 10
#define BUTTON_D 21
#define LED 8

extern Adafruit_SSD1306 display;
extern esp_adc_cal_characteristics_t adcCharacteristics;
enum class SerialHeader {
    Header_Default,
    Header_Text_Bytecount0,
    Header_Text_Bytecount1,
    Header_Text_Bytecount2,
    Header_Text_Bytecount3,
    Data_Text,

    Header_Filesystem_Command,
    
    Header_Filesystem_Upload_Filename,
    Header_Filesystem_Upload_DatalenB0,
    Header_Filesystem_Upload_DatalenB1,
    Header_Filesystem_Upload_DatalenB2,
    Header_Filesystem_Upload_Data,

    Header_Filesystem_Delete_Filename,
    Header_Filesystem_Delete_Recursive_Filename,

    Header_Filesystem_Mkdir_Path,
    Header_Filesystem_Mkdirs_Path,

    Header_Filesystem_List_Path,

    Header_Filesystem_Cat_Path,
    Header_Filesystem_Cat_Next_Byte,

    Header_Realtime,
    Data_Realtime,
    
};

extern App* currentApp;

class Vonalzo {
    public:
        static Vonalzo& instance() {
            static Vonalzo instance;
            return instance;
        }
        Vonalzo() {};
        // 
        void setup();
        void loop();
        bool HandleSerial();
        void HandleButtons();
        
    private:
        SerialHeader serialHeader = SerialHeader::Header_Default;
        uint8_t lastButtonState = 0;
        
        
};

void setLED(int v);
void renderButtonsHorizontal(Adafruit_SSD1306 &display, const char* a, const char* b, const char* c, const char* d, bool renderEmpty);
void renderButtonsVertical(Adafruit_SSD1306 &display, const char* a, const char* b, const char* c, const char* d, bool renderEmpty);
void centerText(Adafruit_SSD1306& display, String s, int16_t x0, int16_t x1, int16_t y);

bool listDir(String path, char fbuf[32][64], char dlist[32]);

bool mkdirs(const String path);

bool showYesNo(Adafruit_SSD1306& display, String s);

bool recursiveDelete(String path);

enum SerialError {
    FS_NOT_FOUND = 255,
    FS_FAILED = 254,
    FS_NOT_EMPTY = 253,
    FS_SUCCESS = 0,
};