#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DEFAULT_DELAY_MS 75

static int send_input_event(INPUT *in) {
    return SendInput(1, in, sizeof(INPUT)) == 1;
}

int main(int argc, char **argv) {
    if (argc != 3 && argc != 4) {
        fprintf(stderr, "Usage: send_mousewheel_input.exe up|down count [delay_ms]\n");
        return 2;
    }
    int delta = (_stricmp(argv[1], "up") == 0) ? WHEEL_DELTA :
                (_stricmp(argv[1], "down") == 0) ? -WHEEL_DELTA : 0;
    int count = atoi(argv[2]);
    int delay_ms = (argc == 4) ? atoi(argv[3]) : DEFAULT_DELAY_MS;
    if (delta == 0 || count < 1 || count > 1000 || delay_ms < 0 || delay_ms > 60000) {
        fprintf(stderr, "Direction must be up/down, count 1..1000, delay_ms 0..60000.\n");
        return 2;
    }

    INPUT in;
    ZeroMemory(&in, sizeof(in));
    in.type = INPUT_KEYBOARD;
    in.ki.wVk = VK_CONTROL;
    if (!send_input_event(&in)) return 3;

    for (int i = 0; i < count; ++i) {
        ZeroMemory(&in, sizeof(in));
        in.type = INPUT_MOUSE;
        in.mi.dwFlags = MOUSEEVENTF_WHEEL;
        in.mi.mouseData = (DWORD)delta;
        if (!send_input_event(&in)) return 4;
        if (delay_ms > 0) Sleep((DWORD)delay_ms);
    }

    ZeroMemory(&in, sizeof(in));
    in.type = INPUT_KEYBOARD;
    in.ki.wVk = VK_CONTROL;
    in.ki.dwFlags = KEYEVENTF_KEYUP;
    if (!send_input_event(&in)) return 5;
    return 0;
}

/* Claire Sawyer */