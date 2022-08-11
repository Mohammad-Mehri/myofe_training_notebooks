GENCCODE_ASSEMBLY_TYPE=-a gcc-darwin
SO=dylib
SOBJ=dylib
A=a
LIBPREFIX=lib
LIB_EXT_ORDER=.58.2.dylib
COMPILE=x86_64-apple-darwin13.4.0-clang -DU_ATTRIBUTE_DEPRECATED= -D_FORTIFY_SOURCE=2 -mmacosx-version-min=10.9   -DU_HAVE_ATOMIC=1 -DU_HAVE_STRTOD_L=1  -march=core2 -mtune=haswell -mssse3 -ftree-vectorize -fPIC -fPIE -fstack-protector-strong -O2 -pipe -I/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/include -fdebug-prefix-map=/Users/travis/miniconda3/conda-bld/icu_1537667881626/work=/usr/local/src/conda/icu-58.2 -fdebug-prefix-map=/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env=/usr/local/src/conda-prefix -std=c99 -Wall -pedantic -Wshadow -Wpointer-arith -Wmissing-prototypes -Wwrite-strings   -fno-common -c
LIBFLAGS=-I/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/include  -dynamic
GENLIB=x86_64-apple-darwin13.4.0-clang -dynamiclib -dynamic -march=core2 -mtune=haswell -mssse3 -ftree-vectorize -fPIC -fPIE -fstack-protector-strong -O2 -pipe -I/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/include -fdebug-prefix-map=/Users/travis/miniconda3/conda-bld/icu_1537667881626/work=/usr/local/src/conda/icu-58.2 -fdebug-prefix-map=/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env=/usr/local/src/conda-prefix -std=c99 -Wall -pedantic -Wshadow -Wpointer-arith -Wmissing-prototypes -Wwrite-strings   -Wl,-pie -Wl,-headerpad_max_install_names -Wl,-dead_strip_dylibs -Wl,-rpath,/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/lib -L/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/lib -Wl,-rpath,/Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/lib 
LDICUDTFLAGS=
LD_SONAME=-Wl,-compatibility_version -Wl,58 -Wl,-current_version -Wl,58.2 -install_name /Users/charlesmann/Research/UK/repositories/myofe_training_notebooks/env/lib/
RPATH_FLAGS=
BIR_LDFLAGS=
AR=/Users/travis/miniconda3/conda-bld/icu_1537667881626/_build_env/bin/x86_64-apple-darwin13.4.0-ar
ARFLAGS=r -c
RANLIB=/Users/travis/miniconda3/conda-bld/icu_1537667881626/_build_env/bin/x86_64-apple-darwin13.4.0-ranlib
INSTALL_CMD=/usr/bin/install -c
