// Original ROM-free console setup host. No emulation or generated game code.
#include <filesystem>
#include <iostream>
#include <string>
#include <vector>
#ifdef _WIN32
#include <windows.h>
static std::wstring wide(const std::string& s) {
    int n=MultiByteToWideChar(CP_UTF8,0,s.c_str(),-1,nullptr,0);
    std::wstring w(n,0);MultiByteToWideChar(CP_UTF8,0,s.c_str(),-1,w.data(),n);w.resize(n-1);return w;
}
static std::wstring quote(const std::wstring& s) {
    std::wstring r=L"\"";unsigned slashes=0;
    for(wchar_t c:s) {
        if(c==L'\\') {++slashes;continue;}
        r.append(slashes*(c==L'"' ? 2 : 1),L'\\');slashes=0;
        if(c==L'"') r+=L'\\';r+=c;
    }
    r.append(slashes*2,L'\\');return r+L'"';
}
static int run(const std::vector<std::string>& args) {
    std::wstring command;
    for(const auto& a:args) {if(!command.empty()) command+=L' ';command+=quote(wide(a));}
    STARTUPINFOW start{};start.cb=sizeof(start);PROCESS_INFORMATION proc{};
    if(!CreateProcessW(nullptr,command.data(),nullptr,nullptr,FALSE,0,nullptr,nullptr,&start,&proc)) return 127;
    WaitForSingleObject(proc.hProcess,INFINITE);DWORD code=1;GetExitCodeProcess(proc.hProcess,&code);
    CloseHandle(proc.hThread);CloseHandle(proc.hProcess);return int(code);
}
#else
#include <sys/wait.h>
#include <unistd.h>
static int run(const std::vector<std::string>& args) {
    std::vector<char*> argv;for(const auto& a:args) argv.push_back(const_cast<char*>(a.c_str()));argv.push_back(nullptr);
    auto child=fork();if(child<0) return 127;
    if(child==0) {execvp(argv[0],argv.data());_exit(127);}
    int status=0;if(waitpid(child,&status,0)<0) return 127;
    return WIFEXITED(status) ? WEXITSTATUS(status) : 1;
}
#endif
int main(int argc,char** argv) {
#ifdef _WIN32
    SetConsoleCP(CP_UTF8);SetConsoleOutputCP(CP_UTF8);
    const std::string python="python";
#else
    const std::string python="python3";
#endif
    if(argc>1 && std::string(argv[1])=="--version") {std::cout<<"SMTDSDSRecomp ROM-free setup 0.1.0\n";return 0;}
    if(argc>1 && std::string(argv[1])=="--help") {
        std::cout<<"Setup requires Python 3.11+, CMake, Ninja, a C/C++ compiler and SDL3 development files.\n"
                 <<"Run without arguments for local file prompts, or: Setup install [install.py options]\n"
                 <<"Play an existing installation: Setup play --work <private-directory>\n";return 0;
    }
    auto root=std::filesystem::absolute(std::filesystem::u8path(argv[0])).parent_path();
    bool play=argc>1 && std::string(argv[1])=="play";
    auto script=root / "tools" / (play ? "play.py" : "install.py");
    if(!std::filesystem::exists(script)) {std::cerr<<"Keep Setup beside its tools/config/deps folders.\n";return 1;}
    std::vector<std::string> command{python,script.u8string()};
    if(argc>1) {
        int first=(play || std::string(argv[1])=="install") ? 2 : 1;
        for(int i=first;i<argc;++i) command.push_back(argv[i]);
    } else {
        std::cout<<"SMTDSDSRecomp private local build\nRequires Python 3.11+, CMake, Ninja, C/C++ compiler and SDL3 development files.\n"
                 <<"No game files are downloaded or uploaded. First build can take several minutes.\n";
        for(const auto* key:{"rom","bios9","bios7","firmware","work"}) {
            std::cout<<key<<" path (no surrounding quotes): "<<std::flush;
            std::string value;if(!std::getline(std::cin,value) || value.empty()) return 1;
            command.push_back(std::string("--")+key);command.push_back(value);
        }
    }
    int result=run(command);
    if(result==127) std::cerr<<"Python could not start; install Python 3.11+ and add it to PATH.\n";
    std::cout<<(result==0 ? "Completed.\n" : "Stopped; inspect the private installation log.\n");
    return result;
}
