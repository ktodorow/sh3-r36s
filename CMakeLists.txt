cmake_minimum_required(VERSION 3.20)
project(sh3_r36s C)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE RelWithDebInfo)
endif()

file(GLOB GEN CONFIGURE_DEPENDS src/recomp/gen/*.c)
file(GLOB RT CONFIGURE_DEPENDS src/runtime/*.c src/win32/*.c src/d3d8/*.c src/game/*.c)

add_executable(sh3 ${GEN} ${RT})
target_include_directories(sh3 PRIVATE src/recomp/gen)
if(SH3_GLES_SAMPLES)
  target_include_directories(sh3 PRIVATE ${CMAKE_BINARY_DIR}/generated)
  target_compile_definitions(sh3 PRIVATE SH3_GLES_SAMPLES=1)
endif()
# Lifted code relies on wrapping arithmetic and type punning through guest memory.
target_compile_options(sh3 PRIVATE -fwrapv -fno-strict-aliasing)
set_source_files_properties(${GEN} PROPERTIES COMPILE_OPTIONS "-w")
# The launcher's images are built into the binary (src/d3d8/launcher.c).
file(SHA1 ${CMAKE_SOURCE_DIR}/assets/splash.bmp SPLASH_SHA1)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS assets/splash.bmp)
set_source_files_properties(src/d3d8/launcher.c PROPERTIES COMPILE_DEFINITIONS
                            "SRC_DIR=\"${CMAKE_SOURCE_DIR}\";SPLASH_SHA1=\"${SPLASH_SHA1}\""
                            OBJECT_DEPENDS "${CMAKE_SOURCE_DIR}/assets/splash.bmp;${CMAKE_SOURCE_DIR}/assets/logo.bmp;${CMAKE_SOURCE_DIR}/assets/font.bmp")

# GL/GLES is loaded at run time through SDL (src/d3d8/gl.c).
find_package(SDL2 REQUIRED)
target_link_libraries(sh3 PRIVATE SDL2::SDL2 m pthread)
