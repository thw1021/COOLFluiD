#!/bin/bash
# ============================================================
# apply_all_fixes.sh
# COOLFluiD 源码一键修复脚本
# 依次执行所有兼容性修复，适用于从原始源码开始的全新安装
#
# 使用方法：在 COOLFluiD 根目录执行
#   bash tools/apply_all_fixes.sh
# ============================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "========================================"
echo "COOLFluiD 源码一键修复"
echo "========================================"
echo ""

# 步骤 1：移除 throw() 动态异常规范
echo ">>> [1/2] 移除 throw() 动态异常规范 ..."
bash tools/fix_exception_specs.sh
echo ""

# 步骤 2：其他编译兼容性修复
echo ">>> [2/2] 编译兼容性修复 ..."
bash tools/fix_compile_issues.sh
echo ""

echo "========================================"
echo "所有源码修复已完成！"
echo "========================================"
echo ""
echo "后续构建步骤："
echo "  cd build/optim"
echo "  cmake -DCF_CUDAC_FLAGS=\"--std c++17 -arch sm_86\" \\"
echo "        -DCMAKE_CUDA_FLAGS=\"--std c++17 -arch sm_86\" \\"
echo "        -DEIGEN3_INCLUDE_DIR=/usr/include/eigen3 ."
echo "  make -j\$(nproc) 2>&1 | tee build.log"
echo "  make install"
echo ""
