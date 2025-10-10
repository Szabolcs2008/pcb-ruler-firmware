#include <Arduino.h>
#include <LittleFS.h>
#include "builtin_Files.h"
#include "../vonalzo.h"
#include <vector>

String path = "/";

char directoryListing[DIR_MAX_FILE_COUNT][MAX_FILENAME_LENGTH];
bool isDir[DIR_MAX_FILE_COUNT];
uint8_t fileCount = 0;
uint8_t fileIndex = 0;
uint8_t fileRenderIndex = 0;


bool files_justStarted = true;
bool files_exit = false;
bool files_optionMenu = false;
uint8_t files_optionMenuIndex = 0;

bool files_reader = false;
bool files_readerLineIndex = 0;
int files_textRow = 0;
File files_openedFile;
std::vector<int> files_lineOffsets; 

void clearList() {
    for (int i = 0; i < fileCount; i++) {
        directoryListing[i][0] = 0;
        isDir[i] = false;
    }
    fileCount = 0;
}

void flistDir(String& _path) {
    clearList();
    strcpy(directoryListing[0], "..");
    fileCount++;
    File item = LittleFS.open(_path);
    File tfile = item.openNextFile();
    while (tfile) {
        strncpy(directoryListing[fileCount], tfile.name(), MAX_FILENAME_LENGTH);
        if (tfile.isDirectory()) isDir[fileCount] = true;
        directoryListing[fileCount][MAX_FILENAME_LENGTH-1] = 0;
        fileCount++;
        tfile = item.openNextFile();
    }
    tfile.close();
}

void FilesApp::reset() {
    files_exit = false;
    files_optionMenu = false;
    files_optionMenuIndex = 0;
    path.reserve(512);
    path = "/";
    flistDir(path);
}

void loadFile() {
    files_openedFile.seek(0);
    files_lineOffsets.clear();
    while (files_openedFile.available()) {
        int pos = files_openedFile.position();
        files_lineOffsets.push_back(pos);
        
        while (files_openedFile.available()) {
            if (files_openedFile.read() == '\n') break;
        }
    }
}

void FilesApp::handleButtons(uint8_t buttons) {
    static uint8_t lastButtonState = 0;
    if (files_justStarted) {lastButtonState = buttons; files_justStarted = false; return;} 
    if (buttons != lastButtonState) {
        if (files_optionMenu) { /* Menu behavior */

            if (buttons == bit(3) && !lastButtonState) {
                if (files_optionMenuIndex == 0) {
                    files_optionMenu = false;
                    files_optionMenuIndex = 0;
                } else if (files_optionMenuIndex == 1) { /* DELETE */
                    if (fileIndex != 0) { /* Check if selected file is not .. */
                        String filePath = path + (path == "/" ? "" : "/") + directoryListing[fileIndex];
                        File rfile = LittleFS.open(filePath);
                        if (rfile.isDirectory()) {
                            rfile.close();
                            if (!LittleFS.rmdir(filePath)) {
                                recursiveDelete(filePath);
                                // display.clearDisplay();
                                // display.setCursor(0, 6);
                                // display.println("Deletion failed.");
                                // display.display();
                                // delay(1000);
                            }
                        } else {
                            rfile.close();
                            if (!LittleFS.remove(filePath)) {
                                display.clearDisplay();
                                display.setCursor(0, 6);
                                display.println("Deletion failed.");
                                display.display();
                                delay(1000);
                            }
                        }
                        clearList();
                        flistDir(path);
                        files_optionMenu = false;
                        fileIndex = 0;
                        fileRenderIndex = 0;
                    }
                } else if (files_optionMenuIndex == 2) { /* EXIT */
                    files_exit = true;
                }
            } else if (buttons == bit(0) && !lastButtonState) {
                /* Menu: Up */
                files_optionMenuIndex--;
                if (files_optionMenuIndex == 255) {
                    files_optionMenuIndex = 3;
                }
            } else if (buttons == bit(1) && !lastButtonState) {
                files_optionMenuIndex = (files_optionMenuIndex + 1) % 4;
            }
        
        } else if (files_reader) {  /* Reader mode */
            if (buttons == bit(3) && !lastButtonState) {
                files_reader = false;
                files_openedFile.close();
                files_textRow = 0;
            } else if (buttons == bit(0) && !lastButtonState) {
                files_textRow = std::max(files_textRow-1, 0);
            } else if (buttons == bit(1) && !lastButtonState) {
                files_textRow = std::min((unsigned int)files_textRow+1, files_lineOffsets.size()-1);
            }
        } else { /* Normal mode */
            if (buttons == bit(2) && !lastButtonState) { /* Open options */
            files_optionMenu = true;
            files_optionMenuIndex = 0;
            } else if (buttons == bit(3) && !lastButtonState) { /* OK */
                if (fileIndex == 0) {
                    path = path.substring(0, path.lastIndexOf("/"));
                    if (path.length() == 0) path = "/";
                    clearList();
                    flistDir(path);
                    fileIndex = 0;
                    fileRenderIndex = 0;
                } else {
                    String filePath = path + (path == "/" ? "" : "/") + directoryListing[fileIndex];
                    File file = LittleFS.open(filePath);
                    if (file.isDirectory()) {
                        path = filePath;
                        clearList();
                        flistDir(path);
                        fileIndex = 0;
                        fileRenderIndex = 0;
                    } else { /* It is a file */
                        files_reader = true;
                        files_openedFile = LittleFS.open(filePath);
                        files_textRow = 0;
                        loadFile();
                    }
                    file.close();
                }
            } else if (buttons == bit(0) && !lastButtonState) {
                /* Normal behaviour */
                fileIndex--;
                if (fileIndex == 255) {
                    fileIndex = fileCount-1;
                    fileRenderIndex = std::max(fileCount-2, 0);
                }
                if (fileIndex < fileRenderIndex) {
                    fileRenderIndex--;
                }
                
            } else if (buttons == bit(1) && !lastButtonState) {
                /* Normal behaviour */
                if (fileIndex == fileCount-1) {
                    fileIndex = 0;
                    fileRenderIndex = 0;
                } else {
                        fileIndex = (fileIndex + 1) % fileCount;
                    if (fileIndex > fileRenderIndex + 1) {
                        fileRenderIndex++;
                    }
                }
            }
            
        }
        lastButtonState = buttons;
    }
}

String readLine(File& file) {
    String s;
    s.reserve(64);
    char c;
    while (file.available()) {
        c = file.read();
        if (c == '\n') {
            break;
        } else {
            s += c;
        }
    }
    return s;
}

void printMenuOption(String s, uint8_t idx, uint8_t line) {
    if (files_optionMenuIndex == idx) {
        centerText(display, "> "+s+" <", 31, 95, FONT.yAdvance*(line+1));
    } else {
        centerText(display, s, 31, 95, FONT.yAdvance*(line+1));
    }
}

bool FilesApp::loop() {
    display.clearDisplay();

    if (files_reader) {
        display.setTextColor(WHITE);
        display.setCursor(0, 5);

        files_openedFile.seek(files_lineOffsets.at(std::min(files_textRow, (int)files_lineOffsets.size()-1)));

        for (uint8_t i = 0; i < 3; i++) {
            if (files_openedFile.available()) {
                String s = readLine(files_openedFile);
                display.setTextColor(WHITE);
                display.println(s);
            } else {
                display.println("--- EOF ---");
                break;
            }
        }

        display.drawFastHLine(0, 24, 128, WHITE);
        renderButtonsHorizontal(display, "Up", "Down", "", "Exit", false);
    
    
    } else {
        display.setCursor(0, 6);
        display.println(path);
        for (uint8_t i = 0; i < 128; i++) {
            if (i % 2 == 0) display.drawPixel(i, 8, WHITE);
        }
        // display.drawFastHLine(0, 8, 128, WHITE);
        display.setCursor(0, 7+FONT.yAdvance);
        for (uint8_t i = fileRenderIndex; i < fileRenderIndex+2; i++) {
            if (i > fileCount) {
                break;
            }
            if (fileIndex == i) {
                display.print("> ");        
            } else {
                display.print("  ");
            }
            if (isDir[i]) {
                display.print(directoryListing[i]);
                display.println("/");
            } else {
                display.println(directoryListing[i]);
            }

            
        }
        // display.println(directoryListing[0]);
        display.drawFastHLine(0, 24, 128, WHITE);
        renderButtonsHorizontal(display, "Up", "Down", "Optn", "OK", false);

        if (files_optionMenu) {
            display.fillRect(31, 0, 64, 32, BLACK);
            display.drawRect(31, 0, 64, 32, WHITE);
            display.setCursor(33, FONT.yAdvance);

            printMenuOption("Back", 0, 0);
            printMenuOption("Delete", 1, 1);
            printMenuOption("Exit", 2, 2);
        }
    }
    

    display.display();

    return files_exit;
}