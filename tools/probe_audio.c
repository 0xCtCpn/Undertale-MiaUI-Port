// SDL1.2 audio probe for MiaUI (ALSA via SDL audio) + joystick poll.
#include <stdio.h>
#include <SDL/SDL.h>

static void audio_cb(void* userdata, Uint8* stream, int len) {
    (void)userdata;
    for (int i = 0; i < len; i++) stream[i] = 128;
}

int main(int argc, char** argv) {
    (void)argc; (void)argv;
    if (SDL_Init(SDL_INIT_AUDIO | SDL_INIT_JOYSTICK | SDL_INIT_VIDEO | SDL_INIT_TIMER) != 0) {
        printf("probe: SDL_Init failed: %s\n", SDL_GetError());
        return 1;
    }
    char vbuf[64];
    const char* vd = SDL_VideoDriverName(vbuf, sizeof(vbuf));
    printf("probe: video=%s\n", vd ? vd : "(null)");
    int n = SDL_NumJoysticks();
    printf("joy %d\n", n);
    for (int i = 0; i < n; i++) {
        SDL_Joystick* joy = SDL_JoystickOpen(i);
        if (!joy) { printf("joy %d open failed %s\n", i, SDL_GetError()); continue; }
        printf("joy %d '%s' buttons=%d axes=%d hats=%d balls=%d index=%d\n", i,
            SDL_JoystickName(i) ? SDL_JoystickName(i) : "(null)",
            SDL_JoystickNumButtons(joy), SDL_JoystickNumAxes(joy),
            SDL_JoystickNumHats(joy), SDL_JoystickNumBalls(joy), SDL_JoystickIndex(joy));
        SDL_JoystickClose(joy);
    }
    printf("audio test (2s)\n");
    SDL_AudioSpec want;
    want.freq = 44100;
    want.format = AUDIO_S16SYS;
    want.channels = 2;
    want.samples = 1024;
    want.callback = audio_cb;
    want.userdata = NULL;
    SDL_AudioSpec got;
    if (SDL_OpenAudio(&want, &got) < 0) {
        printf("audio open failed: %s\n", SDL_GetError());
    } else {
        SDL_PauseAudio(0);
        SDL_Delay(2000);
        SDL_CloseAudio();
        printf("audio ok freq=%d ch=%d\n", got.freq, got.channels);
    }
    SDL_Quit();
    printf("done\n");
    return 0;
}
