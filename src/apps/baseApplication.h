#pragma once

#include <Arduino.h>

class App {
    public:
        virtual bool loop() {return true;}            // Returns true if application exited
        virtual void handleButtons(uint8_t buttons) {};
        virtual void reset() {};
};