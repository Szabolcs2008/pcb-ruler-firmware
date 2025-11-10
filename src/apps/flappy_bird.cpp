#include "flappy_bird.h"
#include "vonalzo.h"

void FlappyBird::reset() {
    this->nextFrame = 0;
    this->exit = false;
    this->firstTick = true;
    this->velocity = 0.5f;
    this->score = 0;
    this->birdY = 14;
    
    this->lost = false;

    this->pipes.clear();
    while (this->newPipe());
}

bool FlappyBird::loop() {
    
    unsigned long now = millis();
    if (now > this->nextFrame) {
        this->nextFrame = now + BIRD_FRAME_TIME;

        if (!lost && !paused) this->tick();
        this->render();
    }
    delay(1);
    return this->exit;
}

void FlappyBird::tick() {
    this->birdY = min(int8_t(birdY + velocity), (int8_t)BIRD_FLOOR);
    this->velocity = min(this->velocity + BIRD_GRAVITY, BIRD_MAX_VELOCITY);

    if (birdY == BIRD_FLOOR) {
        this->lost = true;
        if (this->score > this->highScore) this->highScore = this->score;
        return;
    }

    Pipe& first_pipe = this->pipes.front();
    if (first_pipe.x == 12) {
        for (int8_t y = 0; y < BIRD_FLOOR-BIRD_CEIL; y++) {
            int8_t abs_y = y+BIRD_CEIL;
            if (abs_y == birdY && first_pipe.y_points[y]) {
                if (this->score > this->highScore) this->highScore = this->score;
                this->lost = true;
                return;
            }
        }
    }

    bool removeLast = false;
    for (Pipe& pipe : this->pipes) {
        pipe.x--;
        if (pipe.x  < 12) removeLast = true;
    }

    if (removeLast) {
        this->pipes.pop_front();
        newPipe();
        this->score++;
        
    }

    
}

void FlappyBird::render() {
    display.clearDisplay();
    
    display.fillCircle(BIRD_BIRDX, this->birdY, 1, WHITE);

    if (!lost) {
        for (const Pipe& pipe : this->pipes) {
            for (int8_t i = 0; i <= BIRD_FLOOR - BIRD_CEIL; i++) {
                if (pipe.y_points[i]) {
                    int world_y = i + BIRD_CEIL;
                    display.drawPixel(pipe.x, world_y, WHITE);
                    display.drawPixel(pipe.x+1, world_y, WHITE);
                }
            }
        }
        centerText(display, String(score), 0, 92, 8);
    } else {
        centerText(display, "Score: "+String(score), 12, 92, 13);
        centerText(display, "Best: "+String(highScore), 12, 92, 20);
    }

    display.drawFastHLine(0, BIRD_FLOOR, 128, WHITE);
    display.drawFastHLine(0, BIRD_CEIL, 128, WHITE);
    display.drawFastVLine(93, BIRD_CEIL, BIRD_FLOOR, WHITE);

    if (this->lost) {
        renderButtonsVertical(display, "Rst", "", "", "Ext", true);
    } else {
        if (this->paused) {
            renderButtonsVertical(display, "", "", "Res", "Ext", true);
        } else {
            renderButtonsVertical(display, "Jmp", "", "Pse", "Ext", true);
        }
    }
    display.display();
}

void FlappyBird::handleButtons(uint8_t buttons) {
    if (this->firstTick) {
        this->lastButtonState = buttons;
        this->firstTick = false;
        return;
    }

    if (this->lastButtonState != buttons) {
        if (buttons == bit(3) && !this->lastButtonState) {
            this->exit = true;
        } else if (buttons == bit(0) && !this->lastButtonState) {
            if (this->lost) {
                this->reset();
            } else if (!this->paused) {
                this->velocity = 0.5f;
                this->birdY = max(this->birdY - 4, BIRD_CEIL);
            }
        } else if (buttons == bit(2) && !this->lastButtonState && !this->lost) {
            this->paused = !this->paused;
        }
        this->lastButtonState = buttons;
    }
}

bool FlappyBird::newPipe() {
    Pipe last_pipe;
    last_pipe.x = 12;
    if (!this->pipes.empty()) {
        last_pipe.x = this->pipes.back().x;
    }

    Pipe new_pipe;
    new_pipe = {};
    new_pipe.x = last_pipe.x + 10;

    if (new_pipe.x > 90) return false;

    int gap_start = random(2, (BIRD_FLOOR-BIRD_CEIL)-BIRD_GAP-1);

    for (int i = 0; i < gap_start; i++) {
        new_pipe.y_points[i] = true;
    }
    
    for (int i = gap_start+BIRD_GAP; i < BIRD_FLOOR-BIRD_CEIL; i++) {
        new_pipe.y_points[i] = true;
    }

    this->pipes.push_back(new_pipe);

    return true;
}