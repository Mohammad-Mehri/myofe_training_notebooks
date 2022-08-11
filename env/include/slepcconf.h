#if !defined(__SLEPCCONF_H)
#define __SLEPCCONF_H

#ifndef SLEPC_PETSC_DIR
#define SLEPC_PETSC_DIR "${PETSC_DIR}"
#endif

#ifndef SLEPC_PETSC_ARCH
#define SLEPC_PETSC_ARCH "arch-conda-c-opt"
#endif

#ifndef SLEPC_DIR
#define SLEPC_DIR "${SLEPC_DIR}"
#endif

#ifndef SLEPC_LIB_DIR
#define SLEPC_LIB_DIR "${PETSC_DIR}/lib"
#endif

#endif
