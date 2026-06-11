#!/bin/bash
# ============================================================
# fix_compile_issues.sh
# COOLFluiD 编译兼容性修复：处理 C++17 迁移引发的其他源码问题
#
# 使用方法：在 COOLFluiD 根目录执行
#   bash tools/fix_compile_issues.sh
# ============================================================

set -e
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

echo "========================================"
echo "编译兼容性修复"
echo "========================================"

# ============================================================
# Fix 1: apps/Solver/coolfluid-solver.cxx
# C++17 下 std::filesystem 与 boost::filesystem 命名冲突
# 修复：添加 namespace fs = boost::filesystem; 并将 filesystem:: 替换为 fs::
# ============================================================
echo ""
echo "[1/4] apps/Solver - filesystem 命名冲突 ..."
SOLVER_FILE="apps/Solver/coolfluid-solver.cxx"
if [ -f "$SOLVER_FILE" ]; then
  # 在 "using namespace boost;" 下方添加 namespace fs = boost::filesystem;
  sed -i '/using namespace boost;/a\  namespace fs = boost::filesystem;' "$SOLVER_FILE"
  # 将 standalone 的 filesystem:: 替换为 fs::
  sed -i 's/boost::filesystem::/fs::/g' "$SOLVER_FILE"
  sed -i 's/\bfilesystem::/fs::/g'       "$SOLVER_FILE"
  echo "  [OK] $SOLVER_FILE"
else
  echo "  [SKIP] $SOLVER_FILE 不存在"
fi

# ============================================================
# Fix 2: plugins/Petsc/PetscOptions.cxx
# PETSc 3.13+ 移除了 CUDA 预条件器常量
# 修复：版本检查条件改为 PETSC_VERSION_MINOR>=13 时跳过
# ============================================================
echo ""
echo "[2/4] Petsc - CUDA 预条件器版本检查 ..."
PETSCOPT_FILE="plugins/Petsc/PetscOptions.cxx"
if [ -f "$PETSCOPT_FILE" ]; then
  # 替换版本检查条件
  sed -i 's/#if PETSC_VERSION_MINOR!=9 && PETSC_VERSION_MINOR!=11 && PETSC_VERSION_MINOR!=12/#if PETSC_VERSION_MINOR>=13/' "$PETSCOPT_FILE"
  # 在 PETSC_VERSION_MINOR>=13 分支中添加注释
  sed -i '/#if PETSC_VERSION_MINOR>=13/a\  \/\/ PCSACUSP and friends were removed starting from PETSc 3.13' "$PETSCOPT_FILE"
  echo "  [OK] $PETSCOPT_FILE"
else
  echo "  [SKIP] $PETSCOPT_FILE 不存在"
fi

# ============================================================
# Fix 3: plugins/MutationppI/CMakeLists.txt
# Mutation++ 依赖 Eigen3，但 CMakeLists.txt 未包含路径
# 修复：在 MUTATIONPP_INCLUDE_DIR 之后添加 EIGEN3_INCLUDE_DIR
# ============================================================
echo ""
echo "[3/4] MutationppI - 添加 Eigen3 包含路径 ..."
MUTPP_CMAKE="plugins/MutationppI/CMakeLists.txt"
if [ -f "$MUTPP_CMAKE" ]; then
  # 检查是否已有 Eigen3 路径，如没有则添加
  if grep -q "EIGEN3_INCLUDE_DIR" "$MUTPP_CMAKE"; then
    echo "  [OK] 已有 Eigen3 路径，跳过"
  else
    sed -i '/LIST ( APPEND MutationppI_includedirs ${MUTATIONPP_INCLUDE_DIR} )/a\LIST ( APPEND MutationppI_includedirs ${EIGEN3_INCLUDE_DIR} )' "$MUTPP_CMAKE"
    echo "  [OK] $MUTPP_CMAKE"
  fi
else
  echo "  [SKIP] $MUTPP_CMAKE 不存在"
fi

# ============================================================
# Fix 4: plugins/FiniteVolumeCUDA/FVMCC_ComputeRHSCell.cu
# nvcc + C++17 对从属模板名称要求使用 template 关键字
# 修复：d_castTo<SCHEME>() 改为 .template d_castTo<SCHEME>()
# ============================================================
echo ""
echo "[4/4] FiniteVolumeCUDA - template 关键字修复 ..."
CUDA_FILE="plugins/FiniteVolumeCUDA/FVMCC_ComputeRHSCell.cu"
if [ -f "$CUDA_FILE" ]; then
  # 替换 .d_castTo< 为 .template d_castTo<
  sed -i 's/\.d_castTo</.template d_castTo</g' "$CUDA_FILE"
  echo "  [OK] $CUDA_FILE"
else
  echo "  [SKIP] $CUDA_FILE 不存在"
fi

echo ""
echo "========================================"
echo "所有编译兼容性修复已完成"
echo ""
echo "后续步骤："
echo "  1. cd build/optim"
echo "  2. cmake -DCF_CUDAC_FLAGS=\"--std c++17 -arch sm_86\" \\"
echo "           -DCMAKE_CUDA_FLAGS=\"--std c++17 -arch sm_86\" \\"
echo "           -DEIGEN3_INCLUDE_DIR=/usr/include/eigen3 ."
echo "  3. make -j\$(nproc) 2>&1 | tee build.log"
echo "  4. make install"
echo "========================================"
