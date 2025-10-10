#include "builtin_textReader.h"
#include "../vonalzo.h"
#include <vector>

File textFile;
std::vector<int> lineOffsets; 

bool TextReader::loop() {
    display.clearDisplay();
    display.setTextColor(WHITE);
    display.setCursor(1, 5);

    textFile.seek(lineOffsets.at(std::min(this->textRow, (int)lineOffsets.size()-1)));

    for (uint8_t i = 0; i < 3; i++) {
        if (textFile.available()) {
            String s = textFile.readStringUntil('\n');
            display.setTextColor(WHITE);
            display.println(s);
        } else {
            display.println("--- EOF ---");
            break;
        }
    }

    display.drawFastHLine(0, 24, 128, WHITE);
    renderButtonsHorizontal(display, "Up", "Down", "", "Exit", false);
    display.display();

    return this->exit;
}

void TextReader::handleButtons(uint8_t buttons) {
    if (this->justStarted) {
        this->lastButtonState = buttons;
        this->justStarted = false;
        return;
    }
    if (this->lastButtonState != buttons) {
        if (buttons == bit(3) && !lastButtonState) {
            this->exit = true;
        } else if (buttons == ( bit(1) | bit(0) )) {
            textRow = 0;
        } else if (buttons == ( bit(1) ) && !lastButtonState) {
            this->textRow = std::min((unsigned int)textRow+1, lineOffsets.size()-1);
        } else if (buttons == ( bit(0) ) && !lastButtonState) {
            textRow = std::max(textRow-1, 0);
        }
        this->lastButtonState = buttons;
    } 
}

void TextReader::reset() {
    this->exit = false;
    this->justStarted = true;
    
    lineOffsets.clear();

    display.clearDisplay();
    display.setTextColor(WHITE);
    display.setCursor(1, 5);
    display.println("Loading text...");
    display.display();
    // display.println("Preprocessing line offsets...");
    textFile = LittleFS.open("/data.txt", "r");
    while (textFile.available()) {
        int pos = textFile.position();
        lineOffsets.push_back(pos);

        textFile.readStringUntil('\n');
    }
}