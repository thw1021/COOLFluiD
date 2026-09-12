# Mutation++ 升级适配报告

日期：2026-09-12 ｜ 状态：**适配完成，冒烟验证通过** ｜ 范围：Mutation++ v1.0.5-92 → v1.0.5-108 升级对 COOLFluiD 的影响评估、适配层重编、3 项附带问题修复与端到端验证

> **一句话结论**：M++ 升级后 COOLFluiD **无需全量重编**——全树仅适配层 `libMutationppI.so` 一个组件依赖 `libmutation++.so`；按本报告 §7 流程重编适配层（约 2 分钟）+ 数据文件检查 + 冒烟即可。本次升级适配已全部完成，10 步冒烟通过。

---

## 0. 升级事件时间线（2026-09-12）

| 时刻（+0800） | 事件 |
|------|------|
| 09-12 11:11 | `/home/tang/packages/Mutationpp` 执行 `git pull`，快进 `bb054e5`（v1.0.5-92，2026-04-06 pull）→ `e8edf4f`（v1.0.5-108，上游 2026-07-26），共 16 个提交 |
| 09-12 18:29 | M++ 重新编译并安装（`install/lib/libmutation++.so` 时间戳为准） |
| 09-12 18:5x | COOLFluiD 适配层重编、数据文件恢复、算例笔误修复（本报告 §4–§5） |
| 09-12 19:03 | Hornung V3_SMOKE 10 步冒烟通过，结果正常写出 |

COOLFluiD 侧升级前状态：`libMutationppI.so` 编译于 09-09 13:52，基于当时 M++ 源码 `bb054e5`；内核与其他插件均不涉及 M++。

## 1. 依赖关系分析（为何无需全量重编）

对 `build/optim/dso/` 全部共享库做 `readelf -d` 扫描，**唯一** `NEEDED` 含 `libmutation++.so` 的组件：

| 组件 | 依赖 M++ 方式 | M++ 重编后是否需重编 |
|------|--------------|---------------------|
| 内核（libCommon/Config/Framework…）、其余全部插件 | 无链接 | 否（dlopen/运行时零接触） |
| `libMutationppI.so`（适配层，`plugins/MutationppI/`） | 动态链接 + **编译期内嵌 `<mutation++.h>`**（内联函数、类布局） | **是**（见 §3） |

动态链接层面 SONAME（`libmutation++.so`）未变，运行时自动加载新库；但适配层在编译时把头文件内容（内联方法、类成员布局）固化进自己的二进制，M++ 重编后存在布局/标志漂移风险——这正是 `doc/VALIDATION_REPORT.md` §8.0 记录的本机教训（"M++ 重新安装/升级后适配层 libMutationppI 必须重编，本机已验证 ABI 兼容随 M++ 库重建而失效"）。

## 2. API/ABI 兼容性核查（bb054e5 → e8edf4f）

`git diff --stat bb054e5..HEAD`：17 个文件，+305/−45 行，集中在两处：

1. **GSI（气固相互作用）**：`GasSurfaceInteraction.{h,cpp}`、`Surface.h`、`SurfaceBalanceSolver*` 新增表面平衡收敛容差设置（上游 PR #305）——**纯增量**，COOLFluiD 适配层与全部算例均未使用 GSI。
2. **`src/thermo/Thermodynamics.{h,cpp}`**：唯一签名变化为 `surfaceMassBalance(...)` 末尾新增带默认值的参数 `p_Ykc`——改变该函数符号名，但适配层未调用（`grep` 证实无 `surfaceMassBalance`/GSI 引用）。

`Mixture.h` 未变；适配层实际使用的 API（`MixtureOptions`、`Mixture` 构造、`nSpecies/nElements/nEnergyEqns/speciesMw/setState/viscosity/equilibriumThermalConductivity/species(i)`）全部未动。`ldd -r` 符号解析检查：重编适配层**之前**即 0 个未解析符号——即本次升级在符号层面本就兼容；重编适配层属于按既定教训消除布局漂移风险，成本约 2 分钟。

## 3. 适配层重编与安装刷新

```bash
cd /home/tang/packages/COOLFluiD/build/optim
make MutationppI          # 仅编这一个目标；输出仅原有 auto_ptr 弃用警告，无错误
make install              # 完整安装通过（exit 0，见 §5.3 前置修复）
```

- `build/optim/plugins/MutationppI/libMutationppI.so`：09-12 18:56 重编；`ldd -r` 0 未解析符号。
- `install/lib/libMutationppI.so`：由 `make install` 正规刷新（RUNPATH 已改写为 install 布局），替换旧 09-09 副本。
- 注意：`make install` 会先触发全量构建，依赖 §5.3 的 `.cu` 生成文件齐全；只编适配层时用目标名 `make MutationppI` 即可。

## 4. 冒烟端到端验证（通过）

用例：`plugins/NEQ/testcases/TCNEQ/Hornung/hornung_FVM_NS_CNEQ_EULER_n2_2_V3_SMOKE.CFcase`（Euler2DNEQ + MutationppI `ChemNonEqTTv`，混合物 n2_2，10 步冒烟配置）。

```bash
mkdir -p plugins/NEQ/testcases/TCNEQ/Hornung/results/SMOKE_MPP_v108_20260912
cd plugins/NEQ/testcases/TCNEQ/Hornung/results/SMOKE_MPP_v108_20260912
mpirun -np 1 ${CF_ROOT}/build/optim/apps/Solver/coolfluid-solver \
  --scase .../hornung_FVM_NS_CNEQ_EULER_n2_2_V3_SMOKE.CFcase \
  --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso
```

结果（19:03）：10 步完整运行、残差单调变化（第 10 步 log-L2 ≈ −1.915）、CNEQ 化学源项经 M++ 正常计算、`HornungN2.plt / .surf.plt / CFmesh / convergence.plt.Default` 正常写出、环境正常退出。末尾 `--bdir/--ldir/--scase` 的 "unused option" 警告为已知噪音。

## 5. 发现并修复的三个问题

### 5.1 M++ 自定义混合物数据丢失（阻塞级，升级附带损伤）

- **现象**：冒烟首跑即 `M++ error: file not found: /home/tang/packages/Mutationpp/data/mixtures/n2_2.xml`。
- **根因**：`n2_2.xml`（混合物）与 `n2_2_Park.xml`（机理）**从不在 M++ git 仓库内**——两个版本的 `data/` 树均只含 5 个官方混合物（air_5/air_11/CO2_8/Mars_19/tacot-air_35）。它们是本轮验证期间本地添加的未跟踪文件（与 `N2_neut/N2_TTv → n2_2` 混合物名适配同源，见 `VALIDATION_REPORT.md` §8.3），M++ 更新/重装过程中被清理。
- **修复**：从 `~/packages/SU2/nemo_validation/mpp_2021/data/` 恢复两个文件至 `/home/tang/packages/Mutationpp/data/{mixtures,mechanisms}/`；XML 格式与新库逐字段一致（mixture/species/element_compositions、arrhenius_units/reaction）；`checkmix n2_2` 通过（反应 N2+M=2N+M，A=3.0e16，n=−1.6，Ta=113200 K，与 Park 2001 一致）。
- **注意**：运行时数据目录由 `MPP_DATA_DIRECTORY=/home/tang/packages/Mutationpp/data`（`~/.bashrc`）指定，指向**源码树 data/**，故每次更新 M++ 源码都要确认这两个文件仍在（§7 SOP 第 1 步）。

### 5.2 Hornung V3_SMOKE 算例笔误（预先存在，与 M++ 无关）

`hornung_FVM_NS_CNEQ_EULER_n2_2_V3_SMOKE.CFcase` 第 76 行误写 `Simulator.SubCenterFVM.InField.Vars = x y`（缺 `SubSystem.CellCenterFVM` 中段），导致该选项被框架判为 unused（启动日志有 WARNING），InField 初始化函数无变量定义而 `Def` 提供了 5 个值，触发 `VectorialFunction.cxx:119` 断言崩溃。已改为 `Simulator.SubSystem.CellCenterFVM.InField.Vars = x y`（与完整版 V3 一致）。**教训**：启动日志的 "Unused User Configuration Arguments" WARNING 值得先看——本次它能直接定位笔误。

### 5.3 CMake 配置期生成的 `.cu` 文件缺失（预先存在，阻断 make install）

- **机制**：`plugins/FiniteVolume/CMakeLists.txt:386` 与 `plugins/FluxReconstructionMethod/CMakeLists.txt:501` 用 `EXECUTE_PROCESS(COMMAND cp <名>.cxx <名>.cu)` 在**配置期**生成 CUDA 源（原始库同款设计），生成文件 git 不跟踪——两个代码库的 git 历史中均无此文件属正常现象。
- **后果**：09-09 之后的某次清理删除了 `LaxFriedFlux.cu` 与 `LaxFriedrichsFlux.cu` 两个生成文件，全量 `make all/install` 报 `cc1plus: fatal error: ...: No such file or directory`。
- **修复**：`cp -p .cxx 同名.cu` 恢复两文件（`-p` 保留旧时间戳，使其早于 09-09 的 `.cu.o`，make 判定无需重编 nvcc）；随后 `make install` 完整通过（exit 0）。
- **备选恢复法**：在 `build/optim` 重跑 cmake configure（会重新执行 EXECUTE_PROCESS）。

## 6. 验证证据清单

| 检查项 | 命令 | 结果 |
|--------|------|------|
| 依赖面扫描 | `readelf -d build/optim/dso/*.so \| grep mutation` | 仅 libMutationppI.so |
| 符号兼容（重编前） | `ldd -r build/optim/plugins/MutationppI/libMutationppI.so` | 0 unresolved |
| 适配层重编 | `make MutationppI` | 通过（仅 auto_ptr 弃用警告） |
| 数据自检 | `install/bin/checkmix n2_2` | succeeded |
| 安装刷新 | `make install` | exit 0；install/lib 副本 RUNPATH=install 布局 |
| 端到端 | V3_SMOKE 10 步 | 通过，结果 19:03 写出，残差单调 |

## 7. 今后 M++ 更新的标准操作流程（SOP）

M++ 源码修改/更新并重编安装后，COOLFluiD 侧依次执行（全部命令已在本次实测）：

```bash
# 1. 检查未跟踪自定义数据文件（M++ 侧做过 git clean 类清理必丢）
ls /home/tang/packages/Mutationpp/data/mixtures/n2_2.xml \
   /home/tang/packages/Mutationpp/data/mechanisms/n2_2_Park.xml
# 丢失则恢复: cp -p ~/packages/SU2/nemo_validation/mpp_2021/data/{mixtures/n2_2.xml,mechanisms/n2_2_Park.xml} 至对应目录

# 2. 数据快速自检
bash -ic '/home/tang/packages/Mutationpp/install/bin/checkmix n2_2'

# 3. 重编适配层（唯一 M++ 消费者，约 2 分钟；不要全量 make）
cd /home/tang/packages/COOLFluiD/build/optim && bash -ic 'make MutationppI'

# 4. 刷新 install/lib（.cu 生成文件齐全时可行）
bash -ic 'make install'

# 5. 冒烟验证（10 步，结果写新目录）
#    命令见 §4；末尾出现 "COOLFluiD Environment Terminated" 且有 .plt 输出即通过
```

**按改动规模分档**：
- **仅 `.cpp` 实现变化**：符号层面大概率兼容（本次实测如此），但 SOP 照走——第 3 步仅 2 分钟，换取消除布局漂移风险。
- **跨版本升级**（数据库/头文件变动）：另需核对全部在跑 CFcase 的 `mixtureName` 仍存在于新库 `data/mixtures/`（上次 `N2_neut/N2_TTv/air11 → n2_2/air_11` 适配即此因），可用 `grep -h "mixtureName" <用例>.CFcase` 对照检查。

## 8. 遗留与建议

1. **git clean 类操作风险清单**（本工作流三处易伤，清理前先确认）：
   - COOLFluiD：`LaxFriedFlux.cu`、`LaxFriedrichsFlux.cu`（配置期生成，§5.3）；
   - M++：`data/mixtures/n2_2.xml`、`data/mechanisms/n2_2_Park.xml`（§5.1）；
   - 其他构建生成物。
2. **可选根治**：把两个 `.cu` 的复制从 `EXECUTE_PROCESS`（仅配置期执行）改为 `add_custom_command`（构建期保证存在），或把 n2_2 两个数据文件纳入某处版本管理；本次未改动构建系统，仅按原机制恢复。
3. `doc/VALIDATION_REPORT.md` §8.0"必须重编"条目由本报告具体化为 §7 SOP，后续 M++ 操作按本报告执行即可。
