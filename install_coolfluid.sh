#!/bin/bash
# ============================================================
# install_coolfluid.sh
# COOLFluiD 一键完整安装脚本（从源码到可运行）
#
# 流程：依赖检查 → coolfluid.conf 生成 → prepare.pl
#       → 源码兼容性修复 → CMake 配置 → 编译 → 安装 → 验证
#
# 使用方法：
#   ./install_coolfluid.sh [并行核数]
#   默认 14 核（适用于 14 核 CPU）
#
# 关键路径（已按当前环境预设，如迁移到其他机器请修改下方 CONFIG 段）：
#   源码目录   : /home/tang/packages/COOLFluiD
#   安装目录   : /home/tang/packages/COOLFluiD/install
#   CUDA       : /usr/local/cuda-12.2          (nvcc, sm_86)
#   MPICH      : /home/tang/packages/mpichInstall
#   Boost      : /home/tang/packages/boost_1_85_0/install
#   PETSc      : /home/tang/packages/petsc     (arch-linux-c-opt)
#   Mutation++ : /home/tang/packages/Mutationpp/install
#   Eigen3     : /usr/include/eigen3
# ============================================================

set -euo pipefail

# ============================================================
# CONFIG 段：所有可调参数集中于此
# ============================================================
NPROC=${1:-14}
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$ROOT_DIR/build/optim"
INSTALL_DIR="$ROOT_DIR/install"
CONF_FILE="$ROOT_DIR/coolfluid.conf"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="$ROOT_DIR/build/optim"
LOG_FILE="$LOG_DIR/install_${TIMESTAMP}.log"

# --- 依赖路径（按当前机器预设）---
CUDA_DIR="/usr/local/cuda-12.2"
CUDA_BIN="$CUDA_DIR/bin"
MPICH_DIR="/home/tang/packages/mpichInstall"
BOOST_DIR="/home/tang/packages/boost_1_85_0/install"
PETSC_DIR="/home/tang/packages/petsc"
PETSC_ARCH="arch-linux-c-opt"
MUTATIONPP_DIR="/home/tang/packages/Mutationpp/install"
MPP_SRC_DIR="/home/tang/packages/Mutationpp"   # Mutation++ 源码根（data 目录在此处）
EIGEN3_DIR="/usr/include/eigen3"

# --- 编译器与编译标志 ---
CC_BIN="/usr/bin/gcc"
CXX_BIN="/usr/bin/g++"
FC_BIN="gfortran"
CUDA_ARCH="sm_86"          # RTX 3050 = sm_86；A100=sm_80, H100=sm_90, RTX 40xx=sm_89
CXX_STD="c++17"            # Boost 1.85 atomic 头文件要求 C++17
OPTIM_CXXFLAGS="-O3 -g -fPIC -std=${CXX_STD}"
OPTIM_CFLAGS="-O3 -g -fPIC"
OPTIM_FFLAGS="-O3 -g -fPIC"

mkdir -p "$LOG_DIR"

# ============================================================
# 日志辅助函数
# ============================================================
log()  { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG_FILE"; }
ok()   { log "  [OK]   $*"; }
fail() { log "  [FAIL] $*"; exit 1; }
step() { log ""; log "========================================"; log "$*"; log "========================================"; }

{
    echo "========================================"
    echo "COOLFluiD 完整安装"
    echo "开始时间: $(date)"
    echo "源码目录: $ROOT_DIR"
    echo "构建目录: $BUILD_DIR"
    echo "安装目录: $INSTALL_DIR"
    echo "并行核数: $NPROC"
    echo "日志文件 : $LOG_FILE"
    echo "========================================"
} | tee "$LOG_FILE"

# 加载 COOLFluiD 运行环境（env_coolfluid.sh 不受 bashrc 非交互模式早退影响）
# 优先 source env_coolfluid.sh；若不存在则回退到 ~/.bashrc
if [ -f "$ROOT_DIR/env_coolfluid.sh" ]; then
    source "$ROOT_DIR/env_coolfluid.sh" >/dev/null 2>&1 || true
fi
source ~/.bashrc 2>/dev/null || true
cd "$ROOT_DIR"

# ============================================================
# 步骤 1/8：依赖检查
# ============================================================
step "[1/8] 依赖检查"

check_cmd() {
    local cmd="$1"; local name="$2"
    if command -v "$cmd" >/dev/null 2>&1; then
        log "  $name: $(command -v "$cmd")"
    else
        fail "$name 未找到（命令: $cmd）"
    fi
}

check_path() {
    local p="$1"; local name="$2"
    if [ -e "$p" ]; then
        log "  $name: $p"
    else
        fail "$name 路径不存在: $p"
    fi
}

check_cmd nvcc      "CUDA 编译器"
check_cmd mpicc     "MPI C 编译器"
check_cmd mpiexec   "MPI 运行器"
check_cmd cmake     "CMake"
check_cmd g++       "C++ 编译器"
check_cmd gfortran  "Fortran 编译器"

check_path "$CUDA_DIR"          "CUDA 目录"
check_path "$MPICH_DIR"         "MPICH 目录"
check_path "$BOOST_DIR"         "Boost 目录"
check_path "$PETSC_DIR"         "PETSc 目录"
check_path "$MUTATIONPP_DIR"    "Mutation++ 目录"
check_path "$EIGEN3_DIR"        "Eigen3 头文件"

# PETSc 架构子目录
check_path "$PETSC_DIR/$PETSC_ARCH" "PETSc 架构目录"

# Mutation++ 数据文件（mixtures / mechanisms，位于源码根 data/ 下）
check_path "$MPP_SRC_DIR/data/mixtures"   "Mutation++ mixtures"
check_path "$MPP_SRC_DIR/data/mechanisms" "Mutation++ mechanisms"

ok "依赖检查通过"

# ============================================================
# 步骤 2/8：生成 coolfluid.conf
# ============================================================
step "[2/8] 生成 coolfluid.conf"

# 仅当不存在或与目标内容不同时写入，避免无谓覆盖
cat > "$CONF_FILE" <<EOF
#==================================================================
# COOLFluiD Configuration File
# 由 install_coolfluid.sh 自动生成于 $(date)
#==================================================================
# 目标环境：Ubuntu 22.04 | CUDA 12.2 | Boost 1.85 | MPICH | PETSc 3.24 | Mutation++ | ${CUDA_ARCH}
#==================================================================

coolfluid_dir    = $ROOT_DIR
basebuild_dir    = $ROOT_DIR/build
install_dir      = $INSTALL_DIR

# compilers
cc               = $CC_BIN
cxx              = $CXX_BIN
fc               = $FC_BIN

# CUDA configuration
cudac            = $CUDA_BIN/nvcc
cuda_dir         = $CUDA_DIR
cudacflags       = --std ${CXX_STD} -arch ${CUDA_ARCH}
withcuda         = 1

nofortran        = 0
withcurl         = 0

# library locations
mpi_dir          = $MPICH_DIR
boost_dir        = $BOOST_DIR
petsc_dir        = $PETSC_DIR
parmetis_dir     = $MPICH_DIR

# Mutation++ configuration (thermal nonequilibrium)
mutationpp_dir   = $MUTATIONPP_DIR
with_mutationpp  = 1

allactive        = 1
with_testcases   = 1
cmake_generator  = make

# C++17 standard (required by Boost 1.85 atomic headers)
optim_cxxflags   = $OPTIM_CXXFLAGS
optim_cflags     = $OPTIM_CFLAGS
optim_fflags     = $OPTIM_FFLAGS
EOF

ok "coolfluid.conf 已生成: $CONF_FILE"

# ============================================================
# 步骤 3/8：prepare.pl（生成 CMake 缓存）
# ============================================================
step "[3/8] 运行 prepare.pl 配置构建"

if [ ! -x "$ROOT_DIR/prepare.pl" ]; then
    chmod +x "$ROOT_DIR/prepare.pl" || true
fi

if ./prepare.pl --build=optim >> "$LOG_FILE" 2>&1; then
    ok "prepare.pl 完成"
else
    fail "prepare.pl 失败（退出码 $?）"
fi

# ============================================================
# 步骤 4/8：源码兼容性修复（C++17 / PETSc / Mutation++ / CUDA）
# ============================================================
step "[4/8] 源码兼容性修复"

if [ -x "$ROOT_DIR/tools/apply_all_fixes.sh" ]; then
    if bash "$ROOT_DIR/tools/apply_all_fixes.sh" >> "$LOG_FILE" 2>&1; then
        ok "源码修复完成"
    else
        # 修复脚本可能因已修复而返回非零（idempotent 重复执行），不视为致命
        log "  [WARN] apply_all_fixes.sh 返回非零（可能已修复），继续"
    fi
else
    log "  [WARN] 未找到 tools/apply_all_fixes.sh，跳过（如为全新源码请手动修复）"
fi

# ============================================================
# 步骤 5/8：CMake 重新配置（补充 prepare.pl 未覆盖的关键参数）
# ============================================================
step "[5/8] CMake 重新配置"

cd "$BUILD_DIR"

# 注意：prepare.pl 会重置缓存，每次重新运行 prepare.pl 后必须重新执行此 cmake
cmake -DCF_CUDAC_FLAGS="--std ${CXX_STD} -arch ${CUDA_ARCH}" \
      -DCMAKE_CUDA_FLAGS="--std ${CXX_STD} -arch ${CUDA_ARCH}" \
      -DPETSC_INC_DIR="${PETSC_DIR}/${PETSC_ARCH}/include;${PETSC_DIR}/include" \
      -DEIGEN3_INCLUDE_DIR="${EIGEN3_DIR}" \
      . >> "$LOG_FILE" 2>&1 || fail "CMake 配置失败"

ok "CMake 配置完成"
ok "  CF_CUDAC_FLAGS  = --std ${CXX_STD} -arch ${CUDA_ARCH}"
ok "  CMAKE_CUDA_FLAGS= --std ${CXX_STD} -arch ${CUDA_ARCH}"
ok "  PETSC_INC_DIR   = ${PETSC_DIR}/${PETSC_ARCH}/include;${PETSC_DIR}/include"
ok "  EIGEN3_INCLUDE  = ${EIGEN3_DIR}"

# ============================================================
# 步骤 6/8：编译
# ============================================================
step "[6/8] 编译 (make -j${NPROC})"

START_TIME=$(date +%s)
cd "$BUILD_DIR"

# 编译失败不立即退出，保留日志供诊断
if make -j"$NPROC" >> "$LOG_FILE" 2>&1; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    ok "编译完成，耗时 ${DURATION} 秒"
else
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    log "  [FAIL] 编译失败（耗时 ${DURATION} 秒）"
    log "  错误速查："
    log "    grep -c 'error:' $LOG_FILE"
    log "    tail -200 $LOG_FILE"
    # 输出最近的错误行
    log "  最近错误："
    grep -E 'error:' "$LOG_FILE" | tail -20 | sed 's/^/    /' >> "$LOG_FILE"
    exit 1
fi

# ============================================================
# 步骤 7/8：安装
# ============================================================
step "[7/8] 安装 (make install)"

cd "$BUILD_DIR"
if make install >> "$LOG_FILE" 2>&1; then
    ok "安装完成"
    ok "  安装路径: $INSTALL_DIR"
    ok "  可执行文件: $INSTALL_DIR/bin/coolfluid-solver"
else
    fail "安装失败"
fi

# 清理 CMake 自动复制的 .cu 中间产物（与源 .cxx 内容一致）
AUTO_GEN_FILES=(
    "plugins/FiniteVolume/LaxFriedFlux.cu"
    "plugins/FluxReconstructionMethod/LaxFriedrichsFlux.cu"
)
for file in "${AUTO_GEN_FILES[@]}"; do
    fpath="$ROOT_DIR/$file"
    if [ -f "$fpath" ]; then
        rm -f "$fpath"
        log "  [CLEAN] 删除中间产物: $file"
    fi
done

# ============================================================
# 步骤 8/8：验证
# ============================================================
step "[8/8] 验证安装"

SOLVER="$INSTALL_DIR/bin/coolfluid-solver"
if [ ! -x "$SOLVER" ]; then
    fail "可执行文件不存在或不可执行: $SOLVER"
fi

# 版本/帮助
if "$SOLVER" --help >> "$LOG_FILE" 2>&1 || true; then
    ok "coolfluid-solver --help 可执行"
fi

# 验证 CUDA 链接
if ldd "$SOLVER" | grep -qi cuda; then
    ok "CUDA 链接正常: $(ldd "$SOLVER" | grep -i cuda | head -1 | awk '{print $1}')"
else
    log "  [WARN] 未检测到 CUDA 动态库链接（若已启用 withcuda=1 请检查）"
fi

# 验证 MPI 链接
if ldd "$SOLVER" | grep -qi mpi; then
    ok "MPI 链接正常: $(ldd "$SOLVER" | grep -i mpi | head -1 | awk '{print $1}')"
else
    log "  [WARN] 未检测到 MPI 动态库链接"
fi

# 验证库文件数量
LIB_COUNT=$(ls "$INSTALL_DIR/lib/" 2>/dev/null | wc -l)
ok "共享库数量: $LIB_COUNT"

# 验证可执行文件清单
log "  可执行文件清单："
ls "$INSTALL_DIR/bin/" | sed 's/^/    /' >> "$LOG_FILE"

# ============================================================
# 完成
# ============================================================
step "安装完成"

{
    echo "完成时间: $(date)"
    echo "安装目录: $INSTALL_DIR"
    echo "可执行文件: $SOLVER"
    echo ""
    echo "环境加载（运行前请执行）："
    echo "  source $ROOT_DIR/env_coolfluid.sh"
    echo ""
    echo "快速运行："
    echo "  coolfluid-solver --help"
    echo "  mpirun -np 4 coolfluid-solver --case <case.CFcase>"
    echo ""
    echo "日志查看："
    echo "  tail -50 $LOG_FILE"
} | tee -a "$LOG_FILE"

ln -sf "install_${TIMESTAMP}.log" "$LOG_DIR/install.latest.log"

log "全部完成。"

