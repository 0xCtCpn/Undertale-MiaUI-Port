// SDL1.2 probe for MiaUI glibc (mirrors Garlic probe).
#include <stdio.h>
#include <SDL/SDL.h>
int main(int argc, char** argv) {
    (void)argc; (void)argv;
    if (SDL_Init(SDL_INIT_JOYSTICK|SDL_INIT_VIDEO|SDL_INIT_TIMER) != 0) {
        printf("probe: SDL_Init failed: %s\n", SDL_GetError());
        return 1;
    }
    char vbuf[64];
    const char* vd = SDL_VideoDriverName(vbuf, sizeof(vbuf));
    printf("probe: video driver = %s\n", vd ? vd : "(null)");
    int n = SDL_NumJoysticks();
    printf("probe: joysticks = %d\n", n);
    for (int i = 0; i < n; i++) {
        SDL_Joystick* joy = SDL_JoystickOpen(i);
        if (!joy) { printf("probe[%d] open failed %s\n", i, SDL_GetError()); continue; }
        printf("probe[%d]: '%s' buttons=%d axes=%d hats=%d balls=%d index=%d\n",
            i, SDL_JoystickName(i) ? SDL_JoystickName(i) : "(null)",
            SDL_JoystickNumButtons(joy), SDL_JoystickNumAxes(joy),
            SDL_JoystickNumHats(joy), SDL_JoystickNumBalls(joy), SDL_JoystickIndex(joy));
        SDL_JoystickOpen(joy);
    }
    SDL_Quit();
    printf("probe: done\n");
    return 0;
}
