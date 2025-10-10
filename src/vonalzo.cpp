#include "vonalzo.h"
#include "apps/builtin_textReader.h"
#include "apps/builtin_systemStats.h"
#include "apps/builtin_Files.h"
#include <sys/stat.h>


// App menu things
const char* MenuOptions[] = {
    /* Apps */
    "Files", 
    
    /* System functions */
    "Sleep", "Reboot", "Power off (deep sleep)", "System Info"
};

const int DynamicApps = 1;
const int menuOptionNumber = DynamicApps+4;
int menuIndex = 0;
int menuRenderIndex = 0;

esp_adc_cal_characteristics_t adcCharacteristics;

App* currentApp = nullptr;
Adafruit_SSD1306 display(128, 32, &Wire, -1);
String filePath;

char dirList[32][64];
char isdir[32];

uint8_t pollButtons() {
  uint8_t buttons = 
    !digitalRead(BUTTON_A) 
  | !digitalRead(BUTTON_B) << 1 
  | !digitalRead(BUTTON_C) << 2
  | !digitalRead(BUTTON_D) << 3;
  return buttons;
}

void doSleep() {
  display.clearDisplay();
  // renderButtons(display, "Wake", "", "", "", false);
  display.display();
  display.display();
  #ifdef DEBUG
  Serial.println("Going to sleep.")
  #endif
  esp_light_sleep_start();
  #ifdef DEBUG
  Serial.println("Woke from sleep.")
  #endif
}

void renderButtonsHorizontal(Adafruit_SSD1306 &display, const char* a, const char* b, const char* c, const char* d, bool renderEmpty) {
  if (strcmp(a, "") || renderEmpty) {
    display.setCursor(0, 30);
    display.print("A:");
    display.print(a);
  }
  if (strcmp(b, "") || renderEmpty) {
    display.setCursor(31, 30);
    display.print("B:");
    display.print(b);
  }
  if (strcmp(c, "") || renderEmpty) {
    display.setCursor(63, 30);
    display.print("C:");
    display.print(c);
  }
  if (strcmp(d, "") || renderEmpty) {
    display.setCursor(95, 30);
    display.print("D:");
    display.print(d);
  }
}

void renderButtonsVertical(Adafruit_SSD1306 &display, const char* a, const char* b, const char* c, const char* d, bool renderEmpty) {
    int y = 5;
    if (strcmp(a, "") || renderEmpty) {
    display.setCursor(95, y+5);
    display.print("A:");
    display.print(a);
  }
  if (strcmp(b, "") || renderEmpty) {
    display.setCursor(95, y+12);
    display.print("B:");
    display.print(b);
  }
  if (strcmp(c, "") || renderEmpty) {
    display.setCursor(95, y+19);
    display.print("C:");
    display.print(c);
  }
  if (strcmp(d, "") || renderEmpty) {
    display.setCursor(95, y+26);
    display.print("D:");
    display.print(d);
  }
}

void setLED(int v)  {
    if (!v) {
        analogWrite(LED, 255);
    } else {
        analogWrite(LED, 192);
    }
}

void centerText(Adafruit_SSD1306& display, String s, int16_t x0, int16_t x1, int16_t y) {
    int16_t xs, ys;
    uint16_t w, h;

    display.getTextBounds(s, x0, y, &xs, &ys, &w, &h);

    int16_t x = ((x1-x0) - w) / 2;

    display.setCursor(x+x0, y);
    display.print(s);
}

bool recursiveDelete(const String path) {
  File entry = LittleFS.open(path);
  if (!entry) {
    Serial.printf("Failed to open %s\n", path);
    return false;
  }

  if (!entry.isDirectory()) {
    entry.close();
    bool result = LittleFS.remove(path);
    return result;
  }

  File file = entry.openNextFile();
  while (file) {
    String filePath = path + "/" + file.name();
    file.close();
    if (!recursiveDelete(filePath.c_str())) {
    }
    file = entry.openNextFile();
  }

  entry.close();

  bool result = LittleFS.rmdir(path);
  return result;
}

bool listDir(String path, char fbuf[32][64], char dlist[32]) {
    uint8_t fileCount = 0;
    for (int i = 0; i < fileCount; i++) {
        fbuf[i][0] = 0;
        dlist[i] = 0;
    }
    File item = LittleFS.open(path);
    
    if (!item) {return false;}

    File tfile = item.openNextFile();
    while (tfile) {
        strncpy(fbuf[fileCount], tfile.name(), MAX_FILENAME_LENGTH);
        if (tfile.isDirectory()) dlist[fileCount] = 1;
        fbuf[fileCount][MAX_FILENAME_LENGTH-1] = 0;
        fileCount++;
        tfile = item.openNextFile();
    }
    tfile.close();

    return true;
}

void Vonalzo::setup() {
    // this->currentApp = Menu::instance();
    Serial.begin();
    Wire.begin(6, 7);

    if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        Serial.println("Failed to set up screen");
        for(;;);
    }


    if (!LittleFS.begin(true)) {
        Serial.println("LittleFS mount failed!");
        return;
    }
    // Serial.println("LittleFS mounted successfully.");

    pinMode(BUTTON_A, INPUT_PULLUP);
    pinMode(BUTTON_B, INPUT_PULLUP);
    pinMode(BUTTON_C, INPUT_PULLUP);
    pinMode(BUTTON_D, INPUT_PULLUP);
    pinMode(LED, OUTPUT);
    // delay(2000);
    setLED(0);
    display.dim(true);
    display.setFont(&FONT);
    display.setTextColor(WHITE);

    display.clearDisplay();
    display.display();
    display.display();

    esp_sleep_enable_gpio_wakeup();
    esp_deep_sleep_enable_gpio_wakeup(bit(BUTTON_A), ESP_GPIO_WAKEUP_GPIO_LOW);
    gpio_wakeup_enable((gpio_num_t)BUTTON_A, GPIO_INTR_LOW_LEVEL);

    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_config_channel_atten(ADC1_CHANNEL_0, ADC_ATTEN_DB_12);
    esp_adc_cal_characterize(ADC_UNIT_1, ADC_ATTEN_DB_12, ADC_WIDTH_BIT_12, 1100, &adcCharacteristics);
    
    this->lastButtonState = pollButtons();
    filePath.reserve(512);
}

bool Vonalzo::HandleSerial() {
    static unsigned long byteCount;
    static File file;

    if (Serial.available()) {
        uint8_t next = Serial.peek();
        switch (this->serialHeader) {
            case SerialHeader::Header_Default:
                // if (next == 'T') serialHeader = SerialHeader::Header_Text_Bytecount0;
                if (next == 'F') serialHeader = SerialHeader::Header_Filesystem_Command;
                else serialHeader = SerialHeader::Header_Default;
                break;
            case SerialHeader::Header_Filesystem_Command:
                filePath.clear();
                if      (next == 'w') serialHeader = SerialHeader::Header_Filesystem_Upload_Filename; /* Upload file */
                else if (next == 'd') serialHeader = SerialHeader::Header_Filesystem_Delete_Filename; /* Delete a file or directory */
                else if (next == 'D') serialHeader = SerialHeader::Header_Default; /* Delete a file or directory RECURSIVELY */
                else if (next == 'm') serialHeader = SerialHeader::Header_Filesystem_Mkdir_Path;
                else if (next == 'l') serialHeader = SerialHeader::Header_Filesystem_Mkdir_Path;
                
                break;
            
            /* Upload command */

            case SerialHeader::Header_Filesystem_Upload_Filename:
                if (next != 0) {
                    Serial.write(next);
                    Serial.flush();
                    filePath += char(next);
                } else {
                    serialHeader = SerialHeader::Header_Filesystem_Upload_DatalenB0;
                    String parentDir = filePath.substring(0, filePath.lastIndexOf('/'));
                    if (parentDir.length() == 0) parentDir = "/";
                    file = LittleFS.open(filePath.c_str(), "w", false);
                    if (file) {
                        Serial.write(FS_SUCCESS);
                        
                    } else {
                        Serial.write(FS_FAILED);
                    }
                    Serial.flush();
                }
                break;
            case SerialHeader::Header_Filesystem_Upload_DatalenB0:
                byteCount = 0;
                byteCount |= next << 16;
                serialHeader = SerialHeader::Header_Filesystem_Upload_DatalenB1;
                break;
            case SerialHeader::Header_Filesystem_Upload_DatalenB1:
                byteCount |= next << 8;
                serialHeader = SerialHeader::Header_Filesystem_Upload_DatalenB2;
                break;
            case SerialHeader::Header_Filesystem_Upload_DatalenB2:
                byteCount |= next;
                serialHeader = SerialHeader::Header_Filesystem_Upload_Data;
                display.clearDisplay();
                display.setCursor(1, 5);
                display.setTextColor(WHITE);
                display.println("Downloading file...");
                display.display();
                // setLED(0);
                break;
            case SerialHeader::Header_Filesystem_Upload_Data:
                file.write(next);
                
                Serial.write(next);
                if (--byteCount == 0) {
                    setLED(0);
                    file.close();
                    serialHeader = SerialHeader::Header_Default;
                    delay(500);
                    Serial.write(0);
                    Serial.flush();
                }
                break;
            
            /* Delete command */
            case SerialHeader::Header_Filesystem_Delete_Filename:
                if (next != 0) {
                    Serial.write(next);
                    Serial.flush();
                    filePath += char(next);
                } else {
                    file = LittleFS.open(filePath);
                    if (file) {
                        if (file.isDirectory()) {
                            file.close();
                            if (!LittleFS.rmdir(filePath)) {
                                Serial.write(FS_NOT_EMPTY);
                            } else {
                                Serial.write(FS_SUCCESS);
                            }
                        } else {
                            file.close();
                            if (LittleFS.remove(filePath)) {
                                Serial.write(FS_SUCCESS);
                            } else {
                                Serial.write(FS_FAILED);
                            }
                        }
                    } else {
                        Serial.write(FS_FAILED);
                    }
                    Serial.flush();
                    serialHeader = SerialHeader::Header_Default;
                }
                break;
            
            /* Create directory */
            case SerialHeader::Header_Filesystem_Mkdir_Path:
                if (next != 0) {
                    Serial.write(next);
                    Serial.flush();
                    filePath += char(next);
                } else {
                    if (LittleFS.mkdir(filePath)) {
                        Serial.write(FS_SUCCESS);
                    } else {
                        Serial.write(FS_FAILED);
                    }
                    Serial.flush();
                }
                break;
            
            case SerialHeader::Header_Filesystem_List_Path:
                if (next != 0) {
                    Serial.write(next);
                    Serial.flush();
                    filePath += char(next);
                } else {
                    listDir(filePath, dirList, isdir);
                    Serial.write(isdir, 32);
                    uint8_t i = 0;
                    while (i < 32) {
                        for (uint8_t j = 0; dirList[i][j]; j++) {
                            Serial.write(dirList[i][j]);
                        }
                        Serial.write(0);
                        Serial.flush();
                        i++;
                    }
                    Serial.write(255);
                    Serial.flush();
                }
        }
        Serial.read(); // Discard byte
    }
    return serialHeader == SerialHeader::Header_Filesystem_Upload_Data;
}

void Vonalzo::HandleButtons() {
    // static uint8_t lastButtonState = 0;
    static uint32_t lastPoll = 0;
    uint32_t now = millis();
    if (now - lastPoll < 10) {
        return;
    }
    uint8_t buttons = pollButtons();

    if (this->lastButtonState != buttons) {
        if (buttons == bit(0) && !this->lastButtonState) {
            if (menuIndex == 0) {
                menuIndex = menuOptionNumber-1;
                menuRenderIndex = menuOptionNumber-2;
            } else {
                menuIndex = max((menuIndex - 1), 0);
                if (menuIndex < (menuRenderIndex)) {
                    menuRenderIndex--;
                }
            }
            
        } else if (buttons == bit(1) && !this->lastButtonState) {
            if (menuIndex == menuOptionNumber-1) {
                menuIndex = 0;
                menuRenderIndex = 0;
            } else {
                menuIndex = min((menuIndex + 1), menuOptionNumber-1);
                if (menuIndex > (menuRenderIndex + 1)) {
                    menuRenderIndex++;
                }
            }
            
        } else if (buttons == bit(3) && !this->lastButtonState) {
            switch (menuIndex) {
                // case 0: currentApp = TextReader::instance(); currentApp->reset(); break;
                case 0: currentApp = FilesApp::instance(); currentApp->reset(); break;

                /* Hardcoded system functions */
                
                case (DynamicApps+0): doSleep(); break;
                case (DynamicApps+1): ESP.restart(); break;
                case (DynamicApps+2): display.clearDisplay(); display.display();esp_deep_sleep_start();
                case (DynamicApps+3): currentApp = SysStats::instance(); currentApp->reset(); break;
            }
        }
        this->lastButtonState = buttons;
    }
}


void Vonalzo::loop() {
    setLED(0);
    if (this->HandleSerial()) {
        delayMicroseconds(500);
        return;
    }

    if (currentApp == nullptr) {  // means no app is running 
        setLED(1);
        this->HandleButtons();

        /* Render home screen */

        display.clearDisplay();
        display.setCursor(1, 5);
        display.fillRect(0, 0, 128, 8, WHITE);
        display.setTextColor(BLACK);
        display.print("Vonalzo ");
        display.print(VERION_STRING);
        
        display.setTextColor(WHITE);

        display.setCursor(0, 14);
        for (int i = menuRenderIndex; i < menuRenderIndex + 2; i++) {
            if (i < menuOptionNumber) {
                if (i == menuIndex) display.print("> ");
                else                display.print("  ");
                display.print(MenuOptions[i]);
                if (i == menuIndex) display.println(" <");
                else                display.println();
            }
        }
        // display.println("  abcdefghijklmnopqrstovwxyz");
        // display.println("  abcdefghijklmnopqrstovwxyz");

        
        display.drawFastHLine(0, 24, 128, WHITE);
        renderButtonsHorizontal(display, "Up", "Down", "...", "OK", true);
        display.display();
        return;
    }
    
    currentApp->handleButtons(pollButtons());
    if (currentApp->loop()) currentApp = nullptr;
}

bool showYesNo(Adafruit_SSD1306& display, String s) {
    return false;
}