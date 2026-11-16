#!/bin/bash
# Native ARM64-only research build against reviewed unchanged upstream library.
set -eu
variant=${1:-official}
mkdir -p /out/artifacts
cmake -S /source -B /out/build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DHWCPIPE_BUILD_EXAMPLES=ON \
    -DHWCPIPE_ENABLE_LTO=OFF \
    '-DCMAKE_CXX_FLAGS=-mcpu=cortex-a35 -fwrapv -fno-strict-aliasing' \
    '-DCMAKE_EXE_LINKER_FLAGS=-static-libstdc++ -static-libgcc'
if [ "$variant" = targeted ]; then
    cmake --build /out/build --target hwcpipe --parallel 2
    artifact=gpu-counter-targeted
    c++ -std=c++14 -O2 -mcpu=cortex-a35 -fwrapv -fno-strict-aliasing \
        -I/source/hwcpipe/include -I/source/backend/device/include -I/source/backend/device/src \
        /gpu-counter-targeted.cpp /out/build/hwcpipe/libhwcpipe.a \
        /out/build/backend/device/libdevice.a -pthread -static-libstdc++ -static-libgcc \
        -o "/out/artifacts/$artifact"
    cp /gpu-counter-targeted.cpp /out/gpu-counter-targeted.cpp
else
    cmake --build /out/build --target api-example --parallel 2
    artifact=api-example
    cp /out/build/examples/api-example "/out/artifacts/$artifact"
fi
cp /source/LICENSE.md /out/artifacts/LICENSE.libGPUCounters.md
cp /out/build/compile_commands.json /out/compile_commands.json
cp /out/build/CMakeCache.txt /out/CMakeCache.txt
dpkg-query -W > /out/packages.txt
c++ --version > /out/compiler.txt
getconf GNU_LIBC_VERSION > /out/libc.txt
file "/out/artifacts/$artifact" > /out/artifacts/file.txt
readelf -h -l -d -V "/out/artifacts/$artifact" > /out/artifacts/elf.txt
ldd "/out/artifacts/$artifact" > /out/artifacts/ldd.txt
cd /out/artifacts
sha256sum "$artifact" > artifacts.sha256
