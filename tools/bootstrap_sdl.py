"""Build a fixed upstream SDL3 source revision into a private SDK prefix."""
from pathlib import Path
import argparse
import subprocess

SDL_COMMIT="8e37db5e797b6167f3a00d697d816a684bd259c7"  # release-3.4.10


def prepare_sdl(work: Path, jobs=4):
    work=work.resolve();source=work / "SDL";build=work / "build";prefix=work / "prefix"
    source.mkdir(parents=True,exist_ok=True)
    def run(*args):subprocess.run([str(x) for x in args],check=True)
    if not (source / ".git").exists():run("git","init",source)
    current=subprocess.run(["git","-C",str(source),"rev-parse","HEAD"],capture_output=True,text=True)
    if current.returncode or current.stdout.strip()!=SDL_COMMIT:
        run("git","-C",source,"fetch","--depth","1","https://github.com/libsdl-org/SDL.git",SDL_COMMIT)
        run("git","-C",source,"checkout","--detach","FETCH_HEAD")
    got=subprocess.check_output(["git","-C",str(source),"rev-parse","HEAD"],text=True).strip()
    if got!=SDL_COMMIT:raise RuntimeError("SDL source revision mismatch")
    run("cmake","-S",source,"-B",build,"-G","Ninja","-DCMAKE_BUILD_TYPE=Release",
        "-DSDL_SHARED=OFF","-DSDL_STATIC=ON","-DSDL_TESTS=OFF","-DSDL_EXAMPLES=OFF",f"-DCMAKE_INSTALL_PREFIX={prefix}")
    run("cmake","--build",build,"-j",str(jobs));run("cmake","--install",build)
    return prefix


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("work",type=Path);args=parser.parse_args()
    print(prepare_sdl(args.work))
