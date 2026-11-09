/* Audio-only probe (no video init) for running over adb shell.
 * Usage: probe_audio2 [alsa-device-name]  (sets AUDIODEV for the SDL part)
 */
#include <alsa/asoundlib.h>
#include <SDL/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void cb(void* u, Uint8* s, int l){ (void)u; for(int i=0;i<l;i++) s[i]=(Uint8)(i*37+90); }

static void try_alsa(const char* name) {
    snd_pcm_t* pcm = NULL;
    int err = snd_pcm_open(&pcm, name, SND_PCM_STREAM_PLAYBACK, SND_PCM_NONBLOCK);
    printf("open %-12s -> %d", name, err);
    if (err < 0) { printf("  (%s)\n", snd_strerror(err)); return; }
    snd_pcm_hw_params_t* hw; snd_pcm_hw_params_alloca(&hw);
    snd_pcm_hw_params_any(pcm, hw);
    int e1 = snd_pcm_hw_params_set_access(pcm, hw, SND_PCM_ACCESS_RW_INTERLEAVED);
    int e2 = snd_pcm_hw_params_set_format(pcm, hw, SND_PCM_FORMAT_S16_LE);
    unsigned r = 44100; int dir = 0;
    int e3 = snd_pcm_hw_params_set_rate_near(pcm, hw, &r, &dir);
    int e4 = snd_pcm_hw_params_set_channels(pcm, hw, 2);
    int e5 = snd_pcm_hw_params(pcm, hw);
    printf(" access=%d fmt=%d rate=%u(%d) ch=%d hwparams=%d", e1, e2, r, e3, e4, e5);
    if (e5 < 0) printf(" (%s)", snd_strerror(e5));
    else { int e6 = snd_pcm_prepare(pcm); printf(" prepare=%d", e6); }
    printf("\n");
    snd_pcm_close(pcm);
}

int main(int argc, char** argv) {
    if (argc > 1) setenv("AUDIODEV", argv[1], 1);
    printf("ALSA library version: %s\n", snd_asoundlib_version());
    const char* names[] = {"default", "plughw:0,0", "hw:0,0", "surround40", "surround51", NULL};
    for (int i = 0; names[i]; i++) try_alsa(names[i]);
    printf("== SDL (AUDIODEV=%s) ==\n", getenv("AUDIODEV") ? getenv("AUDIODEV") : "unset");
    if (SDL_Init(SDL_INIT_AUDIO | SDL_INIT_TIMER) != 0) {
        printf("SDL_Init: %s\n", SDL_GetError());
        return 1;
    }
    SDL_AudioSpec want, got; memset(&want, 0, sizeof want);
    want.freq = 44100; want.format = AUDIO_S16SYS; want.channels = 2;
    want.samples = 1024; want.callback = cb;
    if (SDL_OpenAudio(&want, &got) < 0) {
        printf("SDL_OpenAudio: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }
    SDL_PauseAudio(0);
    printf("playing tone 1s: got freq=%d ch=%d samples=%d\n", got.freq, got.channels, got.samples);
    SDL_Delay(1000);
    SDL_CloseAudio();
    SDL_Quit();
    printf("done\n");
    return 0;
}
