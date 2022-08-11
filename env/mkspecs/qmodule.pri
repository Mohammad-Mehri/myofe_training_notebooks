CONFIG +=  compile_examples no-libdl qpa largefile precompile_header sse2 sse3 ssse3 sse4_1 sse4_2 avx avx2 pcre
QT_BUILD_PARTS += libs tools
QT_SKIP_MODULES +=  qtenginio qtlocation qtsensors qtserialport qtserialbus qtquickcontrols2 qtwayland qtcanvas3d qt3d qtwebengine
QT_NO_DEFINES =  ALSA CLOCK_MONOTONIC DBUS EGL EGLFS EGL_X11 EVDEV EVENTFD FONTCONFIG GLIB HARFBUZZ IMAGEFORMAT_JPEG INOTIFY LIBPROXY MREMAP OPENSSL OPENVG POSIX_FALLOCATE PULSEAUDIO STYLE_GTK TSLIB XRENDER ZLIB
QT_QCONFIG_PATH = 
host_build {
    QT_CPU_FEATURES.x86_64 =  cx16 mmx sse sse2 sse3 ssse3
} else {
    QT_CPU_FEATURES.x86_64 =  cx16 mmx sse sse2 sse3 ssse3
}
QT_COORD_TYPE = double
QT_LFLAGS_ODBC   = -lodbc
QMAKE_AR = /Users/distiller/miniconda3/conda-bld/qt_1548883576517/_build_env/bin/x86_64-apple-darwin13.4.0-ar cqs
QMAKE_RANLIB = /Users/distiller/miniconda3/conda-bld/qt_1548883576517/_build_env/bin/x86_64-apple-darwin13.4.0-ranlib
QMAKE_STRIP = /Users/distiller/miniconda3/conda-bld/qt_1548883576517/_build_env/bin/x86_64-apple-darwin13.4.0-strip
QMAKE_LINK = x86_64-apple-darwin13.4.0-clang++
QMAKE_CC = x86_64-apple-darwin13.4.0-clang
QMAKE_CXX = x86_64-apple-darwin13.4.0-clang++
styles += mac fusion windows
DEFINES += QT_NO_MTDEV
DEFINES += QT_NO_LIBUDEV
DEFINES += QT_NO_EVDEV
DEFINES += QT_NO_TSLIB
DEFINES += QT_NO_LIBINPUT
EXTRA_RPATHS +=  "/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/lib"
sql-drivers = 
sql-plugins =  sqlite
