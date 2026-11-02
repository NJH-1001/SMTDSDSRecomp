#pragma once
#include <algorithm>
#include <cstdint>
#include <vector>

// Independent host presentation helper. Extract bright color into a quarter-
// resolution texture using integer arithmetic; all enlarged-image blending is
// left to SDL's accelerated renderer. Nothing reads or writes guest memory.
inline int nds_crt_glow_extent(int size) { return (size+3)/4; }
inline void nds_crt_glow_image(const uint32_t* source,int width,int height,
        std::vector<uint32_t>& output,std::vector<uint32_t>& scratch) {
    if(!source || width<=0 || height<=0) {output.clear();scratch.clear();return;}
    const int w=nds_crt_glow_extent(width),h=nds_crt_glow_extent(height);
    scratch.resize(size_t(w)*h);output.resize(scratch.size());
    for(int y=0;y<h;++y) for(int x=0;x<w;++x) {
        unsigned sum[3]={},peak[3]={};unsigned count=0;
        for(int yy=y*4;yy<std::min(y*4+4,height);++yy)
            for(int xx=x*4;xx<std::min(x*4+4,width);++xx) {
                const uint32_t p=source[yy*width+xx];
                for(int c=0;c<3;++c) {
                    const unsigned v=std::max(0,int((p>>(16-c*8))&255)-32);
                    sum[c]+=v;peak[c]=std::max(peak[c],v);
                }
                ++count;
            }
        // An average alone erased thin text/sparks: a single bright pixel
        // lost 15/16 of its energy before the blur and blend. Preserve peaks
        // while retaining an average contribution for larger luminous areas.
        uint32_t value=0xFF000000u;
        for(int c=0;c<3;++c) value|=((sum[c]/count+3*peak[c])/4)<<(16-c*8);
        scratch[y*w+x]=value;
    }
    // A five-tap softening kernel on just 64x48 pixels per physical DS screen.
    // Fully overwrite both buffers so another screen/frame cannot leave trails.
    for(int y=0;y<h;++y) for(int x=0;x<w;++x) {
        const uint32_t p[]={scratch[y*w+x],scratch[y*w+std::max(0,x-1)],
            scratch[y*w+std::min(w-1,x+1)],scratch[std::max(0,y-1)*w+x],
            scratch[std::min(h-1,y+1)*w+x]};
        uint32_t value=0xFF000000u;
        for(int c=0;c<3;++c) {
            const int shift=16-c*8;
            unsigned v=((p[0]>>shift)&255)*4;
            for(int k=1;k<5;++k) v+=(p[k]>>shift)&255;
            value|=(v/8)<<shift;
        }
        output[y*w+x]=value;
    }
}
