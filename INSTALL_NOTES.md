# COOLFluiD 从零开始完整安装指南

> 目标环境：Ubuntu 22.04 | CUDA 12.2 | Boost 1.85 | MPICH | PETSc 3.24 | Mutation++ | RTX 3050 (sm_86)
>
> 适用场景：从 **原始未修改的 COOLFluiD 源码**（GitHub 或官方发布包）开始，完成完整安装

---

## 目录

- [第 0 步：前置条件](#第-0-步前置条件)
- [第 1 步：获取源码](#第-1-步获取源码)
- [第 2 步：创建 coolfluid.conf](#第-2-步创建-coolfluidconf)
- [第 3 步：运行 prepare.pl](#第-3-步运行-preparepl)
- [第 4 步：源码兼容性修复](#第-4-步源码兼容性修复)
  - [4a. 移除 throw() 动态异常规范](#4a-移除-throw-动态异常规范)
  - [4b. 修复 filesystem 命名冲突](#4b-修复-filesystem-命名冲突)
  - [4c. 修复 PETSc CUDA 预条件器](#4c-修复-petsc-cuda-预条件器)
  - [4d. 修复 Mutation++ 依赖 Eigen3](#4d-修复-mutation-依赖-eigen3)
  - [4e. 修复 CUDA template 关键字](#4e-修复-cuda-template-关键字)
- [第 5 步：CMake 重新配置](#第-5-步cmake-重新配置)
- [第 6 步：编译](#第-6-步编译)
- [第 7 步：安装](#第-7-步安装)
- [第 8 步：验证](#第-8-步验证)
- [附录：常见编译错误速查](#附录常见编译错误速查)
- [完整命令速查](#完整命令速查)

---

## 第 0 步：前置条件

### 依赖列表

| 依赖 | 最低版本 | 用途 |
|------|----------|------|
| CUDA | 12.2 | GPU 加速（需 nvcc） |
| Boost | 1.85 | 智能指针、文件系统、正则表达式 |
| MPICH | 任意 | MPI 并行计算 |
| PETSc | 3.24 | 线性求解器（建议含 CUDA 支持） |
| Mutation++ | 最新 | 热化学非平衡库 |
| Eigen3 | 3.x | 线性代数库（Mutation++ 依赖） |
| CMake | 2.8.3+ | 构建系统 |
| g++/gfortran | 11+ | C++/Fortran 编译器 |

### 验证环境

```bash
source ~/.bashrc

# 验证关键工具版本
nvcc --version            # 应显示 Cuda compilation tools, release 12.2
mpicc --version           # 应显示 gcc (Ubuntu 11.x)
cmake --version           # 应显示 3.x+
g++ --version             # 应显示 g++ (Ubuntu 11.x)
```

---

## 第 1 步：获取源码

```bash
# 克隆官方仓库
cd ~/packages
git clone https://github.com/andrealani/COOLFluiD.git
cd COOLFluiD
```

或解压官方发布包：

```bash
cd ~/packages
tar xzf COOLFluiD-xxx.tar.gz
cd COOLFluiD
```

---

## 第 2 步：创建 coolfluid.conf

在 COOLFluiD 根目录创建配置文件 `coolfluid.conf`（**注意：文件名全小写**，`prepare.pl` 读取此文件）：

```ini
#==================================================================
# COOLFluiD Configuration File
#==================================================================
# 请根据实际环境修改路径

coolfluid_dir    = /home/youruser/packages/COOLFluiD
basebuild_dir    = /home/youruser/packages/COOLFluiD/build
install_dir      = /home/youruser/packages/COOLFluiD/install

# compilers
cc               = /usr/bin/gcc
cxx              = /usr/bin/g++
fc               = gfortran

# CUDA configuration
cudac            = /usr/local/cuda-12.2/bin/nvcc
cuda_dir         = /usr/local/cuda-12.2
cudacflags       = --std c++17 -arch sm_86
withcuda         = 1

nofortran        = 0
withcurl         = 0

# library locations
mpi_dir          = /home/youruser/packages/mpichInstall
boost_dir        = /home/youruser/packages/boost_1_85_0/install
petsc_dir        = /home/youruser/packages/petsc
parmetis_dir     = /home/youruser/packages/mpichInstall

# Mutation++ configuration
mutationpp_dir   = /home/youruser/packages/Mutationpp/install
with_mutationpp  = 1

allactive        = 1
with_testcases   = 1
cmake_generator  = make

# C++17 standard (required by Boost 1.85 atomic headers)
optim_cxxflags   = -O3 -g -fPIC -std=c++17
optim_cflags     = -O3 -g -fPIC
optim_fflags     = -O3 -g -fPIC
```

> **⚠️ GPU 架构参考**（将 `sm_86` 替换为你的 GPU 架构）：
> - RTX 30xx / Axxx → `sm_86`
> - RTX 20xx / T4   → `sm_75`
> - GTX 10xx / P100 → `sm_60`/`sm_61`
> - A100 / H100     → `sm_80`/`sm_90`
> - 纯 CPU（无 CUDA）→ `withcuda = 0`，跳过 CUDA 部分

---

## 第 3 步：运行 prepare.pl

```bash
cd /home/youruser/packages/COOLFluiD
./prepare.pl --build=optim
```

此脚本读取 `coolfluid.conf`，生成 `build/optim/` 目录和 CMake 缓存。

---

## 第 4 步：源码兼容性修复

原始 COOLFluiD 使用 C++98/03 风格的 `throw()` 动态异常规范，C++17 已将其移除。另外还有多个 C++17 迁移相关的兼容性问题需要修复。

### 4a. 移除 throw() 动态异常规范

```bash
cd /home/youruser/packages/COOLFluiD

# logcpp
sed -i 's/throw()//'                                              src/logcpp/Category.cpp
sed -i 's/throw(std::invalid_argument)//'                          src/logcpp/Priority.cpp

# Common — Exception::what() 需改为 noexcept
sed -i 's/virtual const char\* what() const throw()/virtual const char* what() const noexcept/' src/Common/Exception.hh
sed -i 's/const char\* what() const throw()/const char* what() const noexcept/'               src/Common/Exception.cxx

# Common — 各异常类构造函数中的 throw()
sed -i 's/throw()//'                                              src/Common/FilesystemException.cxx
sed -i 's/throw()//'                                              src/Common/NoSuchValueException.cxx
sed -i 's/throw()//'                                              src/Common/ParserException.cxx

# Framework — InterpolatorRegister
sed -i '/throw (Common::NoSuchValueException)/d'                  src/Framework/InterpolatorRegister.hh
sed -i '/throw (Common::NoSuchValueException)/d'                  src/Framework/InterpolatorRegister.cxx

# THOR2CFmesh
sed -i '/throw (Framework::NegativeVolumeException)/d'            plugins/THOR2CFmesh/CheckNodeNumberingHexa.hh
sed -i '/throw (Framework::NegativeVolumeException)/d'            plugins/THOR2CFmesh/CheckNodeNumberingHexa.cxx
```

> **🔧 问题说明**：C++17 完全移除了动态异常规范 `throw()` / `throw(type)`，必须删除或替换为 `noexcept`。

### 4b. 修复 filesystem 命名冲突

**问题**：C++17 下 `std::filesystem` 与 `boost::filesystem` 命名冲突。

**修复**：编辑 `apps/Solver/coolfluid-solver.cxx`：

在 `main()` 函数内的 `using namespace boost;` 下方添加一行：

```cpp
namespace fs = boost::filesystem;
```

然后将该文件中所有 `filesystem::` 替换为 `fs::`：

```bash
sed -i 's/namespace boost;/namespace boost;\n  namespace fs = boost::filesystem;/' apps/Solver/coolfluid-solver.cxx
sed -i 's/boost::filesystem::/fs::/g' apps/Solver/coolfluid-solver.cxx
sed -i 's/filesystem::/fs::/g'          apps/Solver/coolfluid-solver.cxx
```

### 4c. 修复 PETSc CUDA 预条件器

**问题**：PETSc 3.13+ 移除了 `PCSACUSP` 等 CUDA 预条件器常量，旧版本检查条件（排除 9/11/12）对更新版本无效。

**修复**：编辑 `plugins/Petsc/PetscOptions.cxx`，将以下代码：

```cpp
#ifdef CF_HAVE_CUDA
#if PETSC_VERSION_MINOR!=9 && PETSC_VERSION_MINOR!=11 && PETSC_VERSION_MINOR!=12
  _pcType["PCSACUSP"]    = PCSACUSP;
  _pcType["PCSACUSPPOLY"] = PCSACUSPPOLY;
  _pcType["PCBICGSTABCUSP"] = PCBICGSTABCUSP;
#endif
#endif
```

替换为：

```cpp
#ifdef CF_HAVE_CUDA
#if PETSC_VERSION_MINOR>=13
  // PCSACUSP and friends were removed starting from PETSc 3.13
#else
  _pcType["PCSACUSP"]    = PCSACUSP;
  _pcType["PCSACUSPPOLY"] = PCSACUSPPOLY;
  _pcType["PCBICGSTABCUSP"] = PCBICGSTABCUSP;
#endif
#endif
```

### 4d. 修复 Mutation++ 依赖 Eigen3

**问题**：Mutation++ 头文件引用了 `Eigen/Dense`，但 `CMakeLists.txt` 未将 Eigen 路径加入包含目录。

**修复**：编辑 `plugins/MutationppI/CMakeLists.txt`，在以下行之后：

```cmake
LIST ( APPEND MutationppI_includedirs ${MUTATIONPP_INCLUDE_DIR} )
```

添加一行：

```cmake
LIST ( APPEND MutationppI_includedirs ${EIGEN3_INCLUDE_DIR} )
```

### 4e. 修复 CUDA template 关键字

**问题**：nvcc + C++17 对从属模板名称（dependent names）的解析更严格，必须使用 `template` 关键字。

**修复**：编辑 `plugins/FiniteVolumeCUDA/FVMCC_ComputeRHSCell.cu`，将：

```cpp
SafePtr<SCHEME> lf  = getMethodData().getFluxSplitter().d_castTo<SCHEME>();
SafePtr<POLYREC> pr = getMethodData().getPolyReconstructor().d_castTo<POLYREC>();
SafePtr<LIMITER> lm = getMethodData().getLimiter().d_castTo<LIMITER>();
```

替换为：

```cpp
SafePtr<SCHEME> lf  = getMethodData().getFluxSplitter().template d_castTo<SCHEME>();
SafePtr<POLYREC> pr = getMethodData().getPolyReconstructor().template d_castTo<POLYREC>();
SafePtr<LIMITER> lm = getMethodData().getLimiter().template d_castTo<LIMITER>();
```

---

## 第 5 步：CMake 重新配置

`prepare.pl` 生成的 CMake 缓存可能不完整，需要手动补充关键参数：

```bash
cd /home/youruser/packages/COOLFluiD/build/optim

cmake -DCF_CUDAC_FLAGS="--std c++17 -arch sm_86"                                        \
      -DCMAKE_CUDA_FLAGS="--std c++17 -arch sm_86"                                      \
      -DPETSC_INC_DIR="/home/youruser/packages/petsc/arch-linux-c-opt/include;/home/youruser/packages/petsc/include" \
      -DEIGEN3_INCLUDE_DIR=/usr/include/eigen3                                           \
      .
```

> ⚠️ 每次重新运行 `prepare.pl` 后都需要重新执行此 cmake 命令，因为它会重置缓存。

---

## 第 6 步：编译

```bash
# 获取 CPU 核心数
NPROC=$(nproc)

# 启动编译（建议在 COOLFluiD 根目录执行）
cd /home/youruser/packages/COOLFluiD/build/optim
make -j${NPROC} 2>&1 | tee build.log
```

**编译耗时参考**（RTX 3050 + 14 核）：
- 初次完整编译：约 40–60 分钟
- 增量编译（修复后）：约 5–15 分钟

**监控进度**：
```bash
# 实时查看进度
tail -f build.log

# 查看完成百分比
grep -oP '\[\d+%\]' build.log | tail -3

# 检查错误
grep -c "error:" build.log
```

---

## 第 7 步：安装

```bash
make install
```

安装产物：
```
install/bin/
├── coolfluid-solver      # 主求解器可执行文件（~6.5MB）
├── ConvertStructMesh     # 网格转换工具
├── coef_merge            # 系数合并工具
├── tecplot_merge         # Tecplot 文件合并
└── xcfcase_converter     # 算例文件转换器

install/lib/
└── lib*.so               # 约 167 个共享库
```

---

## 第 8 步：验证

```bash
# 验证可执行文件
/home/youruser/packages/COOLFluiD/install/bin/coolfluid-solver --help

# 验证 CUDA 链接
ldd /home/youruser/packages/COOLFluiD/install/bin/coolfluid-solver | grep -i cuda

# 验证 MPI 链接
ldd /home/youruser/packages/COOLFluiD/install/bin/coolfluid-solver | grep -i mpi
```

---

## 附录：常见编译错误速查

| 错误现象 | 根因 | 修复方法 |
|---------|------|---------|
| `redefinition of constexpr` / Boost atomic 错误 | Boost 1.85 与 CUDA C++11 冲突 | 确保 `cudacflags` 包含 `--std c++17` |
| `atomicAdd` no matching overload | 未指定 CUDA 架构，< sm_60 | `cudacflags` 添加 `-arch sm_86` |
| `filesystem is ambiguous` | C++17 命名空间冲突（std vs boost） | 执行 4b 修复 |
| `petscvec.h` not found | CMake 缺 PETSc 包含路径 | 执行第 5 步 cmake 配置 |
| `Eigen/Dense` not found | Mutation++ 缺 Eigen 路径 | 执行 4d 修复 + 第 5 步 cmake |
| `extended character is not valid in an identifier` | 源文件含不可见 Unicode U+00A0 | 用普通空格替换 U+00A0 |
| `type name is not allowed` in `.cu` file | nvcc C++17 模板解析 | 执行 4e 修复 |
| `throw()` dynamic exception specification | C++17 已移除该语法 | 执行 4a 修复 |
| `PCSACUSP` was not declared | PETSc 3.13+ 移除 CUDA 预条件器 | 执行 4c 修复 |
| `malloc_info` / `mallinfo` deprecated | 系统 API 变更 | 非致命警告，可忽略 |
| `auto_ptr` is deprecated | C++17 已移除 `std::auto_ptr` | 需重构为 `unique_ptr`，工作量较大 |
| destructor `throw()` always calls `terminate` | C++11 起析构函数默认为 noexcept | 非致命警告，可忽略 |

---

## 完整命令速查

```bash
# === 1. 环境 ===
source ~/.bashrc

# === 2. 配置 ===
cd ~/packages/COOLFluiD
# 编辑 coolfluid.conf（见第 2 步模板）

# === 3. 构建初始化 ===
./prepare.pl --build=optim

# === 4. 源码修复 ===
# 推荐使用 tools/ 下的修复脚本：
bash tools/apply_all_fixes.sh

# === 5. CMake 补全 ===
cd build/optim
cmake -DCF_CUDAC_FLAGS="--std c++17 -arch sm_86" \
      -DCMAKE_CUDA_FLAGS="--std c++17 -arch sm_86" \
      -DEIGEN3_INCLUDE_DIR=/usr/include/eigen3 \
      .

# === 6. 编译 ===
make -j$(nproc) 2>&1 | tee build.log

# === 7. 安装 ===
make install
```
