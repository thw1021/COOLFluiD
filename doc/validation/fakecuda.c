/**
 * libfakecuda.so - CUDA runtime shim for COOLFluiD
 *
 * Tries the real CUDA library first; if cudaGetDevice/cudaGetDeviceCount
 * fail (flaky driver state), falls back to a fake device so the CPU-only
 * code path can proceed. COOLFluiD hard-initializes CUDA in
 * CudaDeviceManager.cu even when GPU compute is not used.
 *
 * Build: gcc -shared -fPIC -I/usr/local/cuda-12.2/include -o libfakecuda.so fakecuda.c -ldl
 * Use:   LD_PRELOAD=./libfakecuda.so coolfluid-solver ...
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <stddef.h>

/* We only need the cudaDeviceProp struct layout and a few function
 * signatures.  We avoid including <cuda_runtime_api.h> because it
 * #defines cudaGetDeviceProperties to cudaGetDeviceProperties_v2, which
 * breaks our own function-pointer typedef names.  Instead we declare
 * the struct ourselves (only the fields CudaDeviceManager.cu reads). */

struct cudaDeviceProp {
    char   name[256];
    size_t totalGlobalMem;
    size_t sharedMemPerBlock;
    int    regsPerBlock;
    int    warpSize;
    size_t memPitch;
    int    maxThreadsPerBlock;
    int    maxThreadsDim[3];
    int    maxGridSize[3];
    size_t totalConstMem;
    int    major;
    int    minor;
    /* remaining fields are padding; size must be >= real struct */
    char   pad[2048];
};

typedef int (*getDeviceCount_t)(int*);
typedef int (*getDevice_t)(int*);
typedef int (*setDevice_t)(int);
typedef int (*getDeviceProps_t)(struct cudaDeviceProp*, int);

static getDeviceCount_t real_count = NULL;
static getDevice_t       real_get   = NULL;
static setDevice_t       real_set   = NULL;
static getDeviceProps_t  real_props = NULL;
static int use_fake = 0;
static int fake_dev = 0;

static void init_real(void) {
    if (real_count) return;
    void* h = dlopen("libcudart.so.12", RTLD_NOW | RTLD_GLOBAL);
    if (!h) h = dlopen("libcudart.so", RTLD_NOW | RTLD_GLOBAL);
    if (!h) { use_fake = 1; return; }
    real_count = (getDeviceCount_t) dlsym(h, "cudaGetDeviceCount");
    real_get   = (getDevice_t)       dlsym(h, "cudaGetDevice");
    real_set   = (setDevice_t)       dlsym(h, "cudaSetDevice");
    real_props = (getDeviceProps_t)  dlsym(h, "cudaGetDeviceProperties_v2");
    if (!real_props) real_props = (getDeviceProps_t) dlsym(h, "cudaGetDeviceProperties");
    if (!real_count || !real_get || !real_set || !real_props) use_fake = 1;
}

static void fill_fake_props(struct cudaDeviceProp* p) {
    memset(p, 0, sizeof(*p));
    strcpy(p->name, "FakeDevice");
    p->totalGlobalMem = 4096ULL * 1024 * 1024;
    p->sharedMemPerBlock = 48 * 1024;
    p->regsPerBlock = 65536;
    p->warpSize = 32;
    p->memPitch = 2147483647;
    p->maxThreadsPerBlock = 1024;
    p->maxThreadsDim[0] = 1024; p->maxThreadsDim[1] = 1024; p->maxThreadsDim[2] = 64;
    p->maxGridSize[0] = 2147483647; p->maxGridSize[1] = 65535; p->maxGridSize[2] = 65535;
    p->totalConstMem = 65536;
    p->major = 8; p->minor = 6;
}

/* Intercepted functions (must match the symbol names the binary imports).
 * cudaGetDeviceProperties is actually cudaGetDeviceProperties_v2 in recent
 * CUDA toolkits, so we export both names. */
int cudaGetDeviceCount(int* count) {
    init_real();
    if (!use_fake && real_count) {
        int rc = real_count(count);
        if (rc == 0 && count && *count > 0) return rc;
    }
    use_fake = 1;
    if (count) *count = 1;
    return 0;
}

int cudaGetDevice(int* dev) {
    init_real();
    fprintf(stderr, "[fakecuda] cudaGetDevice called, use_fake=%d\n", use_fake);
    if (!use_fake && real_get) {
        int rc = real_get(dev);
        fprintf(stderr, "[fakecuda] real_get rc=%d *dev=%d\n", rc, dev ? *dev : -99);
        if (rc == 0 && dev && *dev >= 0) return rc;
    }
    use_fake = 1;
    if (dev) *dev = fake_dev;
    fprintf(stderr, "[fakecuda] returning fake dev=%d\n", *dev);
    return 0;
}

int cudaSetDevice(int dev) {
    init_real();
    if (!use_fake && real_set) {
        int rc = real_set(dev);
        if (rc == 0) { fake_dev = dev; return rc; }
    }
    use_fake = 1;
    fake_dev = dev;
    return 0;
}

int cudaGetDeviceProperties_v2(struct cudaDeviceProp* prop, int dev) {
    init_real();
    if (!use_fake && real_props) {
        int rc = real_props(prop, dev);
        if (rc == 0) return rc;
    }
    use_fake = 1;
    fill_fake_props(prop);
    return 0;
}

/* alias for non-v2 builds */
int cudaGetDeviceProperties(struct cudaDeviceProp* prop, int dev)
    __attribute__((alias("cudaGetDeviceProperties_v2")));
