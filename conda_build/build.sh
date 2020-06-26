#!/bin/sh
# See https://docs.conda.io/projects/conda-build/en/latest/resources/compiler-tools.html#an-aside-on-cmake-and-sysroots
declare -a CMAKE_PLATFORM_FLAGS
if [[ ${HOST} =~ .*darwin.* ]]; then
  CMAKE_PLATFORM_FLAGS+=(-DCMAKE_OSX_SYSROOT="${CONDA_BUILD_SYSROOT}")
  export LDFLAGS=$(echo "${LDFLAGS}" | sed "s/-Wl,-dead_strip_dylibs//g")
else
  CMAKE_PLATFORM_FLAGS+=(-DCMAKE_TOOLCHAIN_FILE="${RECIPE_DIR}/cross-linux.cmake")
fi

mkdir ../build
cd ../build

cmake -DCMAKE_INSTALL_PREFIX=${PREFIX} \
-DCMAKE_BUILD_TYPE=Release \
-DBUILD_SHARED_LIBS=ON \
-DNO_SONAME=ON \
-GNinja \
$SRC_DIR \
${CMAKE_PLATFORM_FLAGS[@]} 

ninja install
