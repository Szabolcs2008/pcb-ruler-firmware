#include "baseApplication.h"
#include "../vonalzo.h"

bool exited = false;

class TestApp : public App {
    public:
        static TestApp* instance() {
            static TestApp instance;
            return &instance;
        }
        bool loop() {
            display.clearDisplay(); 
            renderButtonsHorizontal(display, "Exit", "", "", "", false);
            display.display(); 
            return exited;
        }

        void reset() {
            exited = false;
        }

        void handleButtons(uint8_t buttons) {
            if (buttons == bit(0)) {exited = true;}
        }
};