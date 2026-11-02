#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>

enum class NdsScreenLayout : uint8_t { Stacked, Separate, SideBySide, TopOnly, BottomOnly };
struct NdsDisplayStyle {
    int gap = 0;
    int border = 0;
    uint32_t border_color = 0x303848;
    uint32_t background_color = 0x141414;
    bool swap = false;
    bool integer_scale = true;
    int lcd = 0;              // off, scanlines, pixel grid
    int lcd_strength = 55;
    int color = 0;            // original, warm LCD, vivid
    int crt = 0;              // off, JVC-style slot mask, Trinitron-style grille
    int crt_strength = 65;
    int crt_gpu_glow = 0;      // renderer-composited low-resolution glow; opt-in
    int crt_bleed = 45;
};
struct NdsDisplayRect { int x=0, y=0, w=0, h=0; };
struct NdsDisplayGeometry {
    int width=256, height=384;
    NdsDisplayRect screens[2];
};
inline NdsDisplayGeometry nds_display_geometry(NdsScreenLayout layout,
        const NdsDisplayStyle& s, int top=256, int bottom=256) {
    NdsDisplayGeometry g;
    const int b=s.border, gap=s.gap;
    if (layout==NdsScreenLayout::Separate) {
        g.width=std::max(top,bottom)+2*b; g.height=192+2*b;
        g.screens[0]={b,b,top,192}; g.screens[1]={b,b,bottom,192};
    } else if (layout==NdsScreenLayout::TopOnly || layout==NdsScreenLayout::BottomOnly) {
        const int i=layout==NdsScreenLayout::BottomOnly ? 1 : 0;
        const int w=i ? bottom : top;
        g.width=w+2*b; g.height=192+2*b; g.screens[i]={b,b,w,192};
    } else if (layout==NdsScreenLayout::SideBySide) {
        g.width=top+bottom+4*b+gap; g.height=192+2*b;
        if (!s.swap) { g.screens[0]={b,b,top,192}; g.screens[1]={top+3*b+gap,b,bottom,192}; }
        else { g.screens[1]={b,b,bottom,192}; g.screens[0]={bottom+3*b+gap,b,top,192}; }
    } else {
        g.width=std::max(top,bottom)+2*b; g.height=384+4*b+gap;
        g.screens[0]={(g.width-top)/2,s.swap ? 192+3*b+gap : b,top,192};
        g.screens[1]={(g.width-bottom)/2,s.swap ? b : 192+3*b+gap,bottom,192};
    }
    return g;
}
inline bool nds_display_touch(const NdsDisplayRect& r, float x, float y,
                              uint16_t* tx, uint16_t* ty) {
    if (r.w<=0 || r.h<=0 || x<r.x || y<r.y || x>=r.x+r.w || y>=r.y+r.h) return false;
    // Adaptive screens are centered around the physical 256-pixel stylus area.
    const float left=r.x+(r.w-256)/2.f;
    if (x<left || x>=left+256) return false;
    *tx=uint16_t(x-left); *ty=uint16_t(y-r.y); return true;
}
inline bool nds_parse_hex_color(const std::string& text, uint32_t* value) {
    const size_t start=text.size()==7 && text[0]=='#' ? 1 : 0;
    if (text.size()-start!=6) return false;
    uint32_t v=0;
    for (size_t i=start;i<text.size();++i) {
        const char c=text[i];
        int n=c>='0'&&c<='9' ? c-'0' : c>='a'&&c<='f' ? c-'a'+10 : c>='A'&&c<='F' ? c-'A'+10 : -1;
        if (n<0) return false;
        v=(v<<4)|uint32_t(n);
    }
    *value=v; return true;
}
inline std::string nds_hex_color(uint32_t c) { char s[8]; std::snprintf(s,sizeof(s),"#%06X",c&0xFFFFFF); return s; }

// Independent presentation effects, not ports of third-party shader code.
// Work only on copies of published host pixels, never emulated framebuffers.
inline int nds_crt_filter(const uint32_t* pixels,int width,int height,
        const NdsDisplayStyle& s,std::vector<uint32_t>& out) {
    constexpr int scale=4;
    out.resize(size_t(width)*height*scale*scale);
    const float strength=s.crt_strength/100.f;
    // Independent procedural profiles inspired by MiSTer's preset composition.
    // No MiSTer mask, polyphase, or gamma-table assets are bundled.
    static const auto gamma=[] {
        std::array<std::array<float,256>,2> table{};
        for(int p=0;p<2;++p) for(int c=0;c<256;++c)
            table[p][c]=255.f*std::pow(c/255.f,1.f/(p==0 ? 1.13f : 1.10f));
        return table;
    }();
    const int profile=s.crt==2 ? 1 : 0;
    const float softness=(profile ? .12f : .18f)*strength;
    const float line_darkness=profile ? .40f : .30f;
    const float bleed=s.crt_bleed/100.f*strength;
    for(int y=0;y<height;++y) for(int x=0;x<width;++x) {
        const uint32_t center=pixels[y*width+x];
        const uint32_t left=pixels[y*width+std::max(0,x-1)];
        const uint32_t right=pixels[y*width+std::min(width-1,x+1)];
        float rgb[3];
        for(int c=0;c<3;++c) {
            const int shift=16-8*c;
            const float v=(1-softness)*((center>>shift)&255)+softness*.5f*(((left>>shift)&255)+((right>>shift)&255));
            const float shaped=gamma[profile][int(std::clamp(v,0.f,255.f))];
            rgb[c]=v+(shaped-v)*strength;
        }
        if(s.color) {
            const float l=.2126f*rgb[0]+.7152f*rgb[1]+.0722f*rgb[2];
            for(float& c:rgb) c=l+(c-l)*(s.color==1 ? .82f : 1.18f);
            if(s.color==1) {rgb[0]*=1.02f;rgb[1]*=.98f;rgb[2]*=.90f;}
        }
        const float luminance=std::clamp((rgb[0]+rgb[1]+rgb[2])/(3*255.f),0.f,1.f);
        float beam_rgb[4][3];
        for(int dx=0;dx<scale;++dx) {
            const float phase=(dx+.5f)/scale-.5f;
            if(bleed==0) {
                for(int c=0;c<3;++c) beam_rgb[dx][c]=rgb[c];
                continue;
            }
            for(int c=0;c<3;++c) {
                const int shift=16-8*c;
                const float original=(center>>shift)&255;
                const float neighbor=((phase<0 ? left : right)>>shift)&255;
                const float v=(1-softness)*original+softness*.5f*(((left>>shift)&255)+((right>>shift)&255))+
                    (neighbor-original)*std::fabs(phase)*bleed;
                const float shaped=gamma[profile][int(std::clamp(v,0.f,255.f))];
                beam_rgb[dx][c]=v+(shaped-v)*strength;
            }
            if(s.color) {
                auto& p=beam_rgb[dx];
                const float l=.2126f*p[0]+.7152f*p[1]+.0722f*p[2];
                for(float& c:p) c=l+(c-l)*(s.color==1 ? .82f : 1.18f);
                if(s.color==1) {p[0]*=1.02f;p[1]*=.98f;p[2]*=.90f;}
            }
        }
        for(int dy=0;dy<scale;++dy) for(int dx=0;dx<scale;++dx) {
            const int ox=x*scale+dx,oy=y*scale+dy;
            // Bright phosphors broaden the beam, reducing dark-line depth.
            float beam=1.f;
            if(dy==3) beam-=line_darkness*strength*(1.f-.55f*luminance);
            else if(dy==0) beam-=line_darkness*.22f*strength*(1.f-.55f*luminance);
            float masks[3]={1,1,1};
            if(profile==0) {
                const bool slot=((ox+((oy/3)&1)*3)%6)<4 && (oy%3)<2;
                if(!slot) for(float& m:masks) m-=.20f*strength;
            } else {
                const int phosphor=(ox%6)/2;
                for(int c=0;c<3;++c) if(c!=phosphor) masks[c]-=.24f*strength;
                if(oy==height*scale/3 || oy==2*height*scale/3)
                    for(float& m:masks) m*=1.f-.08f*strength;
            }
            uint32_t result=0xFF000000;
            for(int c=0;c<3;++c) {
                float value=std::clamp(beam_rgb[dx][c]*beam*masks[c],0.f,255.f);
                result|=uint32_t(std::clamp(value+.5f,0.f,255.f))<<(16-8*c);
            }
            out[size_t(oy)*width*scale+ox]=result;
        }
    }
    return scale;
}
inline int nds_display_filter(const uint32_t* pixels, int width, int height,
        const NdsDisplayStyle& s, std::vector<uint32_t>& out) {
    if(s.crt) return nds_crt_filter(pixels,width,height,s,out);
    const int scale=s.lcd ? 4 : 1;
    if (!s.lcd && !s.color) return 1;
    out.resize(size_t(width)*height*scale*scale);
    const float strength=s.lcd_strength/100.f;
    for (int y=0;y<height;++y) for (int x=0;x<width;++x) {
        const uint32_t p=pixels[y*width+x];
        float r=(p>>16)&255, g=(p>>8)&255, b=p&255;
        if (s.color) {
            const float l=.2126f*r+.7152f*g+.0722f*b;
            const float saturation=s.color==1 ? .82f : 1.18f;
            r=l+(r-l)*saturation; g=l+(g-l)*saturation; b=l+(b-l)*saturation;
            if (s.color==1) { r*=1.02f; g*=.98f; b*=.90f; }
        }
        for (int dy=0;dy<scale;++dy) for (int dx=0;dx<scale;++dx) {
            float weight=1;
            if (s.lcd==1 && dy==3) weight=1-.48f*strength;
            if (s.lcd==2) {
                if (dx==3) weight*=1-.42f*strength;
                if (dy==3) weight*=1-.42f*strength;
            }
            auto channel=[&](float v) { return uint32_t(std::clamp(v*weight+.5f,0.f,255.f)); };
            out[size_t(y*scale+dy)*width*scale+x*scale+dx]=0xFF000000u|(channel(r)<<16)|(channel(g)<<8)|channel(b);
        }
    }
    return scale;
}
