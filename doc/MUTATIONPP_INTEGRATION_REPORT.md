# COOLFluiD × Mutation++ 集成与能力分工报告

**日期**：2026-09-13 ｜ **状态**：现行文档（替代并吸收原 `MUTATIONPP_UPGRADE_ADAPTATION_REPORT.md`，其升级 SOP 见本报告 §7）
**代码库**：COOLFluiD `master`（/home/tang/packages/COOLFluiD）× Mutation++ `v1.0.5-108`（git `e8edf4f`，CMake 项目版本号 1.2.0，/home/tang/packages/Mutationpp）
**配套文档**：运行验证证据见 `doc/VALIDATION_REPORT.md`；算例级状态见 `doc/high_enthalpy_testcases_report.md`；求解能力总评见 `doc/COOLFluiD_高焓高超声速求解能力评估报告.md`

> **一句话结论**：COOLFluiD 通过唯一适配层 `libMutationppI`（provider 名 `Mutationpp`）以抽象接口在运行时绑定 Mutation++。能力分工上，**COOLFluiD 自身承担"方程与算法"层的全部高焓能力**（NEQ/TCNEQ 控制方程与变量集、多组元无黏/黏性通量格式、隐式时间推进、边界条件、催化边界框架、辐射传输、ICP/电弧电磁物理、湍流耦合），**Mutation++ 提供"组元物性"层**（状态方程与温度恢复所需热力学量、输运系数、化学源项、能量交换源项、平衡组分与物性数据库）。M++ 的 GSI 表面热化学、化学源项解析雅可比、多组元扩散矩阵、磁场各向异性输运、等离子体微观参数等能力**未被 COOLFluiD 使用**（§5 差集分析）。

---

## 0. 执行摘要

1. **单一适配层架构**：全代码树仅 `plugins/MutationppI/` 的 2 个头文件 `#include <mutation++.h>`，构建产物中仅 `libMutationppI.so` 一个组件动态链接 `libmutation++.so`（`readelf -d` 全树扫描证实）。NEQ、FiniteVolumeNEQ、LTE、ICP、ArcJet 等物理/数值插件**零直连 M++**，统一通过抽象基类 `Framework::PhysicalChemicalLibrary` 编程，由 CFcase 中 `PropertyLibrary = Mutationpp` 在运行时实例化适配层。因此 M++ 升级只需重编适配层一个组件（§7 SOP，约 2 分钟）。
2. **利用的 M++ 能力**：热力学（setState 三种状态模型、压力/密度/焓/内能/声速/物种焓模式拆分）、输运（黏度、冻结/平衡热导率、振动热导率向量、电导率）、化学（净生成速率）、能量交换（经 `energyTransferSource` 间接使用全部六种机制 OmegaVT/CV/CElec/ET/CE/I）、平衡组分（Equil 状态模型内部多相平衡求解器）、物性数据库（NASA-7/9、RRHO、碰撞积分库、混合物 XML）。完整 API 级映射见 §3 与附录 A。
3. **未利用的 M++ 能力**（§5）：最重要的三块——① **GSI 气固相互作用全模块**（表面催化/烧蚀/升华/表面质量平衡 B'，COOLFluiD 用自写 `CatalycityModel` Γ 常数催化边界替代）；② **化学源项解析雅可比 `jacobianRho`**（适配层 TODO 未实现，是 11 组元电离空气 FireII 化学相隐式收敛刚性的一个已知因素）；③ **多组元扩散矩阵与多分量热导率拆分**（适配层用 `stefanMaxwell` 求扩散速度、只用冻结/平衡两个总热导率）。
4. **实测支撑**：集成端到端正确性已由 Hornung N₂ 圆柱 V3 定量验证（38054 步收敛，近壁热力学态与 M++ 平衡正激波解偏差 ≤5%，详见 `VALIDATION_REPORT.md` §3）；库级 7 项独立核查全部通过（§8）。

---

## 1. 集成架构

### 1.1 适配层与运行时绑定

```
CFcase (.CFcase)                          运行时选择
   │  Simulator.Modules.Libs += libMutationppI
   │  PropertyLibrary = Mutationpp
   ▼
┌─────────────────────────────────────────────────────────────┐
│ NEQ / FiniteVolumeNEQ / LTE / ICP / ArcJet / PoissonNEQ ... │  物理与数值插件
│ 只 include src/Framework/PhysicalChemicalLibrary.hh，        │  不链接 M++
│ 经 PhysicalModelStack::getActive()->getImplementor()         │
│   ->getPhysicalPropertyLibrary<PhysicalChemicalLibrary>()    │
└──────────────────────┬──────────────────────────────────────┘
                       ▼ 抽象接口（约 40 个虚方法）
┌─────────────────────────────────────────────────────────────┐
│ MutationLibrarypp : Framework::PhysicalChemicalLibrary       │  plugins/MutationppI/
│ provider 注册名 "Mutationpp"（MutationLibrarypp.cxx:29-33）    │  唯一链接 libmutation++.so
│   变体 MutationLibraryppDebug（provider "MutationppDebug"）    │  继承 Mutation2OLD 库类，
│                                                              │  双库同时初始化（上游提交
│                                                              │  自述），可用于两库结果对比
└──────────────────────┬──────────────────────────────────────┘
                       ▼ C++ API
┌─────────────────────────────────────────────────────────────┐
│ Mutation++ libmutation++.so（v1.0.5-108）                     │
│ Mixture = Thermodynamics + Transport + Kinetics + GSI 多继承  │
└─────────────────────────────────────────────────────────────┘
```

关键证据：

| 事实 | 证据 |
|------|------|
| 有效 `#include <mutation++.h>` 全树仅 2 个头文件（PlatoI 另有一行被注释的同名 include） | `plugins/MutationppI/MutationLibrarypp.hh:11`、`MutationLibraryppDebug.hh:13` |
| `Mutation::` 命名空间引用仅 4 个文件 | 均在 `plugins/MutationppI/`（两个类各自 .hh/.cxx） |
| 唯一 NEEDED `libmutation++.so` 的组件 | `readelf -d build/optim/dso/*.so \| grep mutation` → 仅 `libMutationppI.so` |
| 物理插件获取库指针的统一方式 | `plugins/FiniteVolumeNEQ/ChemNEQST.ci:97-98`、`plugins/NEQ/NavierStokesNEQVarSet.ci:62-63` |
| 构建开关 | 顶层 `CMakeLists.txt:392-396`（`CF_ENABLE_MUTATIONPP` → `CF_HAVE_MUTATIONPP`）；`cmake/FindMutationpp.cmake`（头/库探测，`CF_SKIP_MUTATIONPP` 可跳过）；`plugins/MutationppI/CMakeLists.txt:1-27`（链接 `MUTATIONPP_LIBRARY` + Eigen3 include——M++ 依赖 Eigen） |

同名并存的非 M++ 物性库适配层（同一抽象基类的其他实现，运行时按 CFcase 选择）：`MutationI`（Mutation 1.x，F77）、`Mutation2.0I`（Mutation 2.0，写 `mutation.in` 调外部程序）、`Mutation2.0.0I`（Mutation2OLD）、`PlatoI`、`NitrogenNASAI`、`ATDModel`（自实现）。源项代码按库注册名字符串分派的证据：`plugins/FiniteVolumeNEQ/ThermNEQST.ci:226-240`、`plugins/FluxReconstructionNEQ/TNEQSourceTerm.cxx:152-166`。本机构建仅编译了 `libMutationppI`，其余旧库接口未编译。

### 1.2 适配层暴露的 CFcase 选项

`MutationLibrarypp.cxx:37-53`（`defineConfigOptions`）与构造函数绑定（:80-121）：

| 选项 | 含义 | 缺省 |
|------|------|------|
| `mixtureName` | M++ 混合物名，隐式决定物种集、机理与热力学数据库（如 `n2_2`、`air_5`、`air_11`、`CO2_8`、`Mars_19`、`tacot-air_35`；`n2_2`/机制 `n2_2_Park` 为本地自定义文件，见 §7.3） | "" |
| `StateModelName` | M++ 状态模型：`Equil`（LTE 平衡）/`ChemNonEq1T`（CNEQ 单温）/`ChemNonEqTTv`（TCNEQ 双温）——M++ 另注册 `EquilTP` 兼容别名，适配层未暴露 | `Equil` |
| `MinRhoi` | 物种分密度下限钳位（`setState` 内 `std::max(_minRhoi, rhoi[i])`） | 0 |
| `MinT` | 温度下限钳位 | 0 |
| `useLookUpTable` / `lookUpVars` / `Tmin/Tmax/deltaT` / `Pmin/Pmax/deltaP` / `pLogScale` | LTE 路径二维查找表加速：对内能 e、焓 h、声速 a、密度 d 预插值（COOLFluiD 侧 `Common::LookupTable2D`，插值对象为 M++ 求出的量） | false / 空（e,h,a,d 中显式选取）/ 100,2000,10 / 1e4,1e6,1000 / false |

基类 `PhysicalChemicalLibrary` 选项（`src/Framework/PhysicalChemicalLibrary.cxx:19-56`）：`electrEnergyID`、`freezeChemistry`（化学冻结开关，经 `getMassProductionTerm` 置零实现）、`ShiftH0`（生成焓平移使 H(0 K)=0，setup 时以 `speciesHOverRT` 五参数版求 0 K 生成焓）、`MaxTe`。

注意：机理（mechanism）与热力学库（NASA-7/9、RRHO）**没有独立 CFcase 选项**——由 M++ 混合物 XML 内部声明隐式确定。

### 1.3 状态更新协议（有状态调用序列）

适配层封装的是 M++ 的**有状态**访问模式：先 `setState`，再读取量。典型序列（每个单元/边界点、每个通量/源项求值前）：

1. `setSpeciesFractions(y)` / `setState(rhoi, T)` —— 后者对 ρi 施 `MinRhoi` 钳位、对温度向量逐元素施 `MinT` 钳位后调用 `m_gasMixture->setState(&m_rhoiv[0], &m_Tstate[0], 1)`。变量集索引 1 的语义：ChemNonEq1T 为 **（物种分密度， 混合温度）**，ChemNonEqTTv 为 **（物种分密度， {T, Tv}）**（vars 0 = 守恒变量直入、vars 2 = Yi+{P,T[,Tv]}，均未被适配层使用）。
   **双温度路径说明**：`setup()` 将温度状态向量定为 `m_Tstate.resize(nEnergyEqns)`（`MutationLibrarypp.cxx:193,197`），TCNEQ 变量集传入状态向量中相邻的 [T, Tv]（`NavierStokesNEQRhoivt.ci:273-274` 的 `setState(rhoi, TTv)`），M++ `ChemNonEqTTv` 变量集 1 直接消费两温度（`ChemNonEqTTvStateModel.cpp`：`m_T = p_energy[0]; m_Tv = p_energy[1]`）。适配层源码注释 "this needs to be fixed for 2-temperatures"（`hh:92`）**已过时**——复制循环按 `m_Tstate.size()` 处理全部温度分量，双温度路径实际可用；M++ 侧 vars=0 的能量反解路径（`getTFromRhoE`）则未被适配层使用（温度恢复始终由 COOLFluiD 侧给出）。
2. `pressure()` —— 直接读 `P()`（协议注释："setState(rhoi, T) must have been called before this so P() is valid"），非正压返回安全值 1.0（NaN 同样拦截）。
3. `eta()` / `lambdaNEQ()` / `lambdaVibNEQ()` / `sigma()` / `getRhoUdiff()` 等 —— 同样基于已设置的内部状态（`sigma` 注释："we are assuming here that setState() has been called before!"）。
4. LTE/平衡路径专用：`setComposition(T,P,x)` 经独立的 `m_gasMixtureEquil`（Equil 状态模型实例）`setState((P,T), 1)` + `X()` + `convert<X_TO_Y>` 求平衡组分；`density(T,P)` 仅在 `m_smType == LTE` 时做该 setState（Equil 变量集 1 = (P,T)，语义正确），非 LTE 路径必须先走 `setState(rhoi,T)`。

这一协议是 2026-09-08 ShockTube 1D 修复的根因所在：1D 变量集 `Euler1DNEQRhoivt::setThermodynamics` 缺失 `setState()` 调用导致 M++ 内部状态停留初值、通量全 NaN（`VALIDATION_REPORT.md` §6.1）。

---

## 2. COOLFluiD 自身具备的高焓流动求解能力（不经 M++）

以下能力由 COOLFluiD 内核与插件自实现。M++（或任一物性库）仅在被调用点提供组元物性数值；若卸载 M++，这些结构与能力依然存在（部分将因缺物性而无法运行 NEQ 算例，但代码归属不变）。

### 2.1 控制方程体系与变量集（plugins/NEQ）

- 物理模型注册：`Euler1D/2D/3DNEQ`、`NavierStokes2D/3DNEQ` 五个 `PhysicalModelType`；方程数 `nbEqs = nbEulerEqs + nbSpecies + nbVibEnergyEqs + nbTe`（公式在 `plugins/NEQ/EulerNEQ.ci:83`、`NavierStokesNEQ.ci:94`；`nbVibEnergyEqs` 选项声明在 `EulerNEQ.ci:23`、`NavierStokesNEQ.ci:29`）。
- 变量集体系（温度自由度与守恒/原始变换）：`Rhoivt`、`RhoivtTv`、`Pivt`、`PivtTv`、`Pvty`、`Cons`、`Symm`、`Roe`、`RoeVinokur` 及全部 `*ToCons/*ToRoe` 变换器——全部自写（`plugins/NEQ/Euler*DNEQ*.cxx`、`NavierStokesNEQ*`）。
- 温度恢复：守恒量→原始量的变换与温度恢复在变量集/变换器内自实现；适配层始终以变量集 1 显式传温度（M++ 侧 vars=0 的 `getTFromRhoE` 能量反解路径未被使用，见 §1.3）。

### 2.2 双温度 / 电子能量 / 多温度方程骨架

- Park 双温度模型的**方程组装**在 COOLFluiD 侧：`plugins/FiniteVolumeNEQ/ThermNEQST.ci` 组装振动能量方程的化学贡献与 VT 弛豫耦合（含 "term for Park's model" 注释，:429），M++ 只提供 `energyTransferSource` 数值。
- 电子能量方程与电子温度 Te 的控制方程骨架（`getSourceEE` 接口、`ThermNEQST` 的电子能项 :106-140,337-357,437-441,500）为 COOLFluiD 侧；`includeElectronicEnergy` 选项仅由旧库 `Mutation2.0I/Mutation2.0.0I` 注册（**MutationppI 不提供该选项**，grep 全树证实），即 FireII 的 Te 方程路径目前绑定旧库。
- 多振动温度 + 电子温度（Nozzle1DNEQ 算例；`ThermNEQMultiTvTe` 仅为算例命名而非现存类，实际源项 `EulerQuasi1DCNEQST`，nbSpecies=11 / nbVibEnergyEqs=3 / nbTe=1）：M++ v1.0.5-108 注册四种状态模型（`Equil`/`EquilTP`/`ChemNonEq1T`/`ChemNonEqTTv`），**均不支持**多 Tv——该能力由旧 Mutation2 库与 COOLFluiD 侧变量集承担。

### 2.3 无黏/黏性通量格式（NEQ 专用）

- 多组元 AUSM 族：`AUSMPlusMS1D/2D/3D`、`AUSMPlusUpMS`（高焓算例主力，含 choiceA12 开关）、`AUSM`、`AUSMPlusUp`。
- NEQ 专用 Roe / Roe-Vinokur 通量：`Euler2DNEQRoe.cxx`、`Euler2DNEQRoeVinokur.cxx`、`RoeTCNEQFlux`、`RoeVinokurTCNEQFlux`（含 carbuncle 修正与熵修正变体 `RoeVinokurEntropyFixTCNEQ1D`）。
- 残差分布法 RDS/FluctSplit：`FluctSplitNEQ` 的 `NSchemeCSysNEQ`、`TCNEQDiffTerm`，双锥 CRD 版的 Gnoffo 激波捕捉分裂器 `SysBCxMS`。
- 高阶方法（FR/SFV/SD/DG）均经 `FluxReconstructionNEQ` 等接入 NEQ 物理；VanLeer 等通用分裂器面向完全气体。
- 轴对称源项：`NavierStokes2DNEQAxiSourceTerm`、`TCNEQAxiSourceTerm`（FireII/双锥 2D 轴对称所需）。

### 2.4 隐式时间推进与线性求解

- `NewtonIterator` + PETSc（GMRES/ASM/RCM）、LUSGS 族（BDF2/BDF3/CrankNicholson、块雅可比扰动）、数值雅可比 `NumJacob/NumJacobFast`（可冻结扩散系数雅可比）。
- 化学源项**解析雅可比**的接口框架在 `PhysicalChemicalLibrary`（`flagJac`），Mutation2OLD 路径曾实现；M++ 路径未实现（§5.2）——当前 M++ 算例依赖 PETSc 数值雅可比。

### 2.5 壁面催化边界框架（不依赖 M++ 的催化模型）

- `src/Framework/CatalycityModel.hh:35` 的 provider 工厂 + `NullCatalycityModel`：以 N/O 原子复合系数 Γ_N/Γ_O 描述的催化壁边界条件族 `NoSlipWallIsothermalNSrvtCat*`（`plugins/FiniteVolumeNEQ/`，含 `_nad`/`CatR`/`CatT` 变体），在壁面求解组元扩散平衡并施加催化复合质量/能量通量。
- M++ 路径的催化壁**不走** M++ 的 GSI 模块：适配层 `getGammaN/getGammaO` 未实现（`MutationLibrarypp.cxx:719,725`），催化速率完全由 Framework 侧 CatalycityModel + 壁面 BC 计算。CateIXV（分材料 Γ=0.019/0.19 + 辐射平衡壁温）、Catalicity（Γ_N=0.254/Γ_O=0.105）、ICP2Cat（分段变 Γ）算例均基于此框架。

### 2.6 辐射（完全自实现，零 M++ 依赖）

`plugins/RadiativeTransfer/`（插件共 61 个源文件）：HSNB 高分辨率谱带模型、ESA PARADE 外部库适配层（`plugins/PARADE/ParadeLibrary.hh:35`，与 M++ 适配层同构但对接 PARADE）、Grey 灰气体、ArcJet 谱库；求解器含蒙特卡洛射线追踪（`RadiativeTransferMonteCarlo`、`PhotonTrace`）、离散坐标法（`FiniteVolumeDOM`）、太阳辐射（`FiniteVolumeSolar`）。流场-辐射耦合经 `ChemNEQST` 的 `_hasRadiationCoupling`/`RadRelaxationFactor` 与 `getSourceTermVT` 的 `omegaRad` 通道。RadiativeTransfer 自身代码不直连 M++，但辐射算例通常以 `Mutationpp` 为物性库提供流场状态（如 `huygens_DLR_PARADE_MC.CFcase:38-40`，混合物 `titan19`——该名已不在现库，见附录 B）。

### 2.7 ICP / ArcJet 电磁物理（自实现，仅电导率取库）

感应方程与感应加热源项（`ICPInductionEquationSourceTerm`）、洛伦兹力（`LorentzForceSourceTermComm`）、焦耳加热（`RMSJouleHeatSource`）、电势 φ 双线性系统（ArcJet `ArcJetPhiST`）均为 COOLFluiD 自实现；**唯一天线物性**是电导率 σ，取自所选物性库（M++ `electricConductivity()`，调用点：`plugins/FiniteVolumeICP/RMSJouleHeatSource.cxx:311`、`plugins/FiniteVolumeICP/StagnationPropsBL.cxx:516`、`plugins/FiniteVolumeArcJet/ArcJetST.cxx:205`、`plugins/FiniteVolumePoissonNEQ/PoissonNEQST.cxx:231,374` 等）。

### 2.8 LTE 平衡流插件骨架

`plugins/LTE/`（Euler2DPuvtLTE、NavierStokes3DPvtLTE、Demix 组分分离变体等）：LTE 变量集与方程自实现；平衡组分、平衡 γ/声速、平衡输运由所选库提供（M++ 经 Equil 状态模型；亦可用旧 Mutation）。注意 demixing（组分分离）所需接口 `setElemFractions`/`setElementXFromSpeciesY` 在 M++ 适配层 **NotImplemented**（§5.6）。

### 2.9 ATDModel 自带物性库（完全不用 M++ 的替代路径）

`plugins/ATDModel/ATDModelLibrary.cxx`：Wilke 型混合黏性公式（:235-260）、Candler/Gnoffo(Yos) 热力学/黏性模型名分派（:1506-1507）、热导率/振动热导率/电导率自算（:264,331,379）、Arrhenius 化学源项自实现（:804-825）。这是高焓弧射流算例的独立物性路径，证明 COOLFluiD 具备不依赖外部物性库运行的基本能力。

### 2.10 数值基础设施工具

网格自适应（r-型网格拟合 `MeshFittingAlgorithm`，算例内注册名 MeFiAlgo，`plugins/FiniteVolume/MeshFittingAlgorithm.hh`；`SimpleGlobalMeshAdapter`）、ParMETIS 并行剖分、NEQ+SA 湍流（ArcJet SALTE 系列）、NEQ+k-ω（NEQKOmega）、壁面热流/摩阻后处理（`NavierStokesSkinFrictionHeatFluxCCNEQ` 系列，`plugins/AeroCoef/NavierStokesSkinFrictionHeatFluxCCNEQ.cxx:74-104`）、CUDA GPU 加速（FiniteVolumeCUDA/FluxReconstructionCUDA）。

---

## 3. 经适配层使用的 Mutation++ 功能（API 级映射）

### 3.1 总览

| M++ 模块 | 使用程度 | 入口 API |
|----------|---------|---------|
| Thermodynamics（热力学/状态模型/平衡） | **重度使用** | setState、P、density、mixtureHMass、mixtureEnergyMass、mixtureFrozen/EquilibriumGamma、(equilibrium)SoundSpeed、speciesHOverRT、X/Y convert、speciesMw、mixtureMw、species(i) |
| Transport（输运） | **核心子集使用** | viscosity、frozenThermalConductivity(Vector)、equilibriumThermalConductivity、electricConductivity、stefanMaxwell |
| Kinetics（化学动力学） | **仅净源项** | netProductionRates |
| Transfer（能量交换） | **间接全用** | energyTransferSource（内部按状态模型组合 6 种机制，§4） |
| 平衡求解（MultiPhaseEquilSolver） | **间接使用** | 经 Equil 状态模型 setState 触发 |
| 物性数据库 | **重度使用** | NASA-7/NASA-9/NASA-9-New/RRHO 热力学库、碰撞积分库、VT 弛豫数据、混合物/机理 XML |
| GSI（气固相互作用） | **未使用** | —（§5.1） |
| 磁场/等离子体微观量 | **未使用** | —（§5.4/§5.5） |

### 3.2 热力学与状态模型

| 适配层方法（位置） | M++ API | 用途/调用方 |
|------|---------|------------|
| `setup()`（MutationLibrarypp.cxx:150-256） | `MixtureOptions(name)`、`setStateModel()`、`new Mixture`、`nSpecies/nElements/speciesMw/nEnergyEqns/hasElectrons/speciesCharge`、`speciesHOverRT` 五参数版 + `mixtureHMass(T0)`（0 K 生成焓 H0，供 `ShiftH0`） | 启动时构建混合物；非 Equil 模式另建 Equil 实例 `m_gasMixtureEquil` 供平衡组分查询 |
| `setState(rhoi,T)`（hh:85-97） | `setState(rhoi, T, 1)`（物种分密度+温度向量；TTv 时实参为 [T,Tv]） | 所有 varset 状态更新第一站（§1.3） |
| `pressure(rho,T,tVec)`（cxx:454） | `P()`（状态化读取） | varset 的 pressure 求值 |
| `density(T,P,tVec)`（cxx:441） | LTE 分支 `setState((P,T),1)` + `density()` | Pvty 变量集、LTE 入口 |
| `setDensityEnthalpyEnergy`（cxx:397,421） | `density()` + `mixtureHMass()`（含 `-m_H0` 生成焓平移） | 守恒↔原始变量变换（RhoivtToCons 等） |
| `energy` / `enthalpy`（cxx:486,499） | `setState` + `mixtureEnergyMass()` / `mixtureHMass()` | 能量/焓求值 |
| `gammaAndSoundSpeed`（cxx:322） | `mixtureEquilibriumGamma()` + `equilibriumSoundSpeed()` | LTE 变量集 |
| `frozenGammaAndSoundSpeed`（cxx:338） | `mixtureFrozenGamma()`；声速**自算** √(γp/ρ)（M++ `frozenSoundSpeed()` 被注释，:346-347） | CNEQ/TCNEQ 变量集（如 `Euler2DNEQRhoivtTv.cxx:140`） |
| `getSpeciesTotEnthalpies`（cxx:739） | `speciesHOverRT` **六参数版**（总焓 + ht/hr/hv/he/hf 模式拆分） | TCNEQ 振动/电子能通量（`NavierStokesTCNEQVarSet.ci:192`） |
| `getSpeciesMolarFractions/MassFractions`（cxx:577,587） | `convert<Y_TO_X>` / `convert<X_TO_Y>` | 边界条件、后处理、通量（`RoeVinokurTCNEQFlux.ci:228` 等） |
| `setMoleculesIDs`（hh:144） | `species(i).type()==MOLECULE` + `species(i).name()` | 双温度振动方程组元定位（基类 `NavierStokesNEQVarSet.ci:72`；TCNEQ 派生类另用 getMolecule2EqIDs，`NavierStokesTCNEQVarSet.ci:93`） |
| `setComposition(T,P,x)`（cxx:369） | `m_gasMixtureEquil->setState((P,T),1)` + `X()` + `convert<X_TO_Y>` | 平衡来流/入口（`SubInletEuler1DTtPtYi*`、LTE 变量集、ICP `setComposition+sigma`） |
| `electronPressure`（cxx:478） | **不经 M++**，自算 ρe·Te·R/M_e | 电子能方程 |
| `getMMass`/`setRiGas`（hh:120,132） | 自算（m_y 与 speciesMw 组合，`Mutation::RU`） | 混合摩尔质量、气体常数向量 |

### 3.3 输运特性

| 适配层方法 | M++ API | 调用方（证据） |
|------|---------|--------------|
| `eta(T,P,tVec)`（hh:203） | `viscosity()` | 各 NS 变量集（`NavierStokesCNEQVarSet.ci:190`、`NavierStokesTCNEQVarSet.ci:372,524`、NEQKOmega `NavierStokesNEQKOmegaRhoivt.ci:103`） |
| `lambdaNEQ`（cxx:277） | `frozenThermalConductivity()` | 平动-转动热导率（CNEQ/TCNEQ NS 变量集） |
| `lambdaVibNEQ`（cxx:288） | `frozenThermalConductivityVector(&λ[])`（拆出 TR 分量与各振动模式 λ） | TCNEQ 振动能量方程扩散项（`NavierStokesTCNEQVarSet.ci:217,376,528`） |
| `lambdaEQ`（hh:216） | `equilibriumThermalConductivity()` | LTE 路径 |
| `sigma`（cxx:308） | `electricConductivity()`（T<100 K 钳位） | ICP/ArcJet/PoissonNEQ 全部电磁源项（§2.7） |
| `getRhoUdiff`（cxx:667） | `mixtureMw()` + 自构 Stefan-Maxwell 驱动力 m_df + `stefanMaxwell(&m_df, &rhoUdiff, E)`（E≡0，电场驱动未启用，cxx:687）+ `density()` | 多组元扩散速度（NS 变量集 :112/:209/:350/:502、催化壁 BC :215,238） |

### 3.4 化学源项与能量交换

- `getMassProductionTerm`（cxx:620）→ `netProductionRates(&omega)`：化学非平衡质量源项的唯一入口。`freezeChemistry=true` 时置零（FireII 两阶段策略的冻结相即由此实现）。**雅可比未实现**（TODO，:642），见 §5.2。
- `getSourceTermVT`（cxx:1032）→ `energyTransferSource(&omegav[0])`：振动能量方程源项；`omegaRad` 输出参数未填充（辐射耦合走 RadiativeTransfer 通道）。
- `getSource`（cxx:647）→ `netProductionRates()` + `energyTransferSource()` 组合版。

调用链（证据）：FVM 化学源项 `ChemNEQST.ci:214`；FVM 热源项 `ThermNEQST.ci:226-240`（按库名分派：Mutation2OLD/MutationPanesi/Mutationpp 走 `getMassProductionTerm`+`getSourceTermVT` 分体接口，其余库走 `getSource`）；FR 格式 `CNEQSourceTerm.cxx:152`、`TNEQSourceTerm.cxx:152-166,249`；FluctSplit 格式 `TCNEQSourceTerm.ci:169,190`。

### 3.5 无黏通量与边界条件对库的调用

- 通量分裂器取物性：`RoeTCNEQFlux.ci:51-58,87,144`（getNbSpecies/getMolarMasses/setMoleculesIDs/getExtraData/getRgas）、`RoeVinokurTCNEQFlux.ci:54-71,171,228,295-297`（presenceElectron/setSpeciesFractions/setRiGas）。
- 催化壁 BC：`NoSlipWallIsothermalNSrvtCat.ci:95,175-261`（setSpeciesFractions/pressure/getRgas/getMMass/getRhoUdiff/getNbTempVib/getNbTe）；催化速率本身经 `CatalycityModel` 工厂（:72）在 Framework 侧完成（§2.5）。
- 亚声入口/出口/远场：`SubInletEuler1DTtPtYi(Tv/Te/MultiTv)`、`SubOutletEulerP`、`FarField2DYiPuvt`、`SubInletVTTvNEQ` 等（setComposition/pressure/setDensityEnthalpyEnergy）；壁距外推器 `DistanceBasedExtrapolator*`（40+ 个源文件引用）。

---

## 4. 能量交换机制的间接使用（易误判为"未用"的项）

适配层只显式调用一个函数 `energyTransferSource()`，但 M++ 的 `ChemNonEqTTv` 状态模型在构造时自动挂接全部六种能量交换机制（`src/thermo/ChemNonEqTTvStateModel.cpp:149-163`：OmegaVT+OmegaCV+OmegaCElec 进振动方程；有电子时再加 OmegaET+OmegaCE+OmegaI）：

| 机制 | 物理内容 | 数据 |
|------|---------|------|
| OmegaVT | 平动-振动弛豫（Millikan-White + Park 修正） | `data/transfer/VT.xml` |
| OmegaCV | 化学-振动耦合（非优先离解） | 机理内生 |
| OmegaCElec | 电子冲击离解/电离的化学-电子能量 | 机理内生 |
| OmegaET | 电子-平动弛豫 | 碰撞积分 |
| OmegaCE | 化学-电子能量耦合 | 机理内生 |
| OmegaI | 电离能量项 | 机理内生 |

因此：**双温度（TCNEQ）算例（双锥 Run42、Hornung TCNEQ）间接使用了 M++ 的全部六种能量交换物理**；单温度（CNEQ）算例无振动方程，不涉及；M++ 侧的 Transfer 工厂还支持按 `MixtureOptions` 单独选择机制，COOLFluiD 未暴露该选项（用状态模型默认组合）。

---

## 5. 未被 COOLFluiD 利用的 Mutation++ 功能（差集分析）

以下为 M++ v1.0.5-108 具备、但当前适配层与全部 CFcase 均未使用的能力。按"若使用可带来的收益"排序。

### 5.1 GSI 气固相互作用全模块（最大未用板块）

`src/gsi/GasSurfaceInteraction.h` 及配套：表面平衡求解 `solveSurfaceBalance()`、催化/烧蚀表面反应速率 `surfaceReactionRates`、质量吹出率 `getMassBlowingRate`、表面辐射 `SurfaceRadiation`、速率律（`gamma_const`/`gamma_T`/`sublimation`）、反应类型（`catalysis`/`ablation`）、表面平衡求解器（`phenomenological_mass`/`phenomenological_mass_energy`）、固体属性（steady_state）；`Thermodynamics::surfaceMassBalance`（B' 表，纯碳烧蚀）；独立工具 `bprime`。

- **COOLFluiD 现状**：催化用自写 `CatalycityModel` Γ 常数 + `NoSlipWallIsothermalNSrvtCat*` BC（§2.5）；无烧蚀/升华/热解能力；适配层 `getGammaN/getGammaO` 未实现、`surfaceMassBalance` 零引用（2026-09-12 升级核查 grep 证实）。
- **若接入的收益**：烧蚀热防护（碳/低密度烧蚀材料，M++ 自带 `tacot-air_35` 35 组分 TACOT 混合物即为此设计）、有限速率催化（γ(T) 模型）、表面辐射平衡的物性级求解。当前 tacot-air_35 混合物在 COOLFluiD 中无法发挥作用（无 GSI 通道）。

### 5.2 化学源项解析雅可比 `jacobianRho`

M++ 提供 ∂ω̇i/∂ρj 解析雅可比（`src/kinetics/Kinetics.h:195`，JacobianManager 支持）。适配层 `getMassProductionTerm` 的雅可比分支为 TODO（`MutationLibrarypp.cxx:642`），当前 M++ 算例隐式求解依赖 PETSc 数值雅可比（`NumJacob`）。**影响有实测证据**：FireII 11 组元电离空气化学相四次运行均发散（单阶段两轮 + 重启 run1/run2，`VALIDATION_REPORT.md` §5.2/§8.2），诊断结论为化学刚性——解析雅可比是改善该收敛性的候选路径之一。旧 Mutation2OLD 路径曾有解析雅可比实现（能力评估报告 §2.1），说明 COOLFluiD 侧接口是现成的，缺的只是适配层实现。

### 5.3 多组元扩散矩阵与热导率分量拆分

- `diffusionMatrix()`（Ramshaw/Exact 两种算法）、`averageDiffusionCoeffs`、`heavyThermalDiffusionRatios`（热扩散/Soret）：适配层改用 `stefanMaxwell()` 求解扩散速度（含电场 E 项），未取矩阵形式。
- 热导率分量族 `reactiveThermalConductivity`、`butlerBrokawThermalConductivity`、`soretThermalConductivity`、`internalThermalConductivity`、`rotational/vibrational/electronicThermalConductivity`、`heavyThermalConductivity`、`euken()`：适配层只取 `frozen`（+Vector 版）与 `equilibrium` 两个总热导率。
- **影响**：高超声速边界层内热扩散（Soret）效应与组分分离的精细建模目前不可用；LTE demixing 算例若需精确热扩散亦受限。

### 5.4 磁场各向异性输运

`setBField/getBField`（`Thermodynamics.h:221-226`）与电子子系统带磁场版本的输运量（`electricConductivity()/B`、`electronThermalConductivity(/B)`、`electronDiffusionCoefficient`、`alpha`、`hallParameter`）。COOLFluiD 的 MHD/Maxwell 插件与 NEQ 电磁源项均不读取磁场修正的输运系数（电导率各向同性 `electricConductivity()`）。

### 5.5 等离子体微观参数

`meanFreePath`、`electronMeanFreePath`、`speciesThermalSpeed`、`averageHeavyThermalSpeed`、`electronThermalSpeed`、`electronHeavyCollisionFreq`、`averageHeavyCollisionFreq`、`coulombMeanCollisionTime`、`hallParameter`（`Transport.h:464-480`）。ICP/ArcJet/PoissonNEQ 的电磁建模只用电导率，未用这些诊断量。

### 5.6 热力学/平衡的未用访问器与 demixing

- 比热与熵族：`speciesCpOverR`（3 重载）、`mixtureFrozenCp/Cv`、`mixtureEquilibriumCp/Cv`、`speciesSOverR`、`mixtureSMass/SMole`、`speciesGOverRT`、`speciesSTGOverRT`、`mixtureHMinusH0Mass`——适配层用不到（所需量经焓/内能间接构造；`getCvTr` 直接抛 `NotImplementedException`）。
- 元素组分/demixing：`setElemFractions`/`setElementXFromSpeciesY` 在适配层 **NotImplemented**（`convert<YE_TO_XE>` 等被注释，cxx:513-535）——`plugins/LTE` 的 Demix 变量集若接 M++ 需先补此接口。
- 平衡导数与元素势：`dXidT`、`dXidP`、`dXjdci`、`dRhodP`、`elementPotentials`、`addEquilibriumConstraint`（多相约束平衡）——未用。
- 凝聚相/多相平衡：M++ `MultiPhaseEquilSolver` 具备凝聚相求解接口（`pure_condensed` 等约束机制），但随库混合物 XML（air_5…Mars_19）均未声明凝聚相物种（grep "condensed" 零命中）；COOLFluiD 亦未使用该接口。

### 5.7 状态模型变量集 0/2 与输运算法切换

- `setState` 变量集 0（守恒变量 ρi+ρe 直入，M++ 内部 `getTFromRhoE` 反解温度）与 2（Yi+{P,T[,Tv]}）未被适配层使用——适配层固定用 vars=1，温度由 COOLFluiD 侧给出。若改用 vars=0 可把能量→温度反解移入库内，属可选微优化。
- 输运算法切换 `setViscosityAlgo/setThermalConductivityAlgo/setDiffusionMatrixAlgo`（Wilke/Gupta-Yos/Chapmann-Enskog LDLT/CG；Ramshaw/Exact 扩散）：适配层未暴露 CFcase 选项，一律用 M++ 混合物默认算法。高焓算例无法在 CFcase 层做 Wilke vs Chapman-Enskog 对比。

### 5.8 语言接口与工具程序

- Fortran cwrapper（`interface/fortran/`）与 Python 绑定（nanobind）：COOLFluiD 用 C++ 原生 API，两者未用。
- 工具程序：`checkmix`/`mppequil`/`mppshock` 在**验证工作流**中大量使用（库级核查与正激波参考解，`VALIDATION_REPORT.md` §2/§3.3）但非求解器运行时依赖；`bprime`（B' 表生成）未用（§5.1）。
- M++ v1.0.5-108 已移除的旧模块（ZeroD 反应器、OneD/Rivier 边界层、谱学/辐射谱带、cascade energy）：上游已删，不构成 COOLFluiD 的未用项——但注意 COOLFluiD 的辐射能力（HSNB/PARADE）与 M++ **完全无关**，为自实现。

---

## 6. 能力分工总表

| 能力项 | 归属 | 说明 |
|--------|------|------|
| NEQ/TCNEQ 控制方程、变量集与温度恢复 | COOLFluiD | plugins/NEQ 五个物理模型 + 全套 varset |
| 双温度/电子能量方程组装 | COOLFluiD | ThermNEQST（Park 模型骨架）；Te 方程选项绑定旧库 |
| 多温度（3Tv+Te）| COOLFluiD + 旧 Mutation2 | M++ 无多 Tv 状态模型 |
| 化学反应速率与净生成源项 | **M++** | netProductionRates + 混合物 XML 机理 |
| 能量交换源项（VT/CV/CE/ET/CElec/I）| **M++** | energyTransferSource（TTv 自动组合，§4） |
| 热力学状态量（p/ρ/h/e/γ/a/物种焓）| **M++**（声速冻结版 COOLFluiD 自算） | §3.2 |
| 输运系数（黏度/热导/振动热导）| **M++** | §3.3 |
| 多组元扩散速度 | **M++**（stefanMaxwell）| 驱动力构造在 COOLFluiD 侧 |
| 电导率 σ | **M++** | ICP/ArcJet/PoissonNEQ 唯一天线物性 |
| 平衡组分（LTE）| **M++** | Equil 状态模型内部多相平衡求解器 |
| 无黏/黏性通量格式 | COOLFluiD | AUSM+MS 族、Roe/RoeVinokur-NEQ、RDS-CRD |
| 隐式时间推进/线性求解 | COOLFluiD | Newton+PETSc、LUSGS、BDF2/CN |
| 化学源项解析雅可比 | **M++ 路径未闭环** | 接口在 COOLFluiD，M++ 有 `jacobianRho`，适配层 TODO（§5.2）；旧 Mutation2OLD 路径曾实现 |
| 壁面催化（Γ 系数模型）| COOLFluiD | CatalycityModel + Cat 壁面 BC 族 |
| 壁面催化（有限速率/表面平衡）、烧蚀、升华、吹出 | （未实现）| M++ GSI 模块具备，未接入（§5.1）|
| 辐射物性与传输 | COOLFluiD（+PARADE 外部库）| HSNB/MC/DOM；与 M++ 无关 |
| ICP/ArcJet 电磁源项 | COOLFluiD | 感应方程/洛伦兹力/焦耳加热 |
| 物性数据库（热力学/碰撞积分/机理）| **M++** | NASA-7/9、RRHO、collisions.xml、混合物 XML |
| LTE 查找表加速 | COOLFluiD（插值对象为 M++ 量）| LookupTable2D |

---

## 7. 集成维护与 M++ 升级 SOP

（本节吸收自原 `MUTATIONPP_UPGRADE_ADAPTATION_REPORT.md`，该报告自 2026-09-13 起由本文档替代。）

### 7.1 依赖面结论

- 全树唯一 M++ 消费者是适配层 `libMutationppI.so`；内核与其余插件对 M++ **零链接、零接触**。
- M++ 重编/升级后**无需全量重编 COOLFluiD**，但适配层必须重编：适配层编译期内嵌 `<mutation++.h>`（内联函数、类布局），存在布局漂移风险。实测案例（2026-09-12，bb054e5→e8edf4f）：`ldd -r` 在重编前即 0 个未解析符号（符号级本就兼容），重编属消除布局风险的例行操作，约 2 分钟。
- 升级影响核查方法：`git diff --stat <旧HEAD>..<新HEAD>` 聚焦 `Mixture.h` 与适配层实际使用的 API（`MixtureOptions`、`Mixture` 构造、`nSpecies/nElements/nEnergyEqns/hasElectrons/speciesCharge/speciesMw/setState/viscosity/equilibriumThermalConductivity/frozenThermalConductivity(Vector)/electricConductivity/netProductionRates/energyTransferSource/stefanMaxwell/speciesHOverRT/convert`）是否变签名。

### 7.2 M++ 更新标准操作流程（5 步，已实测）

```bash
# 1. 检查未跟踪自定义数据文件（M++ 侧做过 git clean 类清理必丢，见 §7.3）
ls /home/tang/packages/Mutationpp/data/mixtures/n2_2.xml \
   /home/tang/packages/Mutationpp/data/mechanisms/n2_2_Park.xml
# 丢失则恢复：
#   cp -p ~/packages/SU2/nemo_validation/mpp_2021/data/{mixtures/n2_2.xml,mechanisms/n2_2_Park.xml} 至对应目录

# 2. 数据快速自检
bash -ic '/home/tang/packages/Mutationpp/install/bin/checkmix n2_2'

# 3. 重编适配层（唯一 M++ 消费者；不要全量 make）
cd /home/tang/packages/COOLFluiD/build/optim && bash -ic 'make MutationppI'

# 4. 刷新 install/lib（配置期生成的 .cu 文件齐全时可行；缺失时按 §7.4 恢复）
bash -ic 'make install'

# 5. 冒烟验证（10 步）
#    用例 hornung_FVM_NS_CNEQ_EULER_n2_2_V3_SMOKE.CFcase，
#    运行命令见 VALIDATION_REPORT.md §8.0 启动模板（-np 1）；
#    出现 "COOLFluiD Environment Terminated" 且 .plt 输出正常即通过
```

按改动规模分档：仅 `.cpp` 实现变化 → 符号层面大概率兼容，SOP 照走；跨版本升级（数据库/头文件变动）→ 另需 `grep -h "mixtureName" <算例>.CFcase` 核对在跑算例的混合物名仍存在于新库 `data/mixtures/`（历史案例：`N2_neut/N2_TTv/air11nasa9` 在现库失效 → 适配为 `n2_2/air_11`）。

### 7.3 自定义数据文件风险（升级必查）

`n2_2.xml`（混合物）与 `n2_2_Park.xml`（机理）**不在 M++ git 仓库内**（上游 `data/mixtures/` 仅 air_5/air_11/CO2_8/Mars_19/tacot-air_35），是本地未跟踪文件（纯 N₂ Run28/Run42 工况所需），M++ 更新/清理时易丢失。运行时数据目录由 `MPP_DATA_DIRECTORY=/home/tang/packages/Mutationpp/data` 指向源码树 data/，故每次更新 M++ 源码后必须确认这两个文件仍在（SOP 第 1 步）。

### 7.4 相关风险清单（git clean 类操作）

- COOLFluiD：`plugins/FiniteVolume/LaxFriedFlux.cu`、`plugins/FluxReconstructionMethod/LaxFriedrichsFlux.cu`——CMake 配置期 `EXECUTE_PROCESS(cp .cxx .cu)` 生成的 CUDA 文件，git 不跟踪；缺失时 `make install` 报 cc1plus 错误。恢复：`cp -p .cxx 同名.cu`（保留时间戳免重编 nvcc）或重跑 cmake configure。
- M++：§7.3 两个数据文件。
- 根治建议：`EXECUTE_PROCESS` 改 `add_custom_command`；n2_2 数据文件纳入某处版本管理。

### 7.5 适配层已知数值适配与限制

1. `MinT`/`MinRhoi` 钳位默认 0——TCNEQ/刚性算例应在 CFcase 显式设置（双锥 Run42 用 MinT=200/MinRhoi=1e-10）。
2. 质量分数断言已改为截断到 [0,1]、非正压力返回安全值（2026-09-08 鲁棒化，FireII 冒烟验证）。
3. `setState` 按 `m_Tstate.size()`（=nEnergyEqns）传递温度向量：TCNEQ 传 [T,Tv]、M++ TTv 变量集 1 直接消费两温度；适配层 hh:92 的 "this needs to be fixed for 2-temperatures" 注释已过时（§1.3）。M++ 侧 vars=0 的能量反解路径（getTFromRhoE）未被适配层使用——温度恢复始终由 COOLFluiD 侧给出。
4. `getGammaN/getGammaO` 未实现——M++ 路径催化壁必须走 Framework CatalycityModel。
5. `getSourceEE` 未实现——电子能量方程（Te）路径绑定旧 Mutation2OLD 库。
6. `mppshock` 工具低密度工况挂起（>5 min 无输出，M++ 工具层牛顿迭代问题）——不影响 COOLFluiD 运行时（不调用该工具），验证中避开低密度参数即可。

---

## 8. 集成正确性的实测支撑（摘要，证据见 VALIDATION_REPORT.md）

| 验证项 | 结论 | 出处 |
|--------|------|------|
| M++ 库级独立核查（7 项） | checkmix / mppequil（常压+低压）/ mppshock 冻结+平衡正激波 / setState 语义 / VT 源项 / ABI 全部通过 | VALIDATION_REPORT §2 |
| Hornung N₂ 圆柱 V3（Euler CNEQ，n2_2） | 38054 步收敛；近壁 T +1.2% / p −4.7% / 密度比 −0.8% vs mppshock 平衡解；δ/R=0.31 vs 实验 0.22（粗网格偏冻结侧，机理明确） | VALIDATION_REPORT §3 |
| M++ 升级适配（bb054e5→e8edf4f） | 重编适配层 + 数据恢复后 10 步冒烟通过（2026-09-12） | 本报告 §7（吸收自原升级报告） |
| FireII 冻结相 / 双锥 Run42 冒烟 | 物理有效 / 越过全部历史崩溃点；生产运行待超算 | VALIDATION_REPORT §5/§0.3/§8.1 |

**对 §5 差集的实践印证**：FireII 化学相四次运行发散的诊断（11 组元化学刚性 + 数值雅可比）与 §5.2（未接 `jacobianRho`）相互印证，是差集分析中"最值得优先补齐项"排序的依据。

---

## 附录 A：适配层未实现/抛出接口清单（`MutationLibrarypp`）

| 方法 | 状态 | 说明 |
|------|------|------|
| `getCvTr` | NotImplementedException | 平动-转动 cv（COOLFluiD 侧经 gamma 换算） |
| `transportCoeffNEQ` | NotImplementedException | NEQ 输运组合接口（用分体 lambdaNEQ/lambdaVibNEQ/eta 替代） |
| `getSourceEE` | NotImplementedException | 电子能量源项（Te 路径走旧库） |
| `getTransportCoefs` | NotImplementedException | 组合输运接口（用分体接口替代） |
| `getDij_fick` | NotImplementedException | Fick 扩散矩阵（用 stefanMaxwell 替代） |
| `getGammaN` / `getGammaO` | NotImplementedException | 催化系数（用 Framework CatalycityModel） |
| `setSpeciesMolarFractions` | NotImplementedException | 用 setSpeciesFractions（质量分数）替代 |
| `setElemFractions` / `setElementXFromSpeciesY` | NotImplemented（convert 注释） | demixing 元素组分（§5.6） |
| `getMassProductionTerm` 的 Jacobian | TODO（:642） | 解析雅可比（§5.2） |
| `getSourceTermVT` 的 `omegaRad` | 未填充 | 辐射源项走 RadiativeTransfer 通道 |
| `frozenSoundSpeed` 调用 | 被注释（:346） | COOLFluiD 自算 √(γp/ρ) |
| `electronPressure` | 自算 | 不经 M++ |

## 附录 B：M++ v1.0.5-108 混合物数据库与 COOLFluiD 可用性

| 混合物 | 来源 | COOLFluiD 可用性 |
|--------|------|-----------------|
| `air_5`（5 组元离解空气） | 上游 | ✅ ShockTube（本轮适配） |
| `air_11`（11 组元电离空气） | 上游 | ✅ FireII（本轮适配，物种顺序重排） |
| `CO2_8` / `Mars_19`（火星大气，全气相物种） | 上游 | 仓库无直连算例（SphereCO2 目录实际配置为 air7） |
| `tacot-air_35`（TACOT 烧蚀碳-空气） | 上游 | ❌ 需 GSI 模块（§5.1），当前不可用 |
| `n2_2` + `n2_2_Park` 机理 | **本地自定义**（不在 git 内） | ✅ Hornung V3 / 双锥 Run42（§7.3 维护注意） |

历史失效名（旧算例→现库）：`N2_neut`/`N2_TTv`→`n2_2`、`air11`/`air11nasa9`→`air_11`、`titan19`（Huygens 辐射算例）→现库无（需自定义）。原版 M++ 算例（Hornung NS CNEQ/TCNEQ/MeFiAlgo/Debug、IXV LTE M++）混合物名全部失效且缺 `libShapeFunctions`，运行前需两处适配（`high_enthalpy_testcases_report.md` §4 修正块）。
