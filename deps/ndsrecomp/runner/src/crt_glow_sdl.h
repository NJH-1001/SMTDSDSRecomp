#pragma once
#include "crt_glow.h"
#include <cstdio>
#include <cstring>
#if defined(NDS_HAVE_SDL3)
#include <SDL3/SDL.h>
#else
#include <SDL.h>
#endif

struct NdsCrtGlowTexture {
    SDL_Texture* texture=nullptr;
    int width=0,height=0;
    bool disabled=false;
    std::vector<uint32_t> pixels,scratch;
};
inline void nds_crt_glow_destroy(NdsCrtGlowTexture& s) {
    if(s.texture) SDL_DestroyTexture(s.texture);
    s={};
}
inline bool nds_crt_glow_upload(NdsCrtGlowTexture& s,SDL_Renderer* renderer,
                               const uint32_t* source,int width,int height) {
    if(s.disabled) return false;
    const int w=nds_crt_glow_extent(width),h=nds_crt_glow_extent(height);
    if(!s.texture || s.width!=w || s.height!=h) {
        nds_crt_glow_destroy(s);
#if defined(NDS_HAVE_SDL3)
        const char* name=SDL_GetRendererName(renderer);
        const bool accelerated=name && std::strcmp(name,"software")!=0;
#else
        SDL_RendererInfo info{};
        const bool accelerated=SDL_GetRendererInfo(renderer,&info)==0 && (info.flags&SDL_RENDERER_ACCELERATED);
#endif
        if(accelerated) s.texture=SDL_CreateTexture(renderer,SDL_PIXELFORMAT_ARGB8888,SDL_TEXTUREACCESS_STREAMING,w,h);
        bool supported=false;
        if(s.texture) {
#if defined(NDS_HAVE_SDL3)
            supported=SDL_SetTextureScaleMode(s.texture,SDL_SCALEMODE_LINEAR) && SDL_SetTextureBlendMode(s.texture,SDL_BLENDMODE_ADD);
#else
            supported=SDL_SetTextureScaleMode(s.texture,SDL_ScaleModeLinear)==0 && SDL_SetTextureBlendMode(s.texture,SDL_BLENDMODE_ADD)==0;
#endif
        }
        if(!supported) {
            nds_crt_glow_destroy(s);s.disabled=true;
            std::fprintf(stderr,"[sdl] GPU glow unavailable; disabled (no CPU fallback)\n");
            return false;
        }
        s.width=w;s.height=h;
        std::fprintf(stderr,"[sdl] GPU glow: %dx%d additive texture\n",w,h);
    }
    nds_crt_glow_image(source,width,height,s.pixels,s.scratch);
#if defined(NDS_HAVE_SDL3)
    const bool ok=SDL_UpdateTexture(s.texture,nullptr,s.pixels.data(),w*sizeof(uint32_t));
#else
    const bool ok=SDL_UpdateTexture(s.texture,nullptr,s.pixels.data(),w*sizeof(uint32_t))==0;
#endif
    if(!ok) {nds_crt_glow_destroy(s);s.disabled=true;std::fprintf(stderr,"[sdl] GPU glow upload failed; disabled\n");}
    return ok;
}
inline void nds_crt_glow_draw(NdsCrtGlowTexture& s,SDL_Renderer* renderer,
                             const SDL_Rect& rect,int glow) {
    if(!s.texture || s.disabled || glow<=0) return;
    // Independent from mask/scanline strength. Full scale is deliberately
    // visible; users can dial down to a subtler phosphor halo.
    SDL_SetTextureAlphaMod(s.texture,uint8_t(std::clamp(glow,0,100)*192/100));
#if defined(NDS_HAVE_SDL3)
    const SDL_FRect r{float(rect.x),float(rect.y),float(rect.w),float(rect.h)};
    SDL_RenderTexture(renderer,s.texture,nullptr,&r);
#else
    SDL_RenderCopy(renderer,s.texture,nullptr,&rect);
#endif
}
