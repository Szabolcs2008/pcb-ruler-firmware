#include "baseApplication.h"

#define DIR_MAX_FILE_COUNT 32
#define MAX_FILENAME_LENGTH 64

class FilesApp : public App {
    public:
        static FilesApp* instance() {
            static FilesApp instance;
            return &instance;
        }
        bool loop();
        void reset();
        void handleButtons(uint8_t buttons);
};