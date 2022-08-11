#configuration
CONFIG +=  shared qpa no_mocdepend release qt_no_framework
host_build {
    QT_ARCH = x86_64
    QT_TARGET_ARCH = x86_64
} else {
    QT_ARCH = x86_64
    QMAKE_DEFAULT_LIBDIRS = /lib /usr/lib
    QMAKE_DEFAULT_INCDIRS = /Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/include /Users/distiller/miniconda3/conda-bld/qt_1548883576517/_build_env/include/c++/v1 /Users/distiller/miniconda3/conda-bld/qt_1548883576517/_build_env/lib/clang/4.0.1/include /Applications/Xcode-9.0.1.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.9.sdk/usr/include
}
QT_CONFIG +=  minimal-config small-config medium-config large-config full-config no-pkg-config c++11 accessibility opengl shared qpa reduce_exports getaddrinfo ipv6ifname getifaddrs system-jpeg system-png png freetype no-harfbuzz system-zlib cups iconv ssl securetransport rpath corewlan icu concurrent audio-backend release

#versioning
QT_VERSION = 5.6.2
QT_MAJOR_VERSION = 5
QT_MINOR_VERSION = 6
QT_PATCH_VERSION = 2

#namespaces
QT_LIBINFIX = 
QT_NAMESPACE = 

QT_EDITION = OpenSource

QT_COMPILER_STDCXX = 201103
QT_CLANG_MAJOR_VERSION = 4
QT_CLANG_MINOR_VERSION = 0
