#include "baseApplication.h"
#include "../vonalzo.h"

class TextReader : public App {
    public:
        static TextReader* instance() {
            static TextReader instance;
            return &instance;
        }
        bool loop();
        void reset();
        void handleButtons(uint8_t buttons);
    private:
        bool exit = false;
        bool justStarted = false;
        uint8_t lastButtonState = 0;
        int textRow = 0;
};