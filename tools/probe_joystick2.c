/* Joystick-only probe (no video init) with live event printing.
 * Usage: probe_joystick2 [poll-ms]
 * Prints which joystick/button/hat/axis index each physical pad key is, so the
 * butterscotch fallback mapping can be verified against the real numbering.
 */
#include <SDL/SDL.h>
#include <stdio.h>
#include <stdlib.h>

#define MAXJ 4

int main(int argc, char** argv) {
    if (SDL_Init(SDL_INIT_JOYSTICK | SDL_INIT_TIMER) != 0) {
        printf("SDL_Init failed: %s\n", SDL_GetError());
        return 1;
    }
    int n = SDL_NumJoysticks();
    printf("joysticks=%d\n", n);
    SDL_Joystick* jo[MAXJ] = {0};
    for (int i = 0; i < n && i < MAXJ; i++) {
        jo[i] = SDL_JoystickOpen(i);
        if (!jo[i]) { printf("open %d failed: %s\n", i, SDL_GetError()); continue; }
        printf("joy[%d] '%s' buttons=%d axes=%d hats=%d balls=%d\n", i,
            SDL_JoystickName(i) ? SDL_JoystickName(i) : "(null)",
            SDL_JoystickNumButtons(jo[i]), SDL_JoystickNumAxes(jo[i]),
            SDL_JoystickNumHats(jo[i]), SDL_JoystickNumBalls(jo[i]));
    }
    if (n == 0) { SDL_Quit(); return 0; }

    int nb[MAXJ] = {0}, na[MAXJ] = {0}, nh[MAXJ] = {0};
    Uint8* prev[MAXJ] = {0};
    int* axprev[MAXJ] = {0};
    Uint8* hatprev[MAXJ] = {0};
    for (int i = 0; i < n && i < MAXJ; i++) {
        nb[i] = SDL_JoystickNumButtons(jo[i]);
        na[i] = SDL_JoystickNumAxes(jo[i]);
        nh[i] = SDL_JoystickNumHats(jo[i]);
        prev[i] = calloc(nb[i] > 0 ? nb[i] : 1, 1);
        axprev[i] = calloc(na[i] > 0 ? na[i] : 1, sizeof(int));
        hatprev[i] = calloc(nh[i] > 0 ? nh[i] : 1, 1);
    }

    int ms = argc > 1 ? atoi(argv[1]) : 8000;
    printf("polling %d ms - press keys to see their indices\n", ms);
    Uint32 end = SDL_GetTicks() + ms;
    while (SDL_GetTicks() < end) {
        SDL_Delay(10);
        SDL_JoystickUpdate();
        for (int i = 0; i < n && i < MAXJ; i++) {
            if (!jo[i]) continue;
            for (int b = 0; b < nb[i]; b++) {
                Uint8 now = SDL_JoystickGetButton(jo[i], b);
                if (now != prev[i][b]) {
                    printf("BUTTON index=%d %s\n", b, now ? "DOWN" : "up");
                    fflush(stdout); prev[i][b] = now;
                }
            }
            for (int h = 0; h < nh[i]; h++) {
                Uint8 now = SDL_JoystickGetHat(jo[i], h);
                if (now != hatprev[i][h]) {
                    printf("HAT     index=%d mask=0x%x\n", h, now);
                    fflush(stdout); hatprev[i][h] = now;
                }
            }
            for (int a = 0; a < na[i]; a++) {
                int now = SDL_JoystickGetAxis(jo[i], a);
                if (abs(now - axprev[i][a]) > 2000) {
                    printf("AXIS    index=%d value=%d\n", a, now);
                    fflush(stdout); axprev[i][a] = now;
                }
            }
        }
    }
    for (int i = 0; i < MAXJ; i++) {
        free(prev[i]); free(axprev[i]); free(hatprev[i]);
        if (jo[i]) SDL_JoystickClose(jo[i]);
    }
    SDL_Quit();
    printf("done\n");
    return 0;
}
