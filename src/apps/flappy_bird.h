#pragma once

#include "baseApplication.h"
#include <Arduino.h>
#include <deque>

#define BIRD_GRAVITY 0.25f
#define BIRD_MAX_VELOCITY 3.0f

#define BIRD_GAP 10
#define BIRD_FLOOR 30
#define BIRD_CEIL 1
#define BIRD_BIRDX 12

#define BIRD_FRAME_TIME 100



typedef struct {
    uint8_t x;
    bool y_points[32-BIRD_CEIL-(31-BIRD_FLOOR)];
} Pipe;

class FlappyBird : public App {
    public:
        static FlappyBird* instance() {
            static FlappyBird instance;
            return &instance;
        }
        bool loop();
        void reset();
        void handleButtons(uint8_t buttons);
        
        void render();
        void tick();

    private:
        bool exit = false;
        unsigned long nextFrame = 0;
        std::deque<Pipe> pipes;
        bool firstTick = false;
        uint8_t lastButtonState;
        int8_t birdY = 14;
        float velocity = 1.0f;
        int score = 0;
        int highScore = 0;
        bool lost = false;
        bool paused = false;
        bool newPipe();
        
};