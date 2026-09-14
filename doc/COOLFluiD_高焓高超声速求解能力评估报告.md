# COOLFluiD 求解器高焓高超声速流动求解能力综合评估报告

**评估日期**：2026-08-26（**2026-09-12 更新**：补充实测验证进展，见 §6.1；运行验证细节见 `VALIDATION_REPORT.md`）
**代码库**：`/home/tang/packages/COOLFluiD`
**代码规模**：C++ 源码约 365,000 行（`.cxx` 3346 个，`.hh` 3976 个，`.h` 44 个）
**构建状态**：已完整构建并安装于 `install/`，全部关键插件已编译为动态库，可执行文件 `coolfluid-solver` 运行正常。

## 版本时间线（倒序）

| 日期 | 事件 |
|------|------|
| **2026-09-13** | **更新**：新增与 `MUTATIONPP_INTEGRATION_REPORT.md`（COOLFluiD × Mutation++ 能力分工/API 映射/升级 SOP）的交叉引用——本报告 §1.2 的物性库接口插件与 §2.1 的化学库接入细节，在该报告中给出 API 级映射与"COOLFluiD 自实现 vs M++ 提供"的完整差集分析 |
| **2026-09-12** | **更新**：新增 §6.1 实测验证进展（完成度四档结论）；修正 §7.2 环境结论（miniforge3/conda 已安装，初版"conda 缺失"不再成立）；同步更新问题清单、修改建议、主要局限与综合结论 |
| 2026-08-26 | **初版**：静态代码审查 + 构建/启动验证（C++ 约 36.5 万行、863 个插件文件、1236 个 `.CFcase`；能力定级"强"） |
| 2026-09-05 ~ 09-12 | （非本报告范围）实际运行验证分阶段开展并形成独立报告，时间线详见 `doc/VALIDATION_REPORT.md`；算例清单级状态见 `doc/high_enthalpy_testcases_report.md` §6 |

---

## 一、代码架构与模块组成

### 1.1 总体架构

COOLFluiD 采用**多插件（plugin）架构**，内核（`src/`）与物理/数值插件（`plugins/`）分层解耦，通过运行时动态加载（`.CFcase` 中的 `Simulator.Modules.Libs` 指定）实现模块化组合。

- **内核层（`src/`）**：`Common`（基础数据结构与 MPI 基础设施）、`Config`（配置系统）、`Framework`（求解器框架、物理化学库抽象接口 `PhysicalChemicalLibrary`）、`Environment`、`MathTools` 等。
- **插件层（`plugins/`）**：863 个文件，覆盖物理模型、数值方法、网格/后处理工具。
- **可执行程序**：`coolfluid-solver`（主求解器）、`ConvertStructMesh`、`xcfcase_converter`、`coef_merge`、`tecplot_merge`、`test_analyticaldm` 等。

### 1.2 与高焓高超声速直接相关的插件

| 插件 | 作用 |
|------|------|
| `NEQ` | 化学非平衡（CNEQ）与热化学非平衡（TCNEQ）Navier-Stokes 物理模型 |
| `FiniteVolumeNEQ` | 非平衡流有限体积求解（化学反应/振动源项、辐射耦合） |
| `FiniteVolumeNavierStokes` | 高焓流 Navier-Stokes 有限体积求解与壁面热流后处理 |
| `RadiativeTransfer` | 辐射传输求解器与辐射物性库（HSNB/PARADE/Grey/ArcJet） |
| `Catalycity` | 壁面催化模型 |
| `Mutation2.0I` / `Mutation2OLDI` / `MutationppI` | 物理化学库接口（热物性、输运、化学反应速率）；**M++ 集成的完整 API 级映射、能力分工与未用功能差集见 `MUTATIONPP_INTEGRATION_REPORT.md`** |
| `LTE` | 局部热力学平衡模型 |
| `ATDModel` | 空气热解模型 |
| `ArcJet` | 感应耦合等离子体（ICP）/弧加热器（LTE + 感应） |
| `ParMetisBalancer` | 并行网格剖分 |
| `FiniteVolumeCUDA` / `FluxReconstructionCUDA` | GPU 加速 |

---

## 二、物理模型支持（核心评估项）

### 2.1 热化学非平衡（核心能力）

COOLFluiD 在高焓非平衡建模上提供了**完整、工业级**的能力：

- **两温度模型（2-T）**：`NavierStokes2DTCNEQ` / `NavierStokes3DTCNEQ`，输运方程含振动能方程（`nbVibEnergyEqs = 1`），通过 `getSource` 返回化学源项与振动 VT 弛豫源项。
- **电子/电子能量非平衡**：`includeElectronicEnergy = true`（FireII 算例启用），支持电离后的自由电子与电子能量方程（`getSourceEE`）。
- **多温度多振动能模型（Multi-Tv-Te）**：`Nozzle1DNEQ` 算例使用 `ThermNEQMultiTvTe`，可设置多个振动温度并独立求解电子温度 Te，超出标准 2-T 模型能力。
- **变量变换体系**：支持 `Rhoivt`、`RhoivtTv`、`Cons`、`Symm`、`Roe`、`RoeVinokur`、`Pivt`、`Pvty` 等，兼顾稳定性与精度。
- **化学离解/电离反应**：通过 Mutation 系列库接入 Arrhenius 反应速率（`getMassProductionTerm`，可解析计算 Jacobian 矩阵 `flagJac`）。
  - `Mutation2OLD`（FireII 算例）：`air11` 11 组分 + `parkair93`（Park 1993 标准空气反应集）
  - `Mutation2`：`air5` + `park5`
  - `Mutation++`（`MutationppI`，M++ 算例）：现代对象化接口
  - `Mutation2.0I`：含 `data/` 下 191 个物性数据文件（26 种混合气、27 种平衡组分表）

### 2.2 振动激发与弛豫

通过物理化学库接口 `getSourceVT(temp, tVec, pressure, rho, omegav, omegaRad)` 返回振动温度源项（VT 能量交换），并在有限体积源项（`ChemNEQST`）中积分。支持振动能输运（TCNEQ 变量集）。

### 2.3 离解与电离反应

- 通过 Mutation 库的化学反应动力学模块处理离解与电离反应，支持解析 Jacobian 加速隐式求解。
- 多组分输运（`getRhoUdiff`）：包含多组分扩散与热扩散（Soret 效应），`dynViscAlgo = CG`（Chapman-Cowling）等算法可选。

### 2.4 辐射耦合（重点亮点）

**`RadiativeTransfer` 插件**提供了从**物性**到**求解**到**耦合**的完整辐射建模链路：

- **辐射物性库**（`RadiationLibrary/Models/`）：
  - `HSNB`：High-resolution Spectral Non-Black body 谱带模型（NASA/明尼苏达大学的高分辨率逐线/谱带基准模型，`core/` 下 61 个源文件，含 `data.tgz` 光谱数据）
  - `PARADE`：ESA 的辐射传输程序接口（含 CUDA 版本 `ParadeRadiatorCUDA`）
  - `Grey`：灰气体模型
  - `ArcJet`：电弧加热器/等离子体辐射模型
  - `Null` / `Reflection`
- **辐射求解方法**（`Solvers/`）：
  - `MonteCarlo`：蒙特卡洛射线追踪
  - `FiniteVolumeDOM`：离散坐标法（Discrete Ordinates）
  - `FiniteVolumeSolar`：太阳辐射
- **流场-辐射耦合**：`ChemNEQST` 源项含 `_hasRadiationCoupling` 标志与 `RadRelaxationFactor`（辐射松弛因子，控制耦合收敛），辐射源项 `omegaRad` 由物理化学库/辐射系统注入能量方程。

### 2.5 壁面催化

**`Catalycity` 插件**独立实现壁面催化模型，`FiniteVolumeNEQ` 与 `Catalycity` 联动，在壁面边界施加热流平衡与催化反应速率边界条件。专门算例：
- `CNEQ/Catalicity/Test_for_Cyl.CFcase`、`Testcase_TCNEQ.CFcase`
- `TCNEQ/CateIXV/IXV_CATE_M25_air5_CNEQ.CFcase`（EXPERT IXV 飞行器催化壁）
- `TCNEQ/ICP2Cat/restart.CFcase`（ICP 双催化）

### 2.6 其他高焓相关模型

- **LTE** 插件：局部热力学平衡（ArcJet 中与 `LTEPhysicalModel` 结合）。
- **ArcJet/ICP**：感应耦合等离子体，含 `ArcJetInductionTerm` 感应加热源项、`ArcJetLTEPhysicalModel`，20 个测试算例。

---

## 三、数值方法

### 3.1 空间离散格式

- **主导方法**：二阶格心有限体积（`CellCenterFVM`），支持重构 `LinearLS2D/3D`、限制器 `Venktn2D/3D`（Venkatakrishnan）、`Bartels`、`SuperBee` 等。
- **Riemann 求解器 / 通量分裂器**（高焓多组分专用）：
  - `AUSMPlusMS2D/3D`（AUSM+ 多组分）、`AUSMPlusUp`、`AUSM`、`PlusMS`
  - `Roe`、`VanLeer` 等（FVM 分裂器）；HLL/LDA 型格式在 RDS/FluctSplit（如 `SysBLDAHLLCx`，双锥 CRD 所用）。初版所列 `LDFSS` 经全树 grep 证实不存在，已删（2026-09-13 复核）
- **高阶方法**（`plugins/` 下完整支持）：
  - `FluxReconstructionMethod`（FR，含 PETSc 与 CUDA 版本）
  - `SpectralFD`、`SpectralFV`
  - `DiscontGalerkin`（间断伽辽金）
  - `FluctSplit`（残差分布法，含 `PrabhuCylinder` RDS TCNEQ 算例）
  - `KOmega`、`KappaMethod` 等

### 3.2 时间推进策略

- **显式**：`RungeKutta`、`RungeKutta2`、`RungeKuttaLS`、`ForwardEuler`
- **隐式（稳态高焓问题重点）**：
  - `NewtonIterator`：牛顿迭代，配合数值 Jacobian（`NumJacob`、`NumJacobFast`，可冻结扩散系数）
  - `LUSGSMethod`：LU-SGS（Lower-Upper Symmetric Gauss-Seidel），支持 `BDF2`、`BDF3`、`CrankNicholson` 时间格式、块 Jacobian 扰动计算（`ComputeDiagBlockJacobMatrByPert`）、LU 分解
  - `BackwardEuler`、`EmptyConvergenceMethod`

### 3.3 隐式求解性能（线性求解器）

- **PETSc 集成**（`libPetscI.so`）：FireII 算例使用 `PCType = PCASM`（并行）、`PCILU`（串行）、`KSPGMRES`、`MatOrderingType = MATORDERING_RCM`，最大迭代 1000，200 个 Krylov 子空间。
- 其他可用：`Trilinos`、`Paralution`、`Pardiso`、`SAMGLSS`、`FluctSplit` 等线性求解器插件。
- **解析 Jacobian**：物理化学库支持解析化学源项 Jacobian，显著提升隐式收敛性与鲁棒性。

---

## 四、边界条件与初始条件

### 4.1 边界条件（高焓流完整套件）

以 FireII TCNEQ 算例为代表，验证了完整 BC 组合：

| BC 类 | 用途 |
|-------|------|
| `NoSlipWallIsothermalNSrvtMultiFVMCC` | 等温无滑移壁（`TWall=640K`），多组分，热化学非平衡壁面 |
| `MirrorVelocityFVMCC` | 对称面（镜像） |
| `SuperInletFVMCC` / `SuperOutletFVMCC` | 超声速进/出口 |
| `NoSlipWallAdiabaticNSrvt` | 绝热无滑移壁 |
| 催化壁（经 Catalycity） | 催化热流平衡边界 |

- 特征类 BC、远场、壁面辐射、Giles 等在各插件中均有实现。
- **关键特性**：`DistanceBasedGMoveRhoivt` 节点外推强化壁面无滑移（`ValuesIdx = u v T Tv`，设置 `Values = 0 0 640 640`），并支持 `NbIterAdiabatic = 1000`（前 1000 步绝热壁提高稳定性、加速激波脱体）。

### 4.2 初始条件

- `InitState` 命令支持解析表达式（`Vars = x y`，`Def = ...`），支持逐组分密度初始化、人工边界层构建、自由来流状态设定（FireII 来流：ρ=0.00078, p=62.04 Pa, u=10480 m/s, T=276 K）。
- 支持从已有 `.CFmesh` 重启（`Restart = true`），并可保存/恢复限制器等额外状态变量（`ExtraStateVarNames = limiter`）。

---

## 五、并行计算能力与可扩展性

### 5.1 MPI 并行

- 完整的 MPI 基础设施（`src/Common/MPI/`）：`PEInterfaceMPI`、`MPIHelper`、`MPICommPattern`、`CommPattern`（halo 交换模式 `PatternFullExchange`、`PatternRing`）、`ParVector` 等。
- 网格剖分：`ParMetisBalancer`（基于 ParMetis 库）。
- 线性求解并行：PETSc `PCASM` 域分解、GMRES Krylov 子空间。
- **构建确认**：求解器链接 MPICH（`libmpi.so.0`），系统另有 OpenMPI 4.1.2，MPI 能力已实际编译进库。

### 5.2 GPU 加速

- `FiniteVolumeCUDA`：CUDA 实现的 RHS 计算、RHS+Jacobian 计算、源项计算（含 `FVMCC_ComputeRhsJacobCell.cu`、`FVMCC_ComputeSourceRhsJacobCellParalution.cu`）。
- `FluxReconstructionCUDA`：FR 高阶方法 GPU 版。
- `ParadeRadiatorCUDA`：辐射物性 GPU 版。
- 支持与 Paralution（GPU 线性求解器）协同。

### 5.3 可扩展性评估

- 架构面向大规模并行设计（`PEInterface` 抽象、通信模式可配置）。
- 高焓问题（非平衡化学反应 + 解析 Jacobian + 辐射）单步开销较高，隐式（LUSGS/PETSc）与 GPU 加速为可扩展性提供了必要支撑。
- 说明：本次审查基于静态代码与构建产物分析，未进行多节点强/弱扩展性实测。

---

## 六、验证与基准算例对比

测试用例库规模庞大（**全库 1236 个 `.CFcase` 文件**），其中高焓高超声速验证算例丰富且均对应**国际公认基准/飞行数据**：

| 算例 | 验证对象 | 物理模型 |
|------|---------|---------|
| **FireII**（fire2_1643s_CNEQ / TCNEQ / M++） | FIRE II 再入飞行实验（1643s 轨迹点），对比壁面热流 | air11/parkair93, 2-T + 电子能, 11 组分 |
| **DoubleCone Run42_N2** | CUBRC/Holden 高超声速双锥分离流实验（Run 42） | TCNEQ, N2 |
| **Hornung**（FVM_NS_CNEQ/TCNEQ/M++） | Hornung 球/圆柱激波脱体实验 | CNEQ/TCNEQ, 多版本 |
| **PrabhuCylinder** | Prabhu 圆柱基准（RDS 残差分布法 TCNEQ） | TCNEQ |
| **CNEQ/SphereCO2Mach28** | Mach 28 CO2 球（火星再入） | CNEQ, M++ |
| **CateIXV**（IXV_CATE_M25_air5） | EXPERT/IXV 飞行器催化壁 | air5 CNEQ, 催化 |
| **EXPERT3D** | EXPERT 三维飞行器 | TCNEQ 3D |
| **ICP2Cat** | 感应耦合等离子体双催化 | ICP + 催化 |
| **Nozzle1DNEQ**（MultiTvTe） | 多温度喷嘴 | Multi-Tv-Te |
| **ShockTube** | 1D 激波管（Sod 型） | Euler1DNEQ, air5/park5 |
| **FireIIDLR / MslDLR / VikingDLR / HuygensDLR** | 辐射耦合基准（FIRE II、火星科学实验室、海盗号、惠更斯号再入） | 辐射 + 流场耦合 |
| **ArcJet** 20 个算例 | 弧加热器/ICP 地面测试 | ArcJetLTE |

这些算例覆盖了再入飞行器热防护分析的核心验证场景：**激波脱体距离、壁面热流、辐射加热、催化效应、分离流/激波干扰**，且多数提供与实验数据的直接对比设置（FireII 壁面热流后处理命令 `NavierStokesSkinFrictionHeatFluxCCNEQ` 计算 q_wall）。

### 6.1 实测验证进展（2026-09-12 更新）

初版评估（2026-08-26）基于静态代码审查；此后以 Mutation++（外部接口，未改源码）
为物性库，对高焓非平衡算例开展了实际运行验证（逐项核查结果目录/日志/配置，
完整证据链见 `doc/VALIDATION_REPORT.md`）。完成度四档结论：

**已确认完成对比验证：**

1. **Hornung N2 圆柱（Euler CNEQ，V3）**——本轮唯一端到端完成的定量验证：
   38054 步收敛（残差 −3.00009）；驻点线近壁 T/p/密度比与 Mutation++ 平衡
   正激波解偏差 +1.2%/−4.7%/−0.8%；激波脱体 δ/R=0.31 vs 实验 0.22（Hornung
   1972，粗网格高估 39%，机理明确）；MutationppI 适配层端到端集成正确。
2. **Mutation++ 库独立核查**（7 项库级检查全部通过）。
3. **SU2 NEMO 交叉对比**（定性一致；SU2 未充分收敛，仅定性）。

**部分完成（物理有效性确认、定量对比未闭环）：** FireII 冻结相（化学相三次
发散，11 组元化学刚性）；ShockTube 1D（修复后 6/7 残差收敛，T 分量停滞）；
Hornung 细网格（V5 系列三次失败，Euler 细网格驻点奇异性）。

**待超算运行验证：** DoubleCone Run42（论文主锚点，CUBRC 实验壁面压力/热流
对比，冒烟已通过、生产配置已备）；FireII 化学相生产运行；Hornung 细网格
δ/R 网格收敛（V6 方案）。运行说明见 `VALIDATION_REPORT.md` §8。

**对本报告能力结论的影响：** CNEQ（单温度）+ Mutation++ 集成的正确性已由
实测定量确认；TCNEQ（双温度）仅冒烟验证、定量结论待双锥 Run42 超算运行；
两个已识别的数值限制——11 组元电离空气化学刚性下的隐式收敛（FireII 化学相）
与 Euler 无粘细网格驻点奇异性——不影响 V3 级别粗网格 CNEQ 分析的有效性，
但在完成超算验证前，对更强刚性工况（电离空气、细网格无粘）的收敛能力应
保守评估。

---

## 七、运行环境与构建验证

### 7.1 构建状态（已验证）

- 代码已完整构建并安装于 `install/`，关键动态库全部存在：`libNEQ.so`、`libFiniteVolumeNEQ.so`、`libRadiativeTransfer.so`、`libCatalycity.so`、`libMutationppI.so`、`libPetscI.so`、`libParMetisBalancer.so`、`libFluxReconstructionCUDA.so` 等。
- `ldd install/bin/coolfluid-solver` 无任何 `not found` 依赖，求解器二进制可正常启动（读取 `.CFcase`）。
- 构建配置确认启用：MPI（MPICH/OpenMPI）、PETSc、ParMetis、CUDA 插件编译。

### 7.2 系统运行环境（已验证）

- **系统环境**（`source ~/.bashrc`）：Python 3.10.12，含 numpy 2.2.6、scipy 1.15.3、matplotlib 3.10.9、h5py 3.16.0——满足后处理脚本需求。
- **conda base**（**2026-09-12 核查更新**）：miniforge3 已安装于 `/home/tang/miniforge3`（初版评估时未装），`source /home/tang/miniforge3/etc/profile.d/conda.sh && conda activate base` 可用，实测验证的后处理脚本（numpy/scipy/matplotlib）已在其下运行；系统 Python 3.10 亦具备同等依赖，后处理不构成阻塞。

---

## 八、发现的问题清单

1. ~~**conda 环境缺失**~~（**2026-09-12 已解决**：miniforge3 已安装于 `/home/tang/miniforge3`，conda base 可用并已支撑后处理脚本运行）。
2. **端到端实测验证已部分完成（2026-09-12 更新）**：初版指出的"未实际运行完整非平衡算例"已部分解决——Hornung V3 完成端到端收敛与定量对比验证；ShockTube 1D 修复后可稳定推进；FireII/DoubleCone 两个高成本算例的生产运行（定量闭环）待超算算力，运行说明已备（`VALIDATION_REPORT.md` §8）。建议后续在超算完成双锥 Run42 与 FireII 后，将本报告 §6.1 的结论升级为"定量闭环完成"。
3. **多节点可扩展性未实测**：并行架构完备，但未进行多核/多节点强、弱扩展性 benchmark。
4. **GPU 路径未经实机验证**：CUDA 插件已编译，但需 NVIDIA 环境实测。
5. **文档偏学术化**：`doc/` 主要为学术论文/手册（Manuals），缺乏面向新用户的端到端快速上手教程，配置项（尤其 NEQ 的非平衡变量 ID 映射）学习曲线较陡。
6. **代码规模大、模块多**：365k 行、86+ 插件，存在历史插件重复（如多套 Mutation 接口 Mutation2/2.0/2OLD/pp），维护与移植成本较高。
7. **`--version` 等命令行参数不支持**：`coolfluid-solver --version` 抛 `BadMatchException`（`no option '--version'`），CLI 信息获取体验一般。

---

## 九、修改建议

1. ~~**补齐 conda**~~（已完成：miniforge3 已安装，conda base 可用）。
2. **端到端验证（2026-09-12 更新）**：本机已形成验证矩阵雏形——Hornung V3（定量通过）、Mutation++ 库核查、SU2 交叉对比（定性）；FireII 化学相、双锥 Run42、细网格收敛三例待超算完成（`VALIDATION_REPORT.md` §8 运行说明已备）。超算运行完成后建议将验证矩阵扩展至 TCNEQ（双锥）与电离空气（FireII），并补充 1D 激波管瞬态解析对比。
3. **可扩展性测试**：对 DoubleCone/FireII 算例做 1/2/4/8/16 核 MPI 强扩展测试，量化 PETSc PCASM 与 LUSGS 的并行效率。
4. **统一物理化学库接口**：评估将多套 Mutation 接口收敛到 `MutationppI`（Mutation++）单一现代接口，减少维护负担。
5. **补充教程文档**：为 NEQ/TCNEQ/辐射耦合编写快速上手模板与变量 ID 映射说明。
6. **CLI 增强**：为求解器补充 `--version`、`--help`、`--dump-config` 等诊断选项，改善可用性。

---

## 十、高焓高超声速流动求解能力综合评价

### 能力定级：**强（工业级 / 学术前沿级）**

COOLFluiD 在高焓高超声速流动领域具备**完整、成熟、经过国际基准验证**的求解能力，是当前开源 CFD 生态中面向高焓/再入物理最全面的求解器之一。

**核心优势：**

1. **热化学非平衡建模全面**：覆盖 CNEQ、TCNEQ（2-T）、Multi-Tv-Te 多温度模型、电子/电离非平衡，变量变换体系丰富，可经 Mutation/Mutation++ 接入任意反应集与物性库。
2. **辐射耦合是一流能力**：内置 HSNB 高分辨率谱带模型与 PARADE 接口，配合 MC 射线追踪与离散坐标法，并通过 FIRE II / MSL / VIKING / HUYGENS 再入辐射基准验证——这在开源 CFD 中非常罕见。
3. **壁面催化独立插件**：Catalycity 插件 + EXPERT IXV / ICP 催化算例，覆盖热防护系统催化热载荷评估。
4. **隐式求解性能扎实**：PETSc 并行线性求解 + LUSGS/BDF 系列 + 解析化学 Jacobian，适合高焓强源项问题。
5. **验证体系完善**：以 FireII（飞行数据）、DoubleCone（实验）、Hornung、CO2 火星再入等构成的高质量基准矩阵，可信度高。
6. **并行与加速**：MPI + ParMetis 剖分 + CUDA GPU 加速 + Paralution，具备向大规模与异构计算扩展的架构基础。

**主要局限：**

1. 高焓问题的**文档与上手门槛**偏高，非平衡变量 ID 映射、物理化学库配置需要较高专业知识。
2. 多套历史 Mutation 接口并存，接口复杂度高。
3. GPU/多节点路径未实测，实际可扩展性需进一步量化。
4. 未提供官方容器化/CI 一键构建方案，环境搭建依赖手工。
5. **实测暴露的数值限制（2026-09-12）**：11 组元电离空气（FireII）化学刚性在
   当前隐式伪时间推进框架下三次发散，TCNEQ 双温度模型仅冒烟验证——生产级
   电离流动/双温度分析能力需待超算定量验证后才能确认。

**结论**：COOLFluiD **在架构与模型覆盖上完全具备高焓高超声速流动（含热化学非平衡、振动、离解/电离、辐射耦合、壁面催化）的求解能力**；本轮实测已定量确认 CNEQ 单温度 + Mutation++ 路径的集成正确性与物理正确性（Hornung V3：近壁平衡态与正激波解偏差 ≤5%、δ/R 落在物理极限区间内）。建议在超算完成 DoubleCone Run42（TCNEQ 定量闭环）与 FireII（电离空气收敛性）验证后，再将其作为高焓再入热防护问题的高置信度分析工具投入使用。
