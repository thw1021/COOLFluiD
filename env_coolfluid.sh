#!/bin/bash
# ============================================================
# env_coolfluid.sh
# COOLFluiD 运行环境配置脚本
#
# 功能：加载 COOLFluiD 及其全部依赖的运行时环境变量
#       （PATH / LD_LIBRARY_PATH / 各依赖 *_DIR 变量）
#
# 使用方法（不可直接执行，必须用 source 加载）：
#   source /home/tang/packages/COOLFluiD/env_coolfluid.sh
#
# 或加入 ~/.bashrc 自动加载：
#   echo 'source /home/tang/packages/COOLFluiD/env_coolfluid.sh' >> ~/.bashrc
#
# 关键路径（按当前机器预设，迁移到其他机器请修改下方 CONFIG 段）：
#   COOLFluiD 安装 : /home/tang/packages/COOLFluiD/install
#   CUDA           : /usr/local/cuda-12.2
#   MPICH          : /home/tang/packages/mpichInstall
#   Boost          : /home/tang/packages/boost_1_85_0/install
#   PETSc          : /home/tang/packages/petsc (arch-linux-c-opt)
#   Mutation++     : /home/tang/packages/Mutationpp/install
#   Eigen3 头文件  : /usr/include/eigen3
# ============================================================

# 防止被直接执行（必须 source）
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    echo "[ERROR] 此脚本必须用 source 加载，不能直接执行。"
    echo "        用法：source $0"
    exit 1
fi

# ============================================================
# CONFIG 段：所有依赖路径集中于此
# ============================================================

# --- COOLFluiD 自身 ---
export COOLFLUID_HOME="/home/tang/packages/COOLFluiD"
export COOLFLUID_INSTALL="${COOLFLUID_HOME}/install"
# COOLFluiD 求解器加载模块的目录（case 文件中 Simulator.Paths.ModulesDir 应指向此处）
export COOLFLUID_MODULES_DIR="${COOLFLUID_INSTALL}/lib"

# --- CUDA ---
export CUDA_DIR="/usr/local/cuda-12.2"
export CUDA_HOME="${CUDA_DIR}"

# --- MPICH ---
export MPICH_DIR="/home/tang/packages/mpichInstall"

# --- Boost ---
export BOOST_DIR="/home/tang/packages/boost_1_85_0/install"

# --- PETSc ---
export PETSC_DIR="/home/tang/packages/petsc"
export PETSC_ARCH="arch-linux-c-opt"

# --- Mutation++ ---
export MPP_DIRECTORY="/home/tang/packages/Mutationpp"
export MUTATIONPP_DIR="/home/tang/packages/Mutationpp/install"
# Mutation++ 的 data 目录在源码根下（install 仅含 bin/include/lib）
export MUTATIONPP_DATA_DIR="${MPP_DIRECTORY}/data"

# --- Eigen3 ---
export EIGEN3_INCLUDE_DIR="/usr/include/eigen3"

# --- ParMETIS / METIS（与 MPICH 同目录）---
export METIS_DIR="${MPICH_DIR}"
export PARMETIS_DIR="${MPICH_DIR}"

# ============================================================
# PATH 配置（依赖优先级：COOLFluiD → CUDA → MPICH → PETSc → Mutation++）
# 使用 prepend 保证自定义版本优先于系统版本
# ============================================================
_prepend_path() {
    # 仅当目录存在时才加入，避免无效路径
    local dir="$1"
    if [ -d "$dir" ]; then
        case ":${PATH:-}:" in
            *":${dir}:"*) ;;           # 已存在，跳过
            *) PATH="${dir}:${PATH:-}" ;;
        esac
    fi
}

_prepend_ld() {
    local dir="$1"
    if [ -d "$dir" ]; then
        case ":${LD_LIBRARY_PATH:-}:" in
            *":${dir}:"*) ;;
            *) LD_LIBRARY_PATH="${dir}:${LD_LIBRARY_PATH:-}" ;;
        esac
    fi
}

# --- COOLFluiD 可执行文件与库 ---
_prepend_path  "${COOLFLUID_INSTALL}/bin"
_prepend_ld    "${COOLFLUID_INSTALL}/lib"

# --- CUDA ---
_prepend_path  "${CUDA_DIR}/bin"
_prepend_ld    "${CUDA_DIR}/lib64"

# --- MPICH ---
_prepend_path  "${MPICH_DIR}/bin"
_prepend_ld    "${MPICH_DIR}/lib"

# --- PETSc（架构子目录含可执行与库）---
_prepend_path  "${PETSC_DIR}/${PETSC_ARCH}/bin"
_prepend_ld    "${PETSC_DIR}/${PETSC_ARCH}/lib"
_prepend_ld    "${PETSC_DIR}/lib"

# --- Mutation++ ---
_prepend_path  "${MUTATIONPP_DIR}/bin"
_prepend_ld    "${MUTATIONPP_DIR}/lib"
# 同时保留源码根目录路径（部分脚本位于 MPP_DIRECTORY 而非 install）
_prepend_path  "${MPP_DIRECTORY}/install/bin"

# --- Boost 库 ---
_prepend_ld    "${BOOST_DIR}/lib"

# --- Eigen3 头文件（供 C++ 编译时使用，加入 CPATH / CPLUS_INCLUDE_PATH）---
if [ -d "${EIGEN3_INCLUDE_DIR}" ]; then
    export CPATH="${EIGEN3_INCLUDE_DIR}:${CPATH:-}"
    export CPLUS_INCLUDE_PATH="${EIGEN3_INCLUDE_DIR}:${CPLUS_INCLUDE_PATH:-}"
    export C_INCLUDE_PATH="${EIGEN3_INCLUDE_DIR}:${C_INCLUDE_PATH:-}"
fi

# --- 导出 PATH / LD_LIBRARY_PATH ---
export PATH
export LD_LIBRARY_PATH

# ============================================================
# Python 扩展（如安装了 COOLFluiD Python 绑定或后处理脚本）
# ============================================================
if [ -d "${COOLFLUID_HOME}/tools/scripts" ]; then
    case ":${PYTHONPATH:-}:" in
        *":${COOLFLUID_HOME}/tools/scripts:"*) ;;
        *) export PYTHONPATH="${COOLFLUID_HOME}/tools/scripts:${PYTHONPATH:-}" ;;
    esac
fi

# ============================================================
# 求解器运行辅助变量
# ============================================================
# OMP_NUM_THREADS：单节点 OpenMP 线程数（COOLFluiD 主要用 MPI 并行，
# OpenMP 用于部分 BLAS 调用；默认 1 以避免与 MPI 线程冲突）
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-1}

# CUDA 可见设备（如需限制 GPU，可在调用前覆盖）
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}

# ============================================================
# 提示信息（每次加载时显示当前环境概览）
# ============================================================
echo "[COOLFluiD env] 环境已加载"
echo "  COOLFLUID_HOME       = ${COOLFLUID_HOME}"
echo "  COOLFLUID_INSTALL    = ${COOLFLUID_INSTALL}"
echo "  COOLFLUID_MODULES_DIR= ${COOLFLUID_MODULES_DIR}"
echo "  CUDA_DIR             = ${CUDA_DIR}"
echo "  MPICH_DIR            = ${MPICH_DIR}"
echo "  PETSC_DIR            = ${PETSC_DIR} (${PETSC_ARCH})"
echo "  MUTATIONPP_DIR       = ${MUTATIONPP_DIR}"
echo "  EIGEN3_INCLUDE_DIR   = ${EIGEN3_INCLUDE_DIR}"
echo "  使用："
echo "    coolfluid-solver --help"
echo "    mpirun -np <N> coolfluid-solver --case <case.CFcase>"

# 清理临时函数，避免污染环境
unset -f _prepend_path _prepend_ld

