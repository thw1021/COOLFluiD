#!/bin/bash
# ============================================================
# init_testcases.sh
# 原用途：解压测试算例的大文件 (.xz -> .dat / .CFmesh)
#
# 当前状态：已禁用 (no-op)
# ------------------------------------------------------------
# 原因：
#   * 解压后会在 git 工作区产生 1500+ 文件变更（740 个 .xz
#     被删 + 740+ 个解压产物），导致 git 提交缓慢、仓库膨胀
#     约 6.6 GB。
#   * 这些 .dat / .CFmesh 仅作为 cf_add_case 注册的算例输入
#     数据使用，并非编译 coolfluid-solver 或其库的依赖，对
#     编译结果无影响（CMakeLists.txt 中没有任何 ADD_LIBRARY /
#     ADD_EXECUTABLE 引用它们作为编译输入）。
#   * 若实际需要运行 COCONUT / SolarCorona / AdvectSinusWave
#     等算例，请在此脚本中临时恢复对应的解压逻辑，或手动
#     `unxz <file>.xz`。
#
# CMakeLists.txt 中通过 execute_process() 调用本脚本，失败会
# 触发 FATAL_ERROR 中止 cmake。此处保持返回 0 以兼容。
# ============================================================
echo "######## init_testcases.sh: no-op (skipped to keep .xz archives) ########"
exit 0
