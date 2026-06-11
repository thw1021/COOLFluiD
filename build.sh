#!/bin/bash
# ============================================================
# build.sh
# COOLFluiD 一键构建脚本
# 功能：配置 → 编译 → 安装 → 清理中间产物 → 日志记录
#
# 使用方法：
#   ./build.sh [并行核数]
#   默认为 14 核（适用于 14 核 CPU）
#
# 日志输出：
#   build/optim/build_<时间戳>.log   — 完整的构建日志
#   build/optim/cleanup_<时间戳>.log — 中间产物清理记录
# ============================================================

# --- 配置参数 ---
NPROC=${1:-14}
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$ROOT_DIR/build/optim"
INSTALL_DIR="$ROOT_DIR/install"
CONF_FILE="$ROOT_DIR/coolfluid.conf"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BUILD_LOG="$BUILD_DIR/build_${TIMESTAMP}.log"
CLEANUP_LOG="$BUILD_DIR/cleanup_${TIMESTAMP}.log"

# 确保日志目录存在
mkdir -p "$BUILD_DIR"

# 初始化构建日志
{
    echo "========================================"
    echo "COOLFluiD 构建开始"
    echo "时间: $(date)"
    echo "工作目录: $ROOT_DIR"
    echo "构建目录: $BUILD_DIR"
    echo "安装目录: $INSTALL_DIR"
    echo "并行核数: $NPROC"
    echo "构建日志: $BUILD_LOG"
    echo "========================================"
    echo ""
} | tee "$BUILD_LOG"

# 加载用户环境
source ~/.bashrc 2>/dev/null || true
cd "$ROOT_DIR"

# 检查 coolfluid.conf
if [ ! -f "$CONF_FILE" ]; then
    echo "[ERROR] 未找到 $CONF_FILE" | tee -a "$BUILD_LOG"
    echo "请先创建配置文件（可参考 tools/conf/ 下的示例）" | tee -a "$BUILD_LOG"
    exit 1
fi

# ===========================================
# 步骤 1/5：运行 prepare.pl 配置构建
# ===========================================
echo "[1/5] 运行 prepare.pl 配置构建 ..." | tee -a "$BUILD_LOG"
if ./prepare.pl --build=optim >> "$BUILD_LOG" 2>&1; then
    echo "  [OK] prepare.pl 配置完成" | tee -a "$BUILD_LOG"
else
    echo "  [FAIL] prepare.pl 失败，退出码: $?" | tee -a "$BUILD_LOG"
    exit 1
fi
echo "" | tee -a "$BUILD_LOG"

# ===========================================
# 步骤 2/5：更新 CMake CUDA 编译标志
# ===========================================
echo "[2/5] 更新 CMake CUDA 编译标志 ..." | tee -a "$BUILD_LOG"
cd "$BUILD_DIR"

cmake -DCF_CUDAC_FLAGS="--std c++17 -arch sm_86" \
      -DCMAKE_CUDA_FLAGS="--std c++17 -arch sm_86" \
      -DEIGEN3_INCLUDE_DIR=/usr/include/eigen3 \
      . >> "$BUILD_LOG" 2>&1

if [ $? -eq 0 ]; then
    echo "  [OK] CMake 配置更新完成" | tee -a "$BUILD_LOG"
    echo "       CF_CUDAC_FLAGS  = --std c++17 -arch sm_86" | tee -a "$BUILD_LOG"
    echo "       CMAKE_CUDA_FLAGS = --std c++17 -arch sm_86" | tee -a "$BUILD_LOG"
    echo "       EIGEN3_INCLUDE   = /usr/include/eigen3" | tee -a "$BUILD_LOG"
else
    echo "  [FAIL] CMake 配置更新失败" | tee -a "$BUILD_LOG"
    exit 1
fi
echo "" | tee -a "$BUILD_LOG"

# ===========================================
# 步骤 3/5：编译
# ===========================================
echo "[3/5] 编译 (make -j${NPROC}) ..." | tee -a "$BUILD_LOG"
START_TIME=$(date +%s)

if make -j"$NPROC" >> "$BUILD_LOG" 2>&1; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    echo "  [OK] 编译完成，耗时 ${DURATION} 秒" | tee -a "$BUILD_LOG"
else
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    echo "  [FAIL] 编译失败（耗时 ${DURATION} 秒）" | tee -a "$BUILD_LOG"
    echo "  查看详细错误: tail -100 $BUILD_LOG" | tee -a "$BUILD_LOG"
    exit 1
fi
echo "" | tee -a "$BUILD_LOG"

# ===========================================
# 步骤 4/5：安装
# ===========================================
echo "[4/5] 安装 (make install) ..." | tee -a "$BUILD_LOG"
if make install >> "$BUILD_LOG" 2>&1; then
    echo "  [OK] 安装完成" | tee -a "$BUILD_LOG"
    echo "       安装路径: $INSTALL_DIR" | tee -a "$BUILD_LOG"
    echo "       可执行文件: $INSTALL_DIR/bin/coolfluid-solver" | tee -a "$BUILD_LOG"
else
    echo "  [FAIL] 安装失败" | tee -a "$BUILD_LOG"
    exit 1
fi
echo "" | tee -a "$BUILD_LOG"

# ===========================================
# 步骤 5/5：清理中间产物并记录日志
# ===========================================
echo "[5/5] 清理中间产物 ..." | tee -a "$BUILD_LOG"
cd "$ROOT_DIR"

# --- 定义中间产物列表 ---
# 这些 .cu 文件由 CMake 的 EXECUTE_PROCESS(COMMAND cp ...) 在配置阶段从 .cxx 复制生成
# 仅用于 nvcc 编译，不是原始仓库文件，编译完成后无需保留
AUTO_GEN_FILES=(
    "plugins/FiniteVolume/LaxFriedFlux.cu"
    "plugins/FluxReconstructionMethod/LaxFriedrichsFlux.cu"
)

# --- 生成清理日志 ---
{
    echo "========================================"
    echo "COOLFluiD 中间产物清理记录"
    echo "时间: $(date)"
    echo "构建: build_${TIMESTAMP}.log"
    echo "说明: 以下文件是 CMake 构建阶段从 .cxx 自动复制生成的 .cu 文件"
    echo "      内容与源 .cxx 完全一致，编译完成后无需保留"
    echo "      下次 cmake 重新配置时会自动重新生成"
    echo "========================================"
    echo ""
    echo "清理文件清单:"
    echo "----------------------------------------"
} > "$CLEANUP_LOG"

DELETED_COUNT=0
TOTAL_SIZE=0

for file in "${AUTO_GEN_FILES[@]}"; do
    if [ -f "$file" ]; then
        cxx_file="${file%.cu}.cxx"
        if [ -f "$cxx_file" ]; then
            FILE_SIZE=$(stat --format=%s "$file" 2>/dev/null || echo 0)
            rm -f "$file"
            echo "  [DELETED] $file" >> "$CLEANUP_LOG"
            echo "     大小: ${FILE_SIZE} bytes" >> "$CLEANUP_LOG"
            echo "     对应源文件: $cxx_file" >> "$CLEANUP_LOG"
            DELETED_COUNT=$((DELETED_COUNT + 1))
            TOTAL_SIZE=$((TOTAL_SIZE + FILE_SIZE))
        else
            echo "  [SKIPPED] $file (未找到源文件 $cxx_file，保留)" >> "$CLEANUP_LOG"
        fi
    else
        echo "  [NOT FOUND] $file (不存在，无需清理)" >> "$CLEANUP_LOG"
    fi
done

{
    echo ""
    echo "----------------------------------------"
    echo "清理摘要:"
    echo "  删除文件数: $DELETED_COUNT"
    echo "  释放空间: ${TOTAL_SIZE} bytes ($((TOTAL_SIZE / 1024)) KB)"
    echo "  清理日志: $CLEANUP_LOG"
    echo "----------------------------------------"
} >> "$CLEANUP_LOG"

# 将清理日志附加到构建日志
cat "$CLEANUP_LOG" >> "$BUILD_LOG"

# 移除旧的日志链接，创建最新日志链接
ln -sf "build_${TIMESTAMP}.log" "$BUILD_DIR/build.latest.log"
ln -sf "cleanup_${TIMESTAMP}.log" "$BUILD_DIR/cleanup.latest.log"

echo "  [OK] 中间产物清理完成，删除 ${DELETED_COUNT} 个文件" | tee -a "$BUILD_LOG"
echo "  [OK] 清理日志: $CLEANUP_LOG" | tee -a "$BUILD_LOG"
echo "" | tee -a "$BUILD_LOG"

# ===========================================
# 构建完成
# ===========================================
{
    echo ""
    echo "========================================"
    echo "COOLFluiD 构建完成"
    echo "时间: $(date)"
    echo "安装目录: $INSTALL_DIR"
    echo "可执行文件: $INSTALL_DIR/bin/coolfluid-solver"
    echo ""
    echo "生成的文件清单:"
    echo "  构建日志: $BUILD_LOG"
    echo "  清理日志: $CLEANUP_LOG"
    echo "  最新日志: $BUILD_DIR/build.latest.log"
    echo "========================================"
    echo ""
    echo "快速查看构建日志:"
    echo "  tail -50 $BUILD_DIR/build.latest.log"
    echo ""
} | tee -a "$BUILD_LOG"
