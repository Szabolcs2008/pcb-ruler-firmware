#include "baseApplication.h"
#include "../vonalzo.h"
#include "driver/adc.h"

#define VOLTAGE_HISTORY_BUFFER_SIZE 256

class SysStats : public App {
    public:
        static SysStats* instance() {
            static SysStats instance;
            return &instance;
        }
        bool loop();
        void reset();
        void handleButtons(uint8_t buttons);
};