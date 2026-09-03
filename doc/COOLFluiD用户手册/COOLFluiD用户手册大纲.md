# COOLFluiD 用户手册编写大纲（2026-08 核对修订版）

**版本基准**：COOLFluiD 2013.9（Kernel 2.5.0），代码库路径 `/home/tang/packages/COOLFluiD`
**手册定位**：面向 CFD/多物理场仿真用户与二次开发者的系统性参考手册，覆盖从安装、求解、后处理到源码级扩展的全流程。
**写作约定**：每一章按"概述 → 原理 → 操作步骤 → 参数表 → 示例 → 常见问题"的层次展开；所有代码路径、类名、CFcase 关键字须与代码库实际内容核对一致；每章末尾附"核对清单"。
**核对状态**：本版大纲已对照代码库（`src/`、`plugins/`、`apps/`、`cmake/`、`tools/`、`doc/`）逐项核对，修正了此前版本中的类名、选项名、目录名与算例描述错误，并补充了遗漏的插件与机制。文件数量统计（`src/` 1186、`plugins/` 9746：3301 `.hh`、2930 `.cxx`、1019 `.CFcase`、751 `.xz`）经 `find` 实测确认无误。

---

## 第 0 章 手册使用说明与阅读指南

- 0.1 手册的组织方式与各章读者定位（初学者 / 一般用户 / 高级用户 / 开发者）
- 0.2 术语与排版约定（`.CFcase` 关键字、类名、命令行、文件路径的书写格式）
- 0.3 快速上手路线图：五个典型使用场景的最短路径
  - 场景 A：跑通第一个 Euler 算例（`plugins/NavierStokes/testcases/Cylinder/cyl_Pg_M15_FVM_1st2nd.CFcase`）
  - 场景 B：高超声速热化学非平衡钝体算例（`plugins/NEQ` + `plugins/FiniteVolumeNEQ`）
  - 场景 C：MHD 多流体算例（`plugins/FiniteVolumeMultiFluidMHD`）
  - 场景 D：高阶方法算例（`plugins/FluxReconstructionMethod` / `plugins/SpectralFD`）
  - 场景 E：增加一个自定义插件（配合第 11 章）
- 0.4 手册与现有资料的关系
  - `doc/Manuals/` 下：`COOLFluiD_FVM.pdf/.tex`、`COOLFluiD_FVM_MHD.pdf/.tex`、`COOLFluiD_FVM_ICP.pdf/.tex`、`COOLFluiD_FVM_ATD.pdf/.tex`、`COOLFLuiD_Manual.pdf`、`FluxReconstructionManual.pdf/.tex`、`COOLFluiD_RDS_UnsteadyNavierStokes.tex`、`COCONUT_user_manual.pdf`（另含 `geom_torch.pdf`、`torch_*.pdf` 等附图文档）
  - Doxygen 文档（`doc/doxygen.config.in` 生成，`make doc`）
  - `doc/COOLFluiD_高焓高超声速求解能力评估报告.md`、`doc/high_enthalpy_testcases_report.md`
  - 本手册已写章节草稿：`doc/COOLFluiD用户手册/第0章~第11章 .md`
- 0.5 获取帮助：GitHub 仓库（andrealani/COOLFluiD）、Wiki（github.com/andrealani/COOLFluiD/wiki）、Twitter @coolfluid

---

## 第 1 章 项目概述与背景

### 1.1 COOLFluiD 是什么
- 1.1.1 定位：面向 CFD 与多物理场（等离子体、MHD、传热、结构、辐射、电磁）的面向对象 HPC 仿真平台，可构建自定义并行 PDE/粒子求解器，支持任意数据结构
- 1.1.2 全称与含义：**Computational Object-Oriented Libraries for Fluid Dynamics**（COOL = Computational Object-Oriented Libraries；FluiD = Fluid Dynamics；代码中常缩写为 CF）。注：旧版大纲中的 "COmpact Object Oriented PDE solving Library for multi-physic fuID applications" 与官网不符，已修正
- 1.1.3 核心理念：内核-插件分离、运行时动态组装（plug-and-play，自注册、自配置对象）、物理模型与数值算法完全解耦、可接口/耦合既有求解器

### 1.2 发展历史
- 1.2.1 起源：2002 年比利时冯·卡门流体动力学研究所（VKI）启动
- 1.2.2 与 KU Leuven 数学等离子体天体物理中心（CmPA）的长期合作（MHD/空间等离子体方向，COCONUT 日冕算例群）
- 1.2.3 版本沿革：Kernel 1.x → 2.x；当前版本 2013.9（`CMakeLists.txt` 中 `COOLFLUID_VERSION 2013.9`、`CF_KERNEL_VERSION 2.5.0`）
- 1.2.4 开源协议：LGPL v3（`LICENSE`、`doc/gpl.txt`、`doc/lgpl.txt`）

### 1.3 主要功能特性总览
- 1.3.1 物理覆盖：可压缩 Euler/NS/RANS（SA、k-ω、GReKO γ-Reθ 转换、γ-θ GammaAlpha）、热化学非平衡（2T/多温度）、LTE、MHD（理想/电阻/多流体/熵稳定）、Maxwell、ICP 电感耦合等离子体、ArcJet 弧加热、ATD 电弧热等离子体、辐射传输、传热/结构耦合、燃烧（FiniteVolumeCombustion）、拉格朗日粒子（LagrangianSolver）
- 1.3.2 数值覆盖：有限体积（单元中心 FVMCC）、残差分布法（RDS/FluctSplit，天然节点中心）、间断伽辽金（DG）、通量重构（FR/CPR）、谱差分（SD/SpectralFD）、谱体积（SV/SpectralFV）、有限元（FE）
- 1.3.3 计算能力：MPI 并行（含混合 MPI/CUDA）、CUDA GPU 加速（ViennaCL）、并行 I/O、隐式/显式时间推进、网格自适应与动网格、子系统耦合（串行/并发）、动态负载平衡（ParMetis）
- 1.3.4 规模数据（经实测，2026-09 复核更新）：`src/` 内核 1186 文件，`plugins/` **9747** 文件（3301 `.hh`、2930 `.cxx`、1019 `.CFcase`、751 `.xz` 数据包；旧记 9746，见附 C.10 第 109 条），仓库总计约 2.2 万文件

### 1.4 适用领域
- 1.4.1 高超声速与高焓流动：钝体绕流、激波-激波/激波-边界层干扰、热流预测（`DoubleEllipse`、`F15`、`BluntBody2D`、`DoubleCone` 等算例群）
- 1.4.2 等离子体流动：ICP 风洞（`ICP`、`FiniteVolumeICP`）、弧加热风洞（`ArcJet`、`FiniteVolumeArcJet`）、ATD 模型（`ATDModel`）
- 1.4.3 磁流体动力学：天体物理（COCONUT 日冕/太阳风算例）与再入磁流体控制（`MHD`、`MultiFluidMHD`、`EntropyMHD`、`Maxwell`）
- 1.4.4 气动声学与线性化流动（`LinEuler`、`LinearAdv`、`LinearAdvSys`）
- 1.4.5 LES/湍流基础研究（`LES`、`LESvki`、`LESDataProcessing`、`SA`、`KOmega`、`GReKO`、`GammaAlpha`、`NEQKOmega`）
- 1.4.6 传热与流固耦合（`Heat`、`StructMech`、`StructMechHeat`、`SubSystemCoupler`、`ConcurrentCoupler`）

### 1.5 与其他 CFD 软件的对比
- 1.5.1 对比维度：物理模型广度、数值方法多样性、二次开发难度、并行/GPU 支持、社区与文档、许可证
- 1.5.2 对比对象：OpenFOAM（通用框架、FVM 单一）、SU2（adjoint/优化强）、FUN3D/AFLR 生态（NASA 商用级）、PLASMAO/MACH 等等离子体专用代码、自研 MHD 代码（BATS-R-US 类）
- 1.5.3 COOLFluiD 的差异化优势：同一框架下 FVM/RDS/DG/FR/SD/SV 共存可比较、非平衡热化学+辐射+催化的完整链条、MHD 多流体能力、太阳等离子体数值模拟（COCONUT）
- 1.5.4 劣势与注意点：文档分散、编译依赖较老（CMake ≥ 2.8.3）、Kernel 版本演进带来的 API 差异

---

## 第 2 章 整体架构设计

### 2.1 总体分层架构
- 2.1.1 三层结构：应用层（`apps/Solver`）→ 内核层（`src/`）→ 插件层（`plugins/`）
- 2.1.2 运行时动态装载机制：`.CFcase` 中 `Simulator.Modules.Libs = libPetscI libCFmeshFileReader libCFmeshFileWriter libTecplotWriter libNavierStokes libFiniteVolume libNewtonMethod ...` 触发 `libdl` 加载与工厂注册（实例见 `cyl_Pg_M15_FVM_1st2nd.CFcase`）
- 2.1.3 静态编译模式：CMake 选项 `CF_ENABLE_SINGLEEXEC`（编译宏 `CF_HAVE_SINGLE_EXEC`），`apps/Solver/PluginsRegister.hh` 统一注册（注：选项名是 `SINGLEEXEC` 无下划线）

### 2.2 内核模块详解（`src/` 目录逐子目录说明）
- 2.2.1 `src/Common/`（188 文件）：基础设施
  - 对象模型：`OwnedObject`、`SetupObject`、`NamedObject`、`TaggedObject`（对象基类族，非 `CFObject`）、`SharedPtr/SafePtr/SelfRegistPtr`、`FactoryRegistry`、`FactoryBase`（完整 `Factory` 实现位于 `src/Environment/`）
  - 并行基础设施：`PE`（MPI 封装）、`PEInterface`、`PEFunctions`（注：无 `PEAPI`）
  - 工具：`StringOps`、`CFLog` 日志、`OSystem`、`ProcessInfo`（含 Linux/MacOSX/Win32 变体）、`Stopwatch`、`TimePolicies`、`FileDownloader`、`FilesystemException`、异常体系（`Exception`、`BadValueException`、`ShouldNotBeHereException` 等）
  - 注：`MathConsts`/`MathTools` 位于 `src/MathTools/`，不在 Common
- 2.2.2 `src/Config/`（46 文件）：配置系统
  - `ConfigObject`（`configure()`、`getConfigOptions()`）、`Option`、`OptionList`、`OptionT`（类型化选项，含数组/向量选项）、`ConfigFileReader`（解析 `.CFcase` 键值对）、`ConfigArgs`、`NestedConfigFileReader`、`XMLConfigFileReader`、`ConfigFacility`；另有 `OptionMarkers`、`OptionValidation`（注：**`ConfigRegistry` 不在此目录**，它在 `src/Environment/`）
  - 异常：`BadMatchException` 等；注：`BadFormatException` 位于 `src/Framework/`，`ShouldNotBeHereException` 位于 `src/Common/`
  - 注：**无 `OptionArray` 类**（数组选项由 `OptionT` 特化实现）
- 2.2.3 `src/Environment/`（45 文件）：运行环境
  - `CFEnv`（初始化/终止、`configure`/`setup`/`unsetup`/`terminate`）、`DirPaths`（库搜索路径 `--ldir`、基目录 `--bdir`）、`CFEnvVars`、`Factory`/`FactoryRegistry`（环境级注册）、**`ConfigRegistry`**（`src/Environment/ConfigRegistry.hh/.cxx`）、`ModuleRegister`（插件模块注册基类）
  - 注：**`TimeTable` 在代码树中不存在**（全仓库 0 命中），旧大纲该条目已删除
- 2.2.4 `src/Framework/`（567 文件，内核核心）：本手册第 2.3 节展开
- 2.2.5 `src/MathTools/`（66 文件）：`RealMatrix/RealVector`、`Matrix`、`MathFunctions`、`MathConsts`、`MathChecks`、`LeastSquaresSolver`、插值工具、`.inc` 表文件
- 2.2.6 `src/ShapeFunctions/`（202 文件）：各型单元的 Lagrange 形函数与导数（`LagrangeLineP1`…`TriagP2`、`TetraP2`、`ContourGaussLegendre*Lagrange*` 族等）与积分点（Gauss-Legendre 等）；注：`CFQuadrature/CFIntegration` 枚举在 `src/Framework/`（见 5.4.3）
- 2.2.7 `src/logcpp/`（65 文件）：内置 log4cpp 日志子系统（`Category`、`Priority` 等）
- 2.2.8 `src/UnitTests/`：内核单元测试组织方式（`MathTools/` 下 `utest-*.cxx`、`test-tools-cfmesh-compare.cxx`；`CF_ENABLE_UNITTESTS` 启用，默认 OFF；注：插件中无 `testsuite/` 目录）

### 2.3 `src/Framework` 内部架构（类职责地图）
- 2.3.1 仿真管理链
  - `Maestro` / `SimpleMaestro`：多 SubSystem 编排（如流-固耦合中流体与结构两个子系统）
  - `Simulator`：读取 CFcase、构建子系统、生命周期管理（`apps/Solver/coolfluid-solver.cxx` 主流程：命令行解析 → `CFEnv.initiate` → 解析 CFcase → `CFEnv.configure` → 创建 `SimpleMaestro` → 创建 `Simulator` → `maestro->call_signal("control")`，均已实测核对）
  - `SubSystem` / `SubSystemStatus`：单一求解子系统的执行器
  - `SimulationStatus`、停止条件（`StopCondition = MaxNumberSteps | Norm`）
- 2.3.2 物理模型抽象
  - `PhysicalModel`（抽象基类在 Framework；具体模型类位于插件中，如 `plugins/NavierStokes` 的 `Euler2D/3D`、`NavierStokes2D/3D`，`plugins/NEQ` 的模板类 `NavierStokesTCNEQVarSet`）、`PhysicalProperty`、`VarSet`（变量集）
  - 变量集命名（跨插件）：`Cons`、`Puvt`、`Prim`、`Roe`、`Symm`（plugins/NavierStokes）；`Rhoivt` 有两义——NavierStokes 的 `Euler2DRhovt`（无组分，r-hov-t）与 NEQ 的 `Euler2DNEQRhoivt`（组分+振动温度）；NEQ 另有 `RhoivtTv`（多振动温度+电子温度）、`Pivt`、`RoeVinokur`（`Euler2DNEQRoeVinokur`、`RoeVinokurTCNEQFlux`）
  - `ConvectiveVarSet`、`DiffusiveVarSet`、`ConvectionPM/ConvectionDiffusionPM` 物理项描述
- 2.3.3 网格与几何
  - `MeshBuilder`、`TopologicalRegionSet`（TRS：`InnerFaces`、`NoSlipWall`、`SuperInlet` …）、`TopologicalRegion`
  - `GeometricEntity`（`Cell`、`Face`、`Edge`、`State`、`Node`）、`GeoBuilder` 族（`CellTrsGeoBuilder`、`FaceTrsGeoBuilder`、`FaceCellTrsGeoBuilder`）
  - `CFGeoShape`（单元形状枚举）、`CFPolyOrder`（P0–P10，枚举 ORDER0–ORDER10）、`CFSide`、`CFPolyForm`、`CFQuadrature`、`CFIntegration`
  - 网格 IO 抽象：`FileReader/FileWriter`、`CFmeshFileReader/Writer`（含二进制 `.ci` 显式模板）、`BaseCFMeshFileSource`
- 2.3.4 数据存储与交换
  - `DataStorage`、`DataSocket`、`DataHandle`（含 MPI 变体 `DataHandleMPI`）、`DataSocketSink/Source`、`DataBroker`、`ElementDataArray`、`DynamicDataSocketSet`
  - 套接字生命周期：allocate → 数据访问 → 释放；插件间数据共享的标准途径
- 2.3.5 数值方法抽象
  - `SpaceMethod`（空间离散接口）、`ConvergenceMethod`（时间推进接口）、`ConvergenceMethodData`、`LinearSystemSolver`（LSS）与 `EigenSolver`、`BlockAccumulator`（分块矩阵装配，含 CUDA 基类 `BlockAccumulatorBaseCUDA`）
  - 稀疏结构：`CellCenteredSparsity`、`CellVertexSparsity`、`CellVertexSparsityNoBlock`
  - Provider 机制：`BaseMethodCommandProvider`、`BaseMethodStrategyProvider`（CFcase 中命令字符串 → 类实例）
- 2.3.6 通用命令组件
  - 初始化/边界条件命令（`InitState`、`BaseSetupFVMCC` …）、法向计算（`ComputeFaceNormals*P1`）、CFL/DT 控制（`CFL`、`ComputeCFL`、`ComputeDT`、`DetermineCFL`、`ConstantDTWarn`）
  - 范数与收敛监测：`ComputeNorm`、`ComputeL2Norm`、`AbsoluteNormAndMaxIter`、`ComputeAllNorms`
  - 外推：`DistanceBasedExtrapolator`、虚拟单元态 `ComputeDummyStates`
  - 数据处理：`DataProcessing`、`DataProcessingMethod`、输出过滤 `FilterRHS`/`IdentityFilterRHS`/`LimitFilterRHS`、`EquationFilter`/`NullEquationFilter`、状态过滤 `FilterState` 族
  - 耦合接口：`CouplerData`、`CouplerMethod`、`CollaboratorAccess`、`EquationSubSysDescriptor`
  - 网格动平衡：`DynamicBalancerMethod`（+ `DynamicBalancerMethodData`）
  - CUDA 支持：`CudaDeviceManager`（.cu）、`CudaTimer`、`BlockAccumulatorBaseCUDA`
  - 交互参数：`InteractiveParamReader`（`.inter` 文件）

### 2.4 数据流与一次迭代的执行流程
- 2.4.1 启动流程图：命令行解析（`--scase` 等）→ `CFEnv` 初始化 → 加载插件库（`Simulator.Modules.Libs`）→ 工厂注册 → 创建 `Maestro`/`Simulator` → 解析 CFcase → 构建 `SubSystem`
- 2.4.2 SubSystem 内部流水线：`MeshCreator` 读网格 → `PhysicalModel` 建立 → `listTRS` 声明拓扑 → SpaceMethod 的 Setup/UnSetup 命令 → 迭代循环（ComputeTimeStep → ComputeRHS → LSS solve → UpdateSolution → 输出/收敛判断）
- 2.4.3 以 `doubleEllipseNS_PG.CFcase`（`plugins/NavierStokes/testcases/DoubleEllipse/`，实测存在）为实例的完整执行走查（逐行 CFcase → 对应类与函数）
- 2.4.4 命令/策略工厂映射表（CFcase 字符串 ↔ C++ Provider 类）

### 2.5 并行计算框架
- 2.5.1 MPI 并行：`PE` 封装、`CF_HAVE_MPI`、虚拟单元（ghost cell）/虚拟态（ghost state）机制、`ParMetisBalancer` 动态负载平衡、并行 IO 注意事项
- 2.5.2 CUDA GPU 加速：`CF_ENABLE_CUDA`、`FiniteVolumeCUDA` 与 `FluxReconstructionCUDA` 插件、`CudaDeviceManager`、`CF_CUDA_MALLOC`→`CF_HAVE_CUDA_MALLOC`、ViennaCL（`CF_ENABLE_VIENNACL`→`CF_HAVE_VIENNACL`）
- 2.5.3 OpenMP：`CF_ENABLE_OMP`（→`CF_HAVE_OMP`）现状与限制
- 2.5.4 并行运行模式：`CF_ENABLE_PARALLEL_VERBOSE/DEBUG`、多 CPU 测试（`CF_TESTCASES_NCPUS`）

### 2.6 目录结构与文件组织
- 2.6.1 顶层目录：`src/`、`plugins/`、`apps/`、`cmake/`、`config/`（`coolfluid_config.h.in` 等模板）、`doc/`、`tools/`（`conf`、`dev`、`MeshGeneration`、`scripts`、`style`、`svn`、`tecplot`、`templates`、`win32`，另有 `apply_all_fixes.sh` 等脚本）、`packages/`（内置 `mpich-3.1.3.tar.gz`、`parmetis-4.0.3.tar.gz` 源码包）、`pics/`、`videos/`（MHD 可视化 mp4）、`prepare.pl`（构建配置脚本）、`build.sh`（本地一键构建脚本）、`coolfluid.conf`（本机构建配置）
- 2.6.2 单个插件的标准布局：`CMakeLists.txt`（用 `CF_ADD_PLUGIN_LIBRARY` 注册）+ 可选外部依赖查找 `*.cmake`（如 `FindPetsc.cmake`、`FindTrilinos.cmake`）、源码平铺（`Xxx.hh/.cxx`）、`*.ci` 显式模板实例化、`testcases/`（CFcase+CFmesh+参考数据）；注：不存在 `coolfluid-XXX.cmake` 文件，也不存在 `testsuite/` 目录（单元测试集中在 `src/UnitTests/`）
- 2.6.3 命名约定：变量集后缀（`Cons/Puvt/Rhoivt/...`）、维度后缀（`2D/3D`）、方法缩写（`FVMCC`、`RDS`、`FR`、`SD`、`SV`）
- 2.6.4 构建产物布局：`build/dso/`（动态库符号链接/拷贝目录）、`build/apps/Solver/coolfluid-solver`、`install/` 安装树（`bin/lib/include/coolfluid/data`）

### 2.7 插件注册与工厂机制原理
- 2.7.1 插件加载链（**实测，注意：本代码树中不存在 `LoadLib()` 或 `COOLFluiD::Plugin::registerPlugins()` 这样的入口函数**）：`Simulator.Modules.Libs = libXxx` → `src/Environment/ModuleLoader.cxx` 的 `loadModule()`（:78，若名字以 `lib` 开头则**剥掉前 3 个字符**）→ `OSystem::getLibLoader()->load_library(name)` → `src/Common/PosixDlopenLibLoader.cxx:46` 的 `dlopen("lib<Xxx>.so", RTLD_LAZY|RTLD_GLOBAL)`（:78，**不做任何符号查找**）→ 插件内各 `ObjectProvider` 的**全局对象在静态初始化阶段自注册**进 FactoryRegistry。插件身份由形如 `NavierStokesModule : public Environment::ModuleRegister<NavierStokesModule>`（`plugins/NavierStokes/NavierStokes.hh:21`，须实现 `static getModuleName()`/`getModuleDescription()`）声明
- 2.7.2 三类 Provider 的注册模式（带代码示例）
- 2.7.3 `.CFcase` 字符串 → Provider 查找 → 实例化 → `configure()` 的完整时序

---

## 第 3 章 数学与物理模型

### 3.1 控制方程体系
- 3.1.1 可压缩 Euler 方程：模型插件 `Burgers`（一维/标量）、`NonLinearAdv`、`RotationAdv`、`RotationAdvSys`、`LinearAdv/LinearAdvSys`（线性模型库）、`NavierStokes` 插件中的 `Euler2D/3D` 模型
- 3.1.2 Navier-Stokes 方程：层流（`NavierStokes2D/3D`）、无量纲化与参考值体系（`refValues`、`refLength`、`Reynolds`、`machInf`、`tempRef`）
- 3.1.3 RANS/湍流模型：`SA`（Spalart-Allmaras）、`KOmega`（k-ω 系）、`GReKO`（γ-Reθ 转换模型 + k-ω，`Euler2DGReKO*`/`Euler2DGReKOLogO*` 等；注：无 EARSM）、`GammaAlpha`（γ-θ 转换）、`NEQKOmega`（非平衡 + k-ω）、`LES/LESvki`（亚格子模型：`Smagorinsky`、`WALES`（WALE）、`Clark`、`Gradient`；注：无 Vreman/DynamicSmagorinsky）
- 3.1.4 MHD 方程：理想 MHD（`MHD` + `FiniteVolumeMHD`：`MHD2DCons/Prim`、`MHD3DCons` 等，投影修正 `MHD2DProjectionCons` 族变量集、Powell 格式）、电阻 MHD、熵修正（`EntropyMHD`：`EntropyMHD3DCons` 等）、多流体 MHD（`MultiFluidMHD`：双流体/多组分等离子体）、Maxwell 方程（`Maxwell`、`FiniteVolumeMaxwell`）
- 3.1.5 热化学非平衡（NEQ）：
  - 变量集体系：`Cons`、`Rhoivt`（组分+振动温度，`Euler2DNEQRhoivt`）、`RhoivtTv`（多振动温度+电子温度）、`Pivt`、`Symm`、`Roe`、`RoeVinokur`
  - 两温度模型：`NavierStokesTCNEQVarSet`（plugins/NEQ 模板类，`nbVibEnergyEqs`、化学源项 + VT 弛豫源项 `getSourceTermVT`）
  - 电子能量非平衡：`includeElectronicEnergy`、`getSourceEE`
  - 化学反应动力学：Arrhenius 速率、`getMassProductionTerm`、解析 Jacobian（`flagJac`）
  - 物理化学库接口：`PhysicalChemicalLibrary` 抽象（src/Framework）与四个实现——`MutationLibrary`（MutationI/Mutation 1）、`MutationLibrary2`（Mutation2.0I，含 `data/` 六类子目录 chemistry/mixture/thermo/thermoCR/transfer/transport，共 191 个物性文件：138 数据表 + 26 种混合气 `.mix` + 27 种平衡组分 `.ceq`）、`MutationLibrary2OLD`（Mutation2.0.0I，数据文件在插件根目录）、`MutationLibrarypp`/`MutationLibraryppDebug`（MutationppI，需 `CF_ENABLE_MUTATIONPP`）
- 3.1.6 LTE 局部热力学平衡：`LTE` 插件（组分平衡、输运与热物性，`Euler2DPuvtLTE` 等），与 NEQ 的切换条件
- 3.1.7 等离子体模型：`ICP`（电感耦合等离子体、电磁场+流动，`ICPInductionConvVarSet` 等）、`ArcJet`（弧加热风洞，`ArcJetInductionConvVarSet` 等）、`ATDModel`（电弧热等离子体物性库）、`FiniteVolumeICP/FiniteVolumeArcJet` 求解器（`RMSJouleHeatSource`、`ICPInductionEquationSourceTerm` 等电磁源项）
- 3.1.8 辐射模型：`RadiativeTransfer` 插件（切平板/射线追踪、谱带模型：HSNB（`testcases/HuygensDLR/hsnb.con` 等）、PARADE、Grey、ArcJet 谱库），与 NEQ 流场耦合策略（`omegRad`/`omegaRad` 源项交换）
- 3.1.9 壁面现象：催化模型（`Catalycity` 插件、Framework 内 `CatalycityModel`/`NullCatalycityModel`）、等温/绝热/辐射壁边界
- 3.1.10 其他物理：传热 `Heat`（含 `StructMechHeat` 固体导热）、Poisson/超 Poisson（`Poisson`、`HyperPoisson`、`PoissonNEQ`）、线化 Euler（`LinEuler`，气动声学）、结构力学（`StructMech`）、拉格朗日粒子（`LagrangianSolver`）

### 3.2 数值离散方法总览（各方法章节索引）
- 3.2.1 有限体积法（FVM）：单元中心 `CellCenterFVM`（FVMCC）；注：代码库中不存在 `VertexCenterFVM`，节点中心离散由 RDS/FluctSplit 承担（见 3.2.2）
- 3.2.2 残差分布法（RDS/FluctSplit）：LDA（`LDASchemeSys`）、N（`NSchemeSys`）、LDA-PSI（`PSISchemeSys`）、FCT、B×（`BxSchemeSys`）等分布格式（`FluctSplit` 920 文件）
- 3.2.3 间断伽辽金（`DiscontGalerkin`：`DG_MeshDataBuilder`、`ContourDGGaussLegendre*Lagrange*` 等）
- 3.2.4 通量重构（FR/CPR）：`FluxReconstructionMethod`（P0–P10、修正函数为 VCJH 族——Vincent-Castonguay-Jameson-Huynh 能量稳定修正函数，参数选择可退化为 SD/CU/HU 特例；RANS/NS/Euler/湍流/NEQ/MHD 等扩展插件族）
- 3.2.5 谱差分 SD 与谱体积 SV：`SpectralFD`（基于 FR 框架的 `BasePointDistribution` 点分布）、`SpectralFV` 及其 NavierStokes/LES/LinEuler 扩展
- 3.2.6 有限元：`FiniteElement`（165 文件，含弹性与输运）
- 3.2.7 方法选择决策树：按问题类型/精度需求/计算成本给出推荐组合

### 3.3 边界条件类型全表（按方法分组）
- 3.3.1 FVMCC 边界条件命令：`MirrorVelocityFVMCC`（滑移壁）、`SuperInletFVMCC`、`SuperOutletFVMCC`、`NoSlipWallIsothermalNSPvt`/`NoSlipWallAdiabaticNSPvt`（FiniteVolumeNavierStokes，无 `FVMCC` 后缀）、`NoSlipWallIsothermalNSrvt`、`CoupledNoSlipWall*` 族（流固耦合 BC）、远场、对称面、周期、压远场、激波匹配、催化壁（NEQ）、传导壁（耦合）等——逐条列 CFcase 名 + 物理含义 + 参数
- 3.3.2 RDS / FR / SD / SV 各自的 BC 命令族（如 FR 的 `BCDirichlet`、`BCSuperOutlet`、`BCMirrorVelocity`、`BCPeriodic`；SpectralFD 的 `BCFarFieldCharEuler*`、`BCSubInletEuler*` 等）
- 3.3.3 TRS 定义与网格文件中边界标记的对应关系（`listTRS`、`.CFmesh` 的 TRS 段）
- 3.3.4 虚拟单元（ghost）机制与 BC 实现原理（`ComputeDummyStates`）

### 3.4 无量纲化与单位约定
- 3.4.1 有量纲/无量纲模式（`DIM`/`NDIM` 算例命名含义）
- 3.4.2 参考量定义（密度、速度、温度、长度）及与输出量的换算

---

## 第 4 章 核心算法详解

### 4.1 空间离散算法
- 4.1.1 `CellCenterFVM`：数据结构、面通量求和、`ComputeRHS` 策略（`NumJacob`/`AnalyticalJacob`）、`PseudoSteadyTimeRhs` 伪时间项、最小二乘模板（`LeastSquareP1Setup`，`stencil = FaceVertex | FaceVertexPlusGhost | AllVertices`，实测含 FaceVertexPlusGhost）
- 4.1.2 节点中心离散：由 RDS/FluctSplit 实现（见 4.1.3）；注：原大纲中的 `VertexCenterFVM` 在代码库中不存在，已删除
- 4.1.3 FluctSplit/RDS：亚通量（fluctuation）分解、分布矩阵、LDA-PSI 与 FCT 限制、`FluctSplitNEQ` 非平衡扩展
- 4.1.4 DiscontGalerkin：基函数、数值通量、跳项惩罚、局部投影限制器
- 4.1.5 FluxReconstruction：VCJH 修正函数族（能量稳定 FR，参数 `g1/g2` 可覆盖 SD/CU/HU）、FR↔DG 等价性、`FluxReconstructionNavierStokes/Turb/MHD/MultiFluidMHD/EntropyMHD/Poisson/HyperPoisson/NEQ/Petsc/CUDA` 子插件
- 4.1.6 SpectralFD：点分布（`BasePointDistribution` 框架）、`SpectralFDNavierStokes` 粘性处理（BR2——`BR2FaceTermComputer`、`NSFaceDiffusiveFluxLocalApproach` 等；注：FLIP 术语在代码中无对应类）
- 4.1.7 SpectralFV：谱体积重构、`SpectralFVNavierStokes`
- 4.1.8 FiniteElement：弱形式、单元矩阵装配

### 4.2 通量计算格式（FluxSplitter 全表）
- 4.2.1 FVM 对流通量（实测清单，`plugins/FiniteVolume` + `plugins/FiniteVolumeNavierStokes`）：
  - Roe 族：`Roe`、`RoeFast`、`RoeEntropyFix`（熵修正）、`RoeSA`（Sanders 熵修正/carbuncle fix）、`RoeVLPA`、`RoeTurb`、`RoeLin`、`Roe*ALE`（动网格）
  - AUSM 族：`AUSM`、`AUSMPlus`、`AUSMPlusUp`、`AUSMPlusUp_Mp`、`AUSMPlusUp_MpW`、`AUSMLiouSteffen`、`AUSMLowMlimit`、`AUSMFluxPrec`/`AUSMPlusFluxPrec`（低马赫预处理）
  - 其他：`HLL`、`HLLE`、`LaxFried`/`LaxFriedBCCorr`（Lax-Friedrichs）、`Centred`、`VanLeer1D/2D/3D`、`StegerWarming`、`GForce`
  - 注：代码中不存在 HLLC、Jameson、AUSMPlusUp2，原大纲列表已修正
  - 每条给出公式推导、CFcase 名、适用马赫数范围与耗散特性
- 4.2.2 粘性通量：`NavierStokes` 粘性项（轴对称开关 `isAxisymm`）、梯度重构与节点外推（`HolmesConnell`、`DistanceBasedExtrapolator`）
- 4.2.3 MHD 通量：Roe 型 MHD 通量、HLL 族、`EntropyMHD` 熵稳定格式、Powell/投影修正
- 4.2.4 NEQ 通量：`Rhoivt/RhoivtTv` 变量集下的 Roe 格式（含 `RoeVinokurTCNEQFlux`）与化学源项刚性处理
- 4.2.5 多流体 MHD 通量：`AUSMFluxMultiFluid`、`AUSMPlusUpFluxMultiFluid`、`LaxFriedFluxMultiFluid`（含 ALE 动网格变体）与双流体界面处理

### 4.3 重构与限制器
- 4.3.1 多项式重构：`ConstantPolyRec`、`LeastSquareP1PolyRec*`（LinearLS 族）、`FVMCC_PolyRec` 等（注：无 `LimiterVanAlbada`，已从原大纲删除）
- 4.3.2 限制器：`BarthJesp`、`Venktn2D/3D`（Venkatakrishnan）、`CustomLimiter*`、`MinMod*`（含时间限制器 `MinModTimeLimiter` 等）；参数 `limitRes`（残差阈值，实测 `LinearLS2D.limitRes = -4.0`）
- 4.3.3 高阶方法的限制与后处理（FR/DG/SD 的 troubled-cell 处理）

### 4.4 时间推进与收敛方法（ConvergenceMethod 全表）
- 4.4.1 显式：`ForwardEuler`、`RungeKutta`、`RungeKutta2`、`RungeKuttaLS`（低存储 RK）、`RKRD`（RDS 专用）
- 4.4.2 隐式：`BackwardEuler`、`NewtonMethod`（`NewtonIterator`：CFL 策略、`MaxSteps`、解析/数值 Jacobian、`freezejacob` 冻结策略）、`LUSGSMethod`（LU-SGS）；SpectralFD/FR 另有 `BDF2/BDF3TimeRHS*` 多步法
- 4.4.3 CFL/DT 控制：固定值、分段函数（`CFL.ComputeCFL = Function` + `CFL.Function.Def = if(i<300,1.,...)`，实测）、`ExprComputeCFL/ExprComputeDT`、局部时间步 `useGlobalDT`
- 4.4.4 低马赫/不可压：低马赫预处理通量（`AUSMFluxPrec`/`AUSMPlusFluxPrec`）、不可压算例（`NavierStokes/testcases/Incompressible/`）、`cyl_Pg_M15_FVM_1st2nd_MeFiAlgo.CFcase`（实测存在）；注：原大纲的 `Mechanical*` 类不存在，已删除

### 4.5 线性系统求解器（LSS）
- 4.5.1 `Petsc` 插件（库名 `PetscI`，`libPetscI.so`）：KSP/GMRES（`KSPType = KSPGMRES`）、预条件子（`PCType = PCASM` 及 ILU/BlockJacobi/LUSGS 等内置 PC）、矩阵排序（`MatOrderingType = MATORDERING_RCM`）、PETSc 选项透传（`NbKrylovSpaces`、`MaxIter`、`RelativeTolerance` 等，实测）
- 4.5.2 直接法与备选：`Pardiso`、`SAMGLSS`（SAMG 代数多重网格）、`Trilinos`、`Paralution`（GPU）
- 4.5.3 分块稀疏装配（`BlockAccumulator`）与稀疏模式选择（单元中心/节点/LocalApproach）
- 4.5.4 LSS 配置模式：`LinearSystemSolver = PETSC` + `LSSNames`（如 `NewtonIteratorLSS`）+ 命名配置节

### 4.6 多重网格与加速收敛
- 4.6.1 SAMG 代数多重网格（`SAMGLSS`）配置
- 4.6.2 其他加速：局部时间步、网格序列（粗网格起步）、LUSGS 隐式迭代；注：无独立"隐式残差光顺"模块，原大纲表述已修正

### 4.7 自适应网格加密（AMR）与网格操作
- 4.7.1 `SimpleGlobalMeshAdapter`：误差估计器（`HessianEE`、`AnalyticalEE`）驱动、全局重构策略
- 4.7.2 `CFmeshCellSplitter`：单元细化（P1→P2、悬挂节点处理）
- 4.7.3 `CFmeshExtruder`：2D→3D 拉伸、边界层网格生成
- 4.7.4 误差估计框架：`ErrorEstimatorMethod/Data` 接口

### 4.8 动网格技术
- 4.8.1 `MeshRigidMove`（刚体运动）、`MeshLaplacianSmoothing`（Laplacian 光顺）、`MeshAdapterSpringAnalogy`（弹簧类比）、`MeshFEMMove`（FEM 变形）
- 4.8.2 GCL（几何守恒律）与动网格下的通量修正（ALE 通量族 `RoeFluxALE`、`AUSMFluxALE`）、`CoeffMove` 参数（实测存在于 `doubleEllipseNS_PG.CFcase`）
- 4.8.3 动网格与边界条件联动（运动壁 BC）

### 4.9 耦合求解策略
- 4.9.1 子系统耦合：`SubSystemCoupler`（界面数据交换、守恒插值、35 个耦合算例，含流固共轭传热）
- 4.9.2 并发耦合：`ConcurrentCoupler`（流-固/流-辐射同步推进）
- 4.9.3 流场-辐射耦合：NEQ 源项中 `omegRad` 的交换流程（`FiniteVolumeNEQ` ↔ `RadiativeTransfer`）
- 4.9.4 流-固-热三场耦合工作流（Heat + StructMech + NavierStokes + SubSystemCoupler）

### 4.10 GPU 加速实现细节
- 4.10.1 `FiniteVolumeCUDA`：核函数清单（`.cu` 文件）、内存布局（`GrowArray` on device）、`CF_HAVE_CUDA_MALLOC`
- 4.10.2 `FluxReconstructionCUDA`：FR 算子的 GPU 化
- 4.10.3 性能调优：`CudaTimer`、设备选择、数据传输最小化

---

## 第 5 章 源代码文件逐文件说明

**写作规则**：按目录逐层展开；每个源文件条目包含【文件名】【一句话功能】【关键类/函数】【被谁调用/调用谁】【典型使用场景】；对纯模板/`.ci` 文件合并说明；每节末尾给出该目录的类图与调用关系图（Mermaid）。

### 5.1 `src/Common/` 逐文件说明（188 项）
- 基础对象与指针：`OwnedObject.hh/cxx`、`SetupObject.hh`、`NamedObject.hh`、`TaggedObject.hh`、`SharedPtr.hh`、`SafePtr.hh`、`SelfRegistPtr.hh`（注：无 `CFObject.hh`、`AutoPtr.hh`）
- 工厂：`FactoryRegistry.hh`、`FactoryBase.hh`（完整 `Factory.hh` 在 `src/Environment/`）、`WorkerStatus.hh`
- 异常体系：`Exception.hh`、`BadValueException.hh`、`ShouldNotBeHereException.hh`、`NoSuchValueException` 等（注：无 `NotFound`）
- 字符串与数学：`StringOps`、`Stopwatch`、`TimePolicies`
- 并行：`PE.hh/cxx`（MPI 初始化、rank、barrier、reduce）、`PEInterface.hh/cxx`、`PEFunctions.hh`（注：无 `PEOperations.hh`、`PEAPI`）
- 日志：`CFLog.hh/cxx`（`Logger`/`LogLevel` 概念由 `src/logcpp/` 的 `Category`/`Priority` 实现）
- 系统：`OSystem`、`ProcessInfo`（Linux/MacOSX/Win32）、`FilesystemException`、`FileDownloader`（注：无 `FilesystemUtils`、`BasicFunctions`）
- 配套 `.ci` 显式模板实例化文件说明

### 5.2 `src/Config/` 逐文件说明（46 项）
- `ConfigObject.hh/cxx`（配置基类、`configure()`、`getConfigOptions`）
- `Option.hh`、`OptionList.hh`、`OptionT.hh`（类型化选项，含数组；注：无独立 `OptionArray` 类）；另有 `OptionMarkers.hh`、`OptionValidation.hh`
- `ConfigFileReader.hh/cxx`（`.CFcase` 解析）、`NestedConfigFileReader`、`XMLConfigFileReader`、`ConfigArgs.hh`、`ConfigFacility.hh`（注：**`ConfigRegistry` 属 `src/Environment/`，不在此目录**）
- 异常：`BadMatchException` 等（注：`ShouldNotBeHere`→`Common/ShouldNotBeHereException.hh`，`BadFormatException` 在 `src/Framework/`）

### 5.3 `src/Environment/` 逐文件说明（45 项）
- `CFEnv.hh/cxx`（运行环境生命周期）、`CFEnvVars`（环境变量表）
- `DirPaths.hh/cxx`（库搜索路径 `--ldir`、`--bdir`）
- `Factory.hh`、`FactoryRegistry.hh`（环境级注册）、`ModuleRegister.hh`、`ConfigRegistry.hh/cxx`
- 日志文件与输出重定向（注：**无 `TimeTable` 文件**）

### 5.4 `src/Framework/` 逐文件说明（567 项，按功能域分组）
- 5.4.1 仿真管理层：`Simulator`、`Maestro`（接口）、`SMaestro`/`LMaestro`（实现，**注册名分别为 `SimpleMaestro`/`LoopMaestro`，注意文件名与注册名不同名**）、`SubSystem`、`SubSystemStatus`、`SimulationStatus`、`StopCondition` 族、`CommandGroup`
- 5.4.2 网格与几何：`MeshBuilder`、`MeshFormatChecker`、`Cell/Face/Edge/State/Node`、`GeometricEntity`、`CFGeoEnt/CFGeoShape`、TRS 相关、GeoBuilder 族、`FaceJacobiansDeterminant`、`ContourIntegrator`（含 `GaussLegendreContourIntegratorImpl`、`NullContourIntegratorImpl`）
- 5.4.3 形状/多项式/积分枚举：`CFPolyForm`（P0–P10）、`CFPolyOrder`、`CFQuadrature`、`CFIntegration`、`CFSide`
- 5.4.4 数据管理：`DataStorage`、`DataSocket`、`DataHandle`（+`DataHandleMPI`）、`DataBroker`、`ElementDataArray`、`DynamicDataSocketSet`
- 5.4.5 物理模型层：`PhysicalModel`、`PhysicalProperty`、`VarSet` 基类、`ConvectiveVarSet/DiffusiveVarSet`、`ConvectionPM` 等 PM 族、`CatalycityModel`/`NullCatalycityModel`、`EquationSetData`
- 5.4.6 数值方法层：`SpaceMethod`、`ConvergenceMethod`、`LinearSystemSolver`、`EigenSolver`、`BlockAccumulator`、稀疏模式族（`CellCenteredSparsity`、`CellVertexSparsity`、`CellVertexSparsityNoBlock`）、`ComputeFlux/ComputeTerm/ComputeSourceTerm` 接口
- 5.4.7 FVM 通用组件：`BaseSetupFVMCC`、`ComputeFaceNormals*`、`BaseDataSocketSource/Sink`、`ConvectiveVarSetFVMCC` 等
- 5.4.8 命令组件：初始化命令、BC 基类、`ComputeDummyStates`、`DetermineCFL/ComputeCFL/ComputeDT`、范数命令族（`ComputeNorm`、`ComputeL2Norm`、`AbsoluteNormAndMaxIter`、`ComputeAllNorms`）
- 5.4.9 IO：`FileReader/FileWriter`、`CFmeshFileReader/Writer`（含 `.ci` 与二进制）、`BaseCFMeshFileSource` 族
- 5.4.10 数据处理与耦合：`DataProcessing(Method/Data)`、`CouplerData/CouplerMethod`、`CollaboratorAccess`、`EquationSubSysDescriptor`、`FilterRHS`/`EquationFilter` 族、`DistanceBasedExtrapolator`、`InteractiveParamReader`
- 5.4.11 负载平衡：`DynamicBalancerMethod(Data)`
- 5.4.12 CUDA：`CudaDeviceManager.cu`、`CudaTimer`、`BlockAccumulatorBaseCUDA`

### 5.5 `src/MathTools/` 逐文件说明（66 项）
- `RealMatrix/RealVector`、`Matrix`（定尺寸小矩阵）、`MathFunctions`、`MathConsts`、`MathChecks`、`LeastSquaresSolver`、插值工具、`.inc` 表文件

### 5.6 `src/ShapeFunctions/` 逐文件说明（202 项）
- 每类单元（Line/Triag/Quad/Tetra/Hexa/Prism/Pyram × P1/P2 …）的 Lagrange 形函数与导数（`Lagrange*`、`ContourGaussLegendre*Lagrange*` 族）
- 积分点：`GaussOrder*`、`GaussQuadratureInfo`、分面积/分体积公式

### 5.7 `apps/Solver/` 逐文件说明
- `coolfluid-solver.cxx`（主程序流程逐段讲解，实测确认）、`coolfluid-solver.xml`（默认配置）、`PluginsRegister.hh`（静态编译插件注册，`CF_ENABLE_SINGLEEXEC` 模式）、`coolfluid-solver-wrapper`（wrapper 脚本）

### 5.8 插件源码分主题逐文件说明（选讲 + 全索引）
- 5.8.1 `FiniteVolume/`（381 文件，FVM 核心库）：SpaceMethod（`CellCenterFVM`）、FluxSplitter 族、PolyRec 族、Limiter 族、BC 命令族、Setup 族——给出类的继承图
- 5.8.2 `NavierStokes/`：物理模型与变量集（`NavierStokes2D Puvt` 等）、源项、扩散项
- 5.8.3 `NEQ/`：非平衡变量集全族（`Euler*NEQRhoivt(Tv)`、`NavierStokesTCNEQVarSet`）、热化学接口封装（`PhysicalChemicalLibrary` 各实现）
- 5.8.4 `FiniteVolumeNEQ/`：化学/振动源项（`ChemNEQST` 等）、辐射耦合项、NEQ 专用 BC
- 5.8.5 `MHD/` + `FiniteVolumeMHD/`：2D/3D、守恒/投影变量集（`MHD2DProjectionCons` 族）、通量、$\nabla\!\cdot\!B$ 处理（Powell/投影）
- 5.8.6 `MultiFluidMHD/` + `FiniteVolumeMultiFluidMHD/`：多流体模型、界面条件、源项
- 5.8.7 `FluctSplit/`（920 文件）：分布矩阵族（LDA/N/PSI/B×）、BC 族、`FluctSplitNEQ`
- 5.8.8 `FluxReconstructionMethod/`（488 文件）：FR 内核（单元/面/补丁、`BaseCorrectionFunction`/`VCJH`/`NullCorrectionFunction`、`BasePointDistribution`、重构、求解器接口）
- 5.8.9 `SpectralFD/`、`SpectralFV/`：点分布布局、通量点重构、粘性处理（BR2/LocalApproach）
- 5.8.10 `RadiativeTransfer/`：谱带模型（HSNB/PARADE/Grey）、射线求交、与流场耦合命令
- 5.8.11 `ICP/`、`ArcJet/`：电磁源项（`ICPInductionEquationSourceTerm`、`RMSJouleHeatSource` 等）、感应加热、LTE 等离子体物性
- 5.8.12 `MutationI/2.0I/2.0.0I/MutationppI/MutationUsage/`：库封装模式（`MutationLibrary` 族）与数据文件组织（`data/` 六类子目录）
- 5.8.13 `Petsc/`、`Pardiso/`、`SAMGLSS/`、`Trilinos/`、`Paralution/`：LSS 封装模式（含各 `Find*.cmake` 依赖查找）
- 5.8.14 IO 插件：`CFmeshFileReader/Writer`、`CGNS2CFmesh/CGNSWriter`、`TecplotWriter`、`TecplotWriterNavierStokes`、`ParaViewWriter`、`ConvertStructMesh`、`Gmsh2CFmesh`、`Gambit2CFmesh`、`FAST2CFmesh`、`Dpl2CFmesh`、`Tecplot2CFmesh`、`XCFcaseConverter`（命令行工具，`main.cxx`）、`TecplotMerge`（含 `CoefMerge.cxx` 气动力系数合并）；注：`CFmesh2THOR` 与 `THOR2CFmesh` 为旧式/独立工具——`CFmesh2THOR` 无 `CMakeLists.txt`（未纳入构建系统），`THOR2CFmesh` 正常构建
- 5.8.15 其余插件全索引表（每个插件一行：名称/类别/一句话功能/关键文件数）
- 5.8.16 空壳与示例插件：`EmptySpaceMethod`、`EmptyConvergenceMethod`、`PhysicalModelDummy`、`MarcoTest`、`AutoTemplateLoader`（二次开发模板）

### 5.9 调用关系图汇总
- 5.9.1 `coolfluid-solver` 启动调用链（Mermaid 序列图）
- 5.9.2 一次 FVM 迭代的调用链
- 5.9.3 一次 FR 迭代的调用链
- 5.9.4 边界条件命令的调用链
- 5.9.5 网格读取到 TRS 建立的调用链

---

## 第 6 章 插件系统详解

**写作规则**：每个插件一节，统一模板——【功能描述】【所属类别】【启用方式（`Simulator.Modules.Libs` 条目 + 必需的 CFcase 配置键）】【输入参数表（选项名/类型/默认值/含义）】【输出结果】【源代码文件清单】【依赖插件/外部库】【验证算例】【已知限制】。

### 6.1 插件分类总表（全部经目录实测核对）
| 类别 | 插件 |
|------|------|
| 物理模型 | NavierStokes, NEQ, LTE, MHD, MultiFluidMHD, Maxwell, EntropyMHD, ATDModel, ArcJet, ICP, Heat, Poisson, PoissonNEQ, HyperPoisson, LinEuler, LinearAdv, LinearAdvSys, NonLinearAdv, RotationAdv, RotationAdvSys, Burgers, StructMech, StructMechHeat, GReKO, GammaAlpha, KOmega, SA, NEQKOmega, LES, LESvki, Chemistry, Catalycity, AnalyticalEE, HessianEE, AnalyticalModel, GETModel, PARADE, NitrogenNASA, NitrogenNASAI, PlatoI, MutationUsage, LagrangianSolver |
| 空间离散方法 | FiniteVolume, FiniteVolumeNavierStokes, FiniteVolumeNEQ, FiniteVolumeMHD, FiniteVolumeMultiFluidMHD, FiniteVolumeMaxwell, FiniteVolumeICP, FiniteVolumeArcJet, FiniteVolumeTurb, FiniteVolumeGReKO, FiniteVolumeLES, FiniteVolumeCombustion, FiniteVolumePoisson, FiniteVolumePoissonNEQ, FiniteVolumeAdvectionDiffusion, FiniteVolumeTU, FiniteVolumeCUDA, FluctSplit, FluctSplitNEQ, DiscontGalerkin, FluxReconstructionMethod, FluxReconstructionNavierStokes, FluxReconstructionTurb, FluxReconstructionMHD, FluxReconstructionMultiFluidMHD, FluxReconstructionEntropyMHD, FluxReconstructionPoisson, FluxReconstructionHyperPoisson, FluxReconstructionNEQ, FluxReconstructionCUDA, FluxReconstructionPetsc, SpectralFD, SpectralFDNavierStokes, SpectralFDLES, SpectralFDLinEuler, SpectralFV, SpectralFVNavierStokes, FiniteElement |
| 时间推进 | ForwardEuler, RungeKutta, RungeKutta2, RungeKuttaLS, BackwardEuler, NewtonMethod, LUSGSMethod, RKRD, EmptyConvergenceMethod |
| 线性求解器 | Petsc（库名 PetscI）, Pardiso, SAMGLSS, Trilinos, Paralution |
| 网格 IO 与转换 | CFmeshFileReader, CFmeshFileWriter, CGNS2CFmesh, CGNSWriter, TecplotWriter, TecplotWriterNavierStokes, ParaViewWriter, THOR2CFmesh, ConvertStructMesh, Gmsh2CFmesh, Gambit2CFmesh, FAST2CFmesh, Dpl2CFmesh, Tecplot2CFmesh, XCFcaseConverter, CFmeshExtruder, CFmeshCellSplitter, MeshTools, MeshGenerator1D, ParMetisBalancer |
| 动网格与自适应 | MeshRigidMove, MeshLaplacianSmoothing, MeshAdapterSpringAnalogy, MeshFEMMove, SimpleGlobalMeshAdapter |
| 耦合 | SubSystemCoupler, ConcurrentCoupler |
| 后处理 | AeroCoef, LESDataProcessing, ExplicitFilters, TecplotMerge |
| 模板/示例 | EmptySpaceMethod, PhysicalModelDummy, MarcoTest, AutoTemplateLoader |

注：`CFmesh2THOR` 为旧式源码（无 `CMakeLists.txt`，未纳入构建系统），表格中不再列入。

### 6.2 重点插件详解（完整模板展开）
- 6.2.1 `NavierStokes` + `FiniteVolumeNavierStokes`：可压 NS/RANS 主力组合（835/268 文件，实测）
- 6.2.2 `NEQ` + `FiniteVolumeNEQ`：热化学非平衡主力组合（208/103 文件，实测）
- 6.2.3 `MHD` + `FiniteVolumeMHD`（1093/130 文件，实测）
- 6.2.4 `MultiFluidMHD` + `FiniteVolumeMultiFluidMHD`（257/166 文件，实测）
- 6.2.5 `RadiativeTransfer`（232 文件，实测）
- 6.2.6 `ICP` + `FiniteVolumeICP`、`ArcJet` + `FiniteVolumeArcJet`
- 6.2.7 `FluctSplit`（920 文件，实测）
- 6.2.8 `FluxReconstructionMethod`（488 文件，实测）及其物理扩展
- 6.2.9 `SpectralFD` 族、`SpectralFV` 族
- 6.2.10 `Petsc`、`NewtonMethod`、`LUSGSMethod`
- 6.2.11 `SubSystemCoupler`（206 文件，实测）
- 6.2.12 `AeroCoef`（气动力系数提取）
- 6.2.13 `FiniteVolumeCUDA`、`FluxReconstructionCUDA`、`Paralution`

### 6.3 插件启用方式详解
- 6.3.1 动态库模式：`Simulator.Modules.Libs` 列表 + `--ldir` 搜索路径；库命名为 **`lib<插件名>.so`**（如 `libNavierStokes.so`、`libFiniteVolume.so`、`libPetscI.so`、`libFiniteVolumeNavierStokes.so`），构建后位于 `build/dso/`（注：无 `libCF_` 前缀，原大纲表述已修正）
- 6.3.2 静态模式：`CF_ENABLE_SINGLEEXEC`（编译宏 `CF_HAVE_SINGLE_EXEC`）、`PluginsRegister.hh`
- 6.3.3 插件间依赖与加载顺序（`_requires_mods` 依赖列表机制，如 `Mutation2I_requires_mods = Mutation2.0`）
- 6.3.4 编译期启用：**逐插件开关为 `CF_BUILD_<LIBNAME>`**（由 `prepare.pl` 解析根目录 `coolfluid.conf` 的 `lib_<Plugin>=on/off` 生成 `-DCF_BUILD_<Plugin>=OFF/ON`，实测）；全局功能开关为 `CF_ENABLE_*`；缺依赖自动禁用：条件 `IF(CF_HAVE_PETSC)`（Petsc）、`IF(NOT CF_SKIP_FORTRAN AND CF_HAVE_MUTATION2)`（Mutation2.0I）、`IF(CF_ENABLE_MUTATIONPP)`（MutationppI）等；注：不存在 `coolfluid-<Name>.cmake` 配置文件，原大纲表述已修正

### 6.4 每个插件的验证算例索引
- 指向第 7 章对应小节与 `plugins/<Name>/testcases/` 路径

---

## 第 7 章 算例库完整说明

**写作规则**：每个算例条目统一模板——【物理背景与文献】【几何与网格（单元数、CFmesh 来源）】【边界条件】【求解器配置要点（SpaceMethod/ConvergenceMethod/LSS/CFL 策略）】【运行命令（串行/并行）】【后处理建议】【预期结果与参考数据（残差收敛图、目标量数值）】【参考图片/文献】。

### 7.1 算例库组织与运行方式
- 7.1.1 布局：`plugins/<Plugin>/testcases/<CaseName>/`（CFcase + CFmesh + `.inter` + 参考输出）
- 7.1.2 数据包解压机制：`tools/scripts/init_testcases.sh` 在 CMake 配置阶段**按需解压** `MHD/testcases/COCONUT/`（Dipole/Dipole_Shifted/Dipole_WTD/Eclipse/Eclipse600 大型网格）与 `RadiativeTransfer/testcases/SolarCorona/` 的 `.xz` 压缩文件；仓库中共 751 个 `.xz` 压缩网格（绝大多数为 MHD 数据，保持压缩存储，运行时按需解压；注：并非"自动解压全部 751 个"，原大纲表述已修正）
- 7.1.3 CTest 集成：`CTestConfig.cmake`（dashboard 站点 coolfluidsrv.vki.ac.be）、`CF_ENABLE_TESTCASES`、`CF_TESTCASES_NCPUS`、`cf_add_case` 宏（`cmake/macros/CFAddTestCase.cmake`）、`--residual`/`--tolerance` 残差验收机制（实测：`--residual r --tolerance t`，tolerance 为允许的百分比偏差，默认 3.0%）
- 7.1.4 并行运行算例：并行版 CFcase 差异要点（`MPI N` 测试声明、ParMetis 剖分）

### 7.2 高焓高超声速算例群（重点章，与已有评估报告衔接）
- 7.2.1 `DoubleEllipse` 双椭球（`plugins/NavierStokes/testcases/DoubleEllipse/`，实测）：FVM/RDS、LTE、CNEQ、TCNEQ（air5/air11、park 反应集、demix、催化、辐射耦合 `deNEQ_CRD.CFcase`、`doubleEllipseNS_PG.CFcase`、`doubleEllipseNS_air5_demix_DIM_coupling.CFcase` 等）——Fire II 再入基准
- 7.2.2 `BluntBody2D` 钝体：CTNEQ 2T/2TV、MII（Mutation2 接口）、Kheops 三维算例
- 7.2.3 `DoubleEllipsoid` 三维双椭球
- 7.2.4 `F15` 外形：Euler/NS、FVM 与 FluctSplit 对照
- 7.2.5 `NEQ` 插件自带算例（27 个 CFcase，实测；testcases 分 `CNEQ`/`PrabhuCylinder`/`TCNEQ` 三大组，`TCNEQ` 下含 `Nozzle1DNEQ` 多温度喷管、`FireII`、`FireII_air11`、`Hornung`、`DoubleCone`、`EXPERT3D`、`ShockTube`、`CateIXV`、`ICP2Cat` 等）
- 7.2.6 `RadiativeTransfer` 算例（50 个 CFcase，实测：谱带辐射 HSNB/MC、耦合辐射、SolarCorona）

### 7.3 经典空气动力学算例群（`NavierStokes` 插件 420 个 CFcase 选讲）
- 7.3.1 翼型：`Airfoils/`（NACA、多段翼 `3elemFVMImpl_viscous.CFcase`（实测）、`gridTrefftz/` 后缘型线网格）
- 7.3.2 `BTC`、`BlastWaves`、`DoubleMachReflection`（双马赫反射）、`BLAST/`（注意目录名为大写 `BLAST`，`blastM6_aoa20_postprocessing.CFcase` 实测存在）
- 7.3.3 圆柱/圆球：`Cylinder/`（Re=40 定常、LES Re=3900、轴对称、`cyl_Pg_M15_FVM_1st2nd*` 系列）、`AccPulse/`（加速脉冲，FR/SD/SV 对照族 `accpulse2d-sfdmP1..P4` 等）
- 7.3.4 激波管与爆轰（`LaxShockTube`、`SodRiemann`、`OsherShu`、`SlowShockHittingWedge` 等）

### 7.4 MHD 与等离子体算例群
- 7.4.1 `MHD/`（112 CFcase + 746 xz 网格包，实测）：`COCONUT/` 系列（`Dipole`、`Dipole_Shifted`、`Dipole_WTD`、`Eclipse`、`Eclipse600`、`Map`、`MapCR2296`、`MHDRotor`、`OrszagTang`、`Quadrupole`，日冕/太阳风模拟）、`ShockTube/`（`shocktube-fvm-powell`/`shocktube-fvm-proj` 激波管）、`CoronalExpansion`、`SolarWind`、`Sphere`、`Wedge`、`Nozzle3D`、`Cylinder`、`Dipole3D`、`Jets2D`、`Quasi-steady-SW` 等；注：原大纲的 "Brio-Wu" 算例不存在，已修正为实际算例
- 7.4.2 `MultiFluidMHD/`（81 CFcase + 41 `.inter`，实测）
- 7.4.3 `Maxwell/`（9 CFcase，实测）、`EntropyMHD`
- 7.4.4 `ICP/`（45 CFcase，实测：纯 ICP、带磁场、与流动耦合）、`ArcJet/`（15 CFcase，实测）

### 7.5 方法验证算例群
- 7.5.1 线性对流/系统：`LinearAdv`（53 个，实测：LDA/N 验证、周期域、`*.SP` 谱文件）、`LinearAdvSys`、`LinEuler`（18 个，实测：`AeroAcoustic/` 下声脉冲/涡 `accpulse2dLEE-sfdmP1`、`dipole2dLEE-sfdmP1` 等）
- 7.5.2 标量非线性：`Burgers`、`NonLinearAdv`、`RotationAdv`
- 7.5.3 Poisson/超 Poisson：`Poisson`（12 个，实测）、`HyperPoisson`
- 7.5.4 高阶方法收敛族：`cylinderEuler2DFR-impl_P4..P8.CFcase`（`Cylinder/` 目录，实测 P4/P5/P6/P8）、`accpulse2d-sfdmP1..P4`（SpectralFD）

### 7.6 湍流与 LES 算例群
- 7.6.1 `SA/`（26 个 CFcase，实测：平板、翼型）、`KOmega/`（5 个，实测）、`GReKO/`（19 个 + 20 CFmesh，实测）
- 7.6.2 `LES/LESvki`：T3A/T3B 平板、圆柱 LES、`LESDataProcessing` 统计后处理流程

### 7.7 传热、结构与耦合算例群
- 7.7.1 `Heat/`（28 个 CFcase，实测：含 2D/3D 导热、辐射壁、`.hdf5` 数据）
- 7.7.2 `StructMech/`（27 个 CFcase，实测：悬臂梁、薄板）、`StructMechHeat`
- 7.7.3 `SubSystemCoupler/`（35 个 CFcase，实测：流固共轭传热、迭代耦合策略）

### 7.8 工具类与转换算例
- 7.8.1 `MeshTools`、`CFmeshExtruder`、`CFmeshCellSplitter`、`SimpleGlobalMeshAdapter`（off 网格，实测 2 个 `.off`）
- 7.8.2 `GReKO`（转换模型验证）、`KOmega`、`Maxwell`、`FiniteVolumeMaxwell` 其余算例
- 7.8.3 附录：全部 1019 个 CFcase 的完整索引表（插件/算例名/物理/方法/并行标记）

---

## 第 8 章 安装与编译指南

### 8.1 系统要求与依赖库
- 8.1.1 编译工具链：CMake ≥ 2.8.3（实测 `CMAKE_MINIMUM_REQUIRED`）、C/C++（必选）、Fortran（可选，`CF_SKIP_FORTRAN`）
- 8.1.2 必需库：Boost ≥ 1.42（thread/filesystem/system/regex/unit_test_framework；新版 1.79/1.85/1.88 需附加 atomic 组件，`CMakeLists.txt` 实测含版本分支逻辑；另有 1_42~1_88 各版本的 `CF_HAVE_BOOST_*` 编译宏）
- 8.1.3 可选库：MPI（OpenMPI/MPICH，`packages/` 内附 mpich-3.1.3 源码包）、Metis/ParMetis（剖分，附 parmetis-4.0.3 源码包）、ZLIB、BZip2、Curl、GSL、Valgrind、GooglePerftools、log4cpp、CUDA、ViennaCL、Mutation++、PLATO、Paralution、Pardiso/Trilinos/SAMG（商业/受限许可，各配 `Find*.cmake`）
- 8.1.4 依赖库获取与推荐版本表

### 8.2 Linux 平台安装（主推）
- 8.2.1 Ubuntu/Debian：apt 依赖清单 + 源码编译 PETSc/ParMetis 可选（`tools/scripts/install-coolfluid-deps.pl`、`install.sh` 辅助脚本）
- 8.2.2 CentOS/RHEL/Rocky、集群环境（module 系统、Intel 编译器/MKL 注意项；`tools/conf/` 提供 `coolfluid.conf.MF.static.CRAY`、`coolfluid.conf.MF.static.JUQUEEN`、`coolfluid_OPENMPI_VSC.conf`、`coolfluid.conf.vki.example` 等示例）
- 8.2.3 标准构建流程：
  - 方式一（prepare.pl）：根目录 `prepare.pl --build=optim`，读取个人配置文件 `coolfluid.conf`（`lib_<插件>=on/off`、编译器、`withcuda`、`with_testcases`、`allactive` 等键，实测），生成 CMake 参数后进入 `build/<mode>/` 构建
  - 方式二（直接 cmake，out-of-source）：
    ```bash
    mkdir build && cd build
    cmake <srcdir> -DCMAKE_BUILD_TYPE=RelWithDebInfo ...
    make -j
    ```
  - `build.sh`（本地一键构建脚本：prepare.pl → cmake 更新 CUDA 标志 → make -jN → make install → 清理中间产物，实测）
  - 注：`coolfluid.cmake` 是 CMakeLists.txt 在**构建目录**中可选 `INCLUDE` 的文件（`INCLUDE(${COOLFluiD_BINARY_DIR}/coolfluid.cmake OPTIONAL)`），与个人配置文件 `coolfluid.conf` 不同，原大纲混用已修正
- 8.2.4 PETSc 集成（`Petsc` 插件、`FindPetsc.cmake` 路径指定、`CF_HAVE_PETSC` 检测）

### 8.3 macOS 平台安装
- 8.3.1 Homebrew 依赖、clang 注意事项、Darwin 静态链接特殊处理（`DefineGlobalOptions.cmake` 实测含 `-all_load`；`coolfluid.conf.MF.static.clang`、`coolfluid.conf.MF.static.mpich.clang` 示例）

### 8.4 Windows 平台安装
- 8.4.1 Visual Studio 生成（`-G"Visual Studio 9 2008"` 注释实测，实际建议新版 VS + 适配）、`tools/win32/` 辅助工具
- 8.4.2 WSL/MSYS2 替代方案（推荐）

### 8.5 CMake 配置选项完整参考
- 8.5.1 通用开关（`DefineGlobalOptions.cmake` + 顶层 `CMakeLists.txt` 实测全表）：
  - 构建模式：`CF_ENABLE_STATIC`、`CF_ENABLE_SINGLEEXEC`（注意拼写）、`CF_ENABLE_IBMSTATIC`、`CF_ENABLE_CRAYSTATIC`、`CF_SKIP_FORTRAN`
  - 并行/加速：`CF_ENABLE_MPI`、`CF_ENABLE_CUDA`、`CF_ENABLE_OMP`、`CF_CUDA_MALLOC`（→`CF_HAVE_CUDA_MALLOC`）、`CF_ENABLE_VIENNACL`、`CF_ENABLE_PARALLEL_VERBOSE`、`CF_ENABLE_PARALLEL_DEBUG`、`CF_TESTCASES_NCPUS`
  - 第三方库：`CF_ENABLE_CURL`、`CF_ENABLE_GSL`、`CF_ENABLE_LOG4CPP`、`CF_ENABLE_MUTATIONPP`、`CF_ENABLE_MUTATIONPP_DEBUG`、`CF_ENABLE_PLATO`
  - 测试/文档：`CF_ENABLE_TESTCASES`（连带开启单元/性能测试）、`CF_ENABLE_UNITTESTS`、`CF_ENABLE_DOCS`、`CF_ENABLE_PERFORMANCE_TESTS/CASES`
  - 调试/日志：`CF_ENABLE_LOGALL`、`CF_ENABLE_LOGDEBUG`、`CF_ENABLE_TRACE`、`CF_ENABLE_ASSERTIONS`、`CF_ENABLE_DEBUG_MACROS`、`CF_ENABLE_WARNINGS`、`CF_ENABLE_STDASSERT`、`CF_ENABLE_PROFILING`（gprof/google-perftools）、`CF_CMAKE_LIST_PLUGINS`
  - 精度/索引：`CF_PRECISION_DOUBLE/SINGLE/LONG_DOUBLE`、`CF_ENABLE_LONG`、`CF_ENABLE_LLONG`
  - 内部机制：`CF_ENABLE_EXPLICIT_TEMPLATES`、`CF_ENABLE_GROWARRAY`、`CF_ENABLE_INTERNAL_DEPS`、`CF_ENABLE_AUTOMATIC_UPDATE_MODULES`（SVN 自动更新）、`CF_NO_LIBRARY_VERSION`、`CF_EXTRA_SEARCH_DIRS`（源码树外插件，实测 `CMakeLists.txt` 的 `FOREACH(EXDIR ...)` 机制）
- 8.5.2 构建类型：Debug/Release/RelWithDebInfo（默认）/MinSizeRel
- 8.5.3 精度与索引宽度（`IDXTYPEWIDTH/REALTYPEWIDTH` 注释项，实测）
- 8.5.4 配置结果检查：CMake summary 输出逐行解读（版本、编译器、MPI、插件列表）

### 8.6 安装、测试与部署
- 8.6.1 `make install` 与安装目录布局（`bin/lib/include/coolfluid/data`、RPATH 设置，实测 `CMAKE_INSTALL_RPATH = ${CMAKE_INSTALL_PREFIX}/lib`）
- 8.6.2 运行回归测试：`ctest`、`CF_ENABLE_TESTCASES`、单元测试（`CF_ENABLE_UNITTESTS`）
- 8.6.3 性能测试：`CF_ENABLE_PERFORMANCE_TESTS/CASES`、profiler 使用
- 8.6.4 打包：CPack（`INCLUDE(PrepareCPack)` 实测）

### 8.7 常见编译/配置错误与解决方案（FAQ 形式，≥20 条）
- Boost 版本不识别（老 CMake + 新 Boost 的 `Boost_ADDITIONAL_VERSIONS` 补丁，实测）
- MPI 找不到 / MPI 编译器包装、CUDA 与 CMake 版本兼容、Mutation 库路径环境变量、`init_testcases.sh` 失败、孤文件警告 `OrphanFiles.txt`（实测机制）、RPATH 问题、`CF_SKIP_FORTRAN`、显式模板 `.ci` 相关链接错误、CUDA 下 `.cxx`→`.cu` 复制编译的中间产物（`LaxFriedFlux.cu` 等）等

---

## 第 9 章 使用流程与输入文件格式

### 9.1 总体使用流程
- 9.1.1 五步法：准备网格（CFmesh）→ 编写 CFcase → 运行 `coolfluid-solver` → 监控收敛 → 后处理
- 9.1.2 最小可用 CFcase 模板（带逐行注释，基于 `cyl_Pg_M15_FVM_1st2nd.CFcase` 精简，实测）

### 9.2 CFcase 语法规范（`ConfigFileReader` 解析规则）
- 9.2.1 键值对格式 `Key = Value`、`#` 注释（`###` 为元注释）、续行符 `\`、字符串与数字解析规则（实测 `CFL.Function.Def = \` 多行续行）
- 9.2.2 命名空间层级：`Simulator.*`（顶层）、`Simulator.SubSystem.*`、`Simulator.SubSystem.<Name>.*`（命名实例，如 `NewtonIteratorLSS`）、`CFEnv.*`（环境配置，如 `CFEnv.ExceptionLogLevel`、`CFEnv.ErrorOnUnusedConfig`）
- 9.2.3 选项名与 C++ `addConfigOption` 的映射关系、严格模式（`OptionList::setStrictArgs(true)` 未识别键报错）
- 9.2.4 列表语法（空格分隔多值，如 `Modules.Libs`、`listTRS`）

### 9.3 CFcase 字段完整参考（按前缀分组）
- 9.3.1 顶层与路径：`Simulator.Paths.WorkingDir/ResultsDir`、`Simulator.Modules.Libs`
- 9.3.2 子系统级：`PhysicalModelType`、`SubSystem.InteractiveParamReader.FileName`（`.inter` 交互参数文件，实测 `InteractiveParamReader`）、`listTRS`、`MeshCreator`、`ConvergenceMethod`、`SpaceMethod`、`LinearSystemSolver`、`LSSNames`、`ConvergenceFile`、`ConvRate/ShowRate`
- 9.3.3 停止条件：`StopCondition = MaxNumberSteps | Norm`、`MaxNumberSteps.nbSteps`、`Norm.valueNorm`（实测 `valueNorm = -9.0`）
- 9.3.4 输出：`OutputFormat = Tecplot | CFmesh | ...`、各 Writer 的 `FileName/SaveRate/AppendTime/AppendIter`、输出变量集切换（TecplotWriter 用 `Data.outputVar`，AnalyticalEE/ParaViewWriter/TecplotWriterNavierStokes 等用 `updateVar`，实测两者均存在）、`Tecplot.Data.SurfaceTRS`（面 TRS 输出）
- 9.3.5 物理模型参数：`refValues/refLength/Reynolds/machInf/tempRef` 等逐项（每个 PhysicalModelType 一张参数表）
- 9.3.6 收敛方法参数：`NewtonIterator.Data.CFL.*`（`ComputeCFL = Function | Interactive`、`CFL.Function.Def` 分段函数语法，实测）、`AbsoluteNormAndMaxIter.MaxIter`、`MaxSteps`、LUSGS 参数、FR/SD 的 `BDF2/BDF3/CrankNicholson` 时间格式参数
- 9.3.7 空间方法参数：`ComputeRHS`（NumJacob/AnalyticalJacob）、`ComputeTimeRHS`（`PseudoSteadyTimeRhs`）、`FluxSplitter/UpdateVar/SolutionVar/LinearVar/DiffusiveVar/DiffusiveFlux/PolyRec/Limiter/limitRes`、`SetupCom/SetupNames/UnSetupCom`、`stencil`、`NodalExtrapolation`、轴对称
- 9.3.8 LSS 参数：`PCType/KSPType/MatOrderingType`（PCASM/KSPGMRES/MATORDERING_RCM 实测）及 PETSc 直通选项（`NbKrylovSpaces`、`MaxIter`、`RelativeTolerance`、`KSPShowRate`）
- 9.3.9 初始化与边界条件命令：`InitComds/InitNames`、`BcComds/BcNames`、`applyTRS`、`Vars/Def`（自由格式表达式，如 `x y` 与初值 `50. -5102.61 0. 288.`，实测）、BC 专有参数（`TWall`、`ZeroGradientFlags` 等）
- 9.3.10 其他专用节：`Maestro`、CUDA 设备配置、耦合器配置、动网格配置、`CFmeshFileReader.convertFrom`（Tecplot2CFmesh 等网格转换，实测）

### 9.4 网格格式支持
- 9.4.1 原生格式 `.CFmesh`（ASCII/二进制、结构段说明：节点/单元/状态/TRS）
- 9.4.2 外部格式转换：Gmsh、Gambit（`.neu`）、CGNS、Tecplot、FAST、THOR、DPL → `Xxx2CFmesh` 插件用法与限制
- 9.4.3 结构网格转换 `ConvertStructMesh`
- 9.4.4 网格质量要求与常见问题（单位、右手系、TRS 命名、`ScalingFactor` 缩放）

### 9.5 运行方式
- 9.5.1 命令行完整参考（实测 `apps/Solver/coolfluid-solver.cxx` 的 `AppOptions`）：`coolfluid-solver --scase <file> [--conf <xml>] [--bdir <dir>] [--ldir dir1 dir2 ...] [--log level] [--residual r --tolerance t] [--wait|--waitend] [--testEnv] [--help]`
- 9.5.2 串行运行、MPI 并行运行（`mpirun -np N` + 网格预剖分 ParMetis + 剖分文件）
- 9.5.3 环境变量与运行目录约定（`WorkingDir`、相对/绝对路径解析、`--bdir` 基目录，实测 `scase` 相对路径拼接逻辑）
- 9.5.4 运行输出解读：`config*.log`、`*-output.log`、收敛文件 `.conv` 格式
- 9.5.5 重启动：CFmesh 保存/续算字段与操作步骤（`CellCenterFVM.Restart = true` 实测）
- 9.5.6 调试运行：`--wait` 附加调试器（打印 PID 等待确认，实测）、日志级别、断言

### 9.6 作业提交脚本模板
- 9.6.1 Slurm 模板（串行/并行/MPI/CUDA 三种）
- 9.6.2 PBS/Torque 模板、集群 module 加载范例
- 9.6.3 参数扫描批处理脚本示例（bash 循环生成 CFcase）

---

## 第 10 章 后处理与可视化

### 10.1 输出数据格式
- 10.1.1 Tecplot：`TecplotWriter`（`.plt`；⚠️ **C 库接口直接放在插件根目录**——`TECXXX.h`、`TecplotWriterAPI.hh`、`preutil.c`，**不存在 `TecplotWriter/lib/` 子目录**）、`TecplotMerge`（分块合并）、多时刻输出与 `AppendTime/AppendIter`（实测可用键：`Simulator.SubSystem.Tecplot.FileName/SaveRate/AppendTime/AppendIter` + `Tecplot.Data.outputVar` + `Tecplot.Data.SurfaceTRS`，见 `cyl_Pg_M15_FVM_1st2nd.CFcase`）
- 10.1.2 ParaView/VTK：`ParaViewWriter`（`.vtu/.pvtu` 并行输出）
- 10.1.3 CGNS：`CGNSWriter` 用法与适用场景
- 10.1.4 CFmesh 输出（续算用）与输出变量集切换（`outputVar`/`updateVar`，Cons ↔ Puvt 等）
- 10.1.5 收敛历史 `.conv` 文件格式与绘制

### 10.2 派生量提取
- 10.2.1 气动系数：`AeroCoef` 插件（壁面积分、参考系）、`TecplotMerge` 内的 `CoefMerge.cxx` 系数合并工具
- 10.2.2 壁面热流与热流密度分布（`FiniteVolumeNavierStokes`/NEQ 后处理命令）
- 10.2.3 沿线/切面数据提取：`DataHandleOutput`、`ContourIntegrator`
- 10.2.4 LES 统计量：`LESDataProcessing`（平均/脉动/谱）

### 10.3 可视化工作流
- 10.3.1 ParaView 工作流：加载 `.vtu`、流线/等值面/Q 判据、并行分区可视化
- 10.3.2 Tecplot 360 工作流与 `tools/tecplot/` 宏（`.mcr`、`.eqn` 方程文件，实测）
- 10.3.3 残差与目标量监控图（matplotlib/gnuplot 脚本模板）

### 10.4 数据提取与分析脚本
- 10.4.1 Python 读取 `.plt`/`.dat`/`.conv` 的脚本模板（`tools/scripts/`（含 `Python/` 子目录）、`tools/MeshGeneration/` 中现有脚本索引）
- 10.4.2 批量算例对比与误差统计脚本
- 10.4.3 与已有评估报告联动的脚本（`doc/high_enthalpy_testcases_report.md` 配套）

---

## 第 11 章 二次开发指南

### 11.1 开发环境与代码规范
- 11.1.1 目录与命名规范（`tools/style/`、`tools/templates/` 模板、`tools/dev/` 开发脚本、`tools/apply_all_fixes.sh` 等）
- 11.1.2 版权头与 LGPL 声明模板（`tools/scripts/addgplv3header.sh`）、Doxygen 注释规范
- 11.1.3 编码基础类型：`CFuint/CFint/CFreal`、`SharedPtr/SafePtr`、`CFLog/cf_assert/cf_always_assert`、`FromHere()` 异常上下文
- 11.1.4 显式模板实例化（`.ci` 文件机制）与 `CF_ENABLE_EXPLICIT_TEMPLATES`（→`CF_HAVE_CXX_EXPLICIT_TEMPLATES`）

### 11.2 理解 Provider/工厂模式（开发的前置知识）
- 11.2.1 三种 Provider 详解与最小注册代码示例
- 11.2.2 ConfigObject：`defineConfigOptions()`、`configure()`、参数表编写
- 11.2.3 DataSocket 数据申明与生命周期（源/汇模式）

### 11.3 创建自定义插件（手把手教程）
- 11.3.1 用 `AutoTemplateLoader`/`EmptySpaceMethod` 起步：目录结构、`CMakeLists.txt`（`CF_ADD_PLUGIN_LIBRARY` 宏）编写、`CF_EXTRA_SEARCH_DIRS` 源码树外开发（实测机制）
- 11.3.2 插件入口（**实测更正：不是 `LoadLib` 函数**）：声明 `XxxModule : public Environment::ModuleRegister<XxxModule>`（`getModuleName()`/`getModuleDescription()`）+ 在 `.cxx` 里放置 `ObjectProvider`/`MethodStrategyProvider` 的**全局实例**（静态自注册），无需任何 `extern "C"` 导出函数
- 11.3.3 单元测试：集中于 `src/UnitTests/`（`utest-*.cxx`，MathTools 等）与 `CF_ENABLE_UNITTESTS` 开关、CTest 接入（`CFAddTest.cmake`）；注：插件内无 `testsuite/` 目录，原大纲表述已修正
- 11.3.4 插件调试技巧（日志、`MarcoTest` 参考、`--wait` gdb 附加）

### 11.4 新增物理模型教程
- 11.4.1 定义 `PhysicalModelType` 与变量集（以"新增理想气体+组分输运"为例）：VarSet 转换函数、`setupPhysicalData`、CFcase 参数
- 11.4.2 实现通量与源项：`ConvectiveVarSet::computeFlux`、`ComputeSourceTerm`
- 11.4.3 新增边界条件命令（以"压力远场"为例）：继承 FVMCC BC 基类、注册、CFcase 配置
- 11.4.4 接入第三方库（参照 `MutationUsage`/`MutationppI` 的封装模式）

### 11.5 新增数值格式教程
- 11.5.1 新增 FluxSplitter（以"AUSMPW+"为例）：继承关系、注册、CFcase 启用
- 11.5.2 新增 PolyRec/限制器
- 11.5.3 新增 ConvergenceMethod（以"SSP-RK3"为例）
- 11.5.4 新增 LinearSystemSolver（参照 `Pardiso` 封装）
- 11.5.5 新增 SpaceMethod 家族的一般路线（参照 `EmptySpaceMethod` → `SpectralFV` 的层次）

### 11.6 API 参考
- 11.6.1 内核公共 API 速查：Simulator/SubSystem/MeshBuilder/DataStorage/Factory/PE/OptionList
- 11.6.2 方法开发者 API：SpaceMethod/ConvergenceMethod/LSS/Command 接口签名
- 11.6.3 Doxygen 生成与在线浏览（`doc/doxygen.config.in`、`make doc`）

### 11.7 测试与质量保证
- 11.7.1 单元测试框架与组织（`src/UnitTests/`、Boost 组件 unit_test_framework 编译依赖）
- 11.7.2 算例回归测试（`--residual`/`--tolerance` 机制、CTest dashboard `coolfluidsrv.vki.ac.be/cdash`）
- 11.7.3 内存与性能检查：Valgrind、GooglePerftools 集成

---

## 第 12 章 附录

### 12.1 术语表
- 内核术语：Kernel、Plugin、Simulator、SubSystem、Maestro、TRS、GeoEntity/GE、State、Node、CFcase、CFmesh、Provider、DataSocket/DataHandle、FVMCC、RDS、FR、SD、SV、LSS、VarSet、PM（Physical Model）、BC、Ghost/Dummy State、ParMetis 剖分、VCJH
- 物理术语：CNEQ/TCNEQ、LTE、2T/2TV、MII、VT 弛豫、HSNB、ICP、γ-Reθ、GCL、CFL

### 12.2 符号说明
- 数学符号约定（守恒变量、通量、雅可比）、无量纲量、上下标约定

### 12.3 参考文献
- 12.3.1 方法论文：Roe (1981)、AUSM 族（Liou）、HLL（Harten 等）、RDS（Roe; van der Weide & Deconinck LDA-PSI/FCT）、FR（Huynh; Vincent-Castonguay-Jameson）、SD（Kopriva）、SV、DG（Cockburn）
- 12.3.2 COOLFluiD 论文：Lani 博士论文（VKI）、MHD 论文（CmPA/Kim）、FR 手册、VKI 系列
- 12.3.3 物理化学：Gupta/Yos 热力学曲线拟合、Park 两温度模型、Mutation/Mutation++ 论文、air5/air11 反应集
- 12.3.4 软件工程：COCONUT 项目文档、Boost.PTR 体系

### 12.4 常见问题排查表（FAQ 汇总）
- 运行期：插件加载失败（`Could not load library`）、TRS 未定义、BC 命令与物理模型不匹配、发散（CFL 调整策略）、NaN 排查、并行不守恒
- 编译期：见第 8.7 节汇总表

### 12.5 版本变更记录
- Kernel 1.x → 2.x 主要 API 变迁、2013.9 版内容快照、与上游 GitHub（andrealani/COOLFluiD）的关系

### 12.6 许可证与版权
- LGPL v3 全文指引（`LICENSE`、`doc/lgpl.txt`、`doc/gpl.txt`）、第三方组件许可（Boost、log4cpp、Tecplot 接口、Mutation）

---

## 附：编写计划与工作量估算（供立项参考）

| 阶段 | 章节组合 | 预估篇幅 | 前置工作 |
|------|----------|----------|----------|
| P1 | 第 0、1、2 章 + 第 8 章 | ~60 页 | 构建系统实测、依赖清单核验 |
| P2 | 第 9 章 + 第 10 章（用户主路径） | ~70 页 | CFcase 字段全量提取（可用 Doxygen/脚本扫描 `addConfigOption`） |
| P3 | 第 3 章 + 第 4 章 | ~90 页 | 对照 `doc/Manuals/*.tex` 已有手稿、通读插件核心类 |
| P4 | 第 6 章 + 第 7 章 | ~100 页 | 逐插件模板化扫描 + 算例批量试跑 |
| P5 | 第 5 章（最重） | ~120 页 | 建议脚本化生成文件索引骨架后人工补充 |
| P6 | 第 11 章 + 第 12 章 | ~60 页 | 跑通模板插件示例后撰写 |

**通用素材清单**（写作前准备）：类图（Doxygen 生成）、调用链（LSP/gdb 提取）、CFcase 选项全表（正则扫描源码 `addConfigOption<...>("...")`）、插件清单表、算例清单表、编译日志样例、ParaView/Tecplot 截图。

---

## 附 B：本次核对修正记录（2026-08 对照代码库实测）

1. **1.1.2 全称**：改为官网一致的 **Computational Object-Oriented Libraries for Fluid Dynamics**（原"COmpact Object Oriented PDE solving Library..."有误）。⚠️ 补充精度：**本仓库 `README.md` 未逐字写出该全称**，仅描述为 "The object-oriented HPC platform for CFD, plasma and multi-physics simulations"（`README.md` 第 2 行附近）；第 1 章正文已加准确性说明，引用出处以官网为准。
2. **2.1.3 / 8.5.1**：选项名 `CF_ENABLE_SINGLE_EXEC` → **`CF_ENABLE_SINGLEEXEC`**（编译宏 `CF_HAVE_SINGLE_EXEC`）。
3. **2.2.1 / 5.1（src/Common）**：删除不存在的 `CFObject`、`AutoPtr`、`Factory.hh`（Common 仅有 `FactoryBase`）、`PEAPI`、`PEOperations`、`NotFound`、`BasicFunctions`、`Timing`、`FilesystemUtils`、`Logger/LogLevel`（在 logcpp）、`MathConsts/MathTools`（在 src/MathTools）；补 `OwnedObject/SetupObject/NamedObject/TaggedObject`、`PEInterface/PEFunctions`、`Stopwatch/TimePolicies`、`FileDownloader`、`ShouldNotBeHereException`。
4. **2.2.2 / 5.2（src/Config）**：`BadFormatException` 实际在 `src/Framework/`；`ShouldNotBeHere` 实际为 `Common/ShouldNotBeHereException.hh`；无 `OptionArray`/`ConfigCaller`（为 `OptionT`/`ConfigFacility`）；补 `NestedConfigFileReader`、`XMLConfigFileReader`。
5. **2.3.2**：`NavierStokes2D` 等具体物理模型类位于插件中；TCNEQ 为 `plugins/NEQ` 的模板类 `NavierStokesTCNEQVarSet`；`Rhoivt` 两义说明；补 `RoeVinokur` 位置。
6. **2.3.3**：`CFPolyOrder` 为 P0–P10（枚举 ORDER0–ORDER10），原"P0–P6"有误。
7. **3.1.3**：`GReKO` 是 γ-Reθ 转换模型（非 EARSM）；LES 亚格子模型实测为 Smagorinsky/WALES/Clark/Gradient（无 Vreman、DynamicSmagorinsky）；补 `GammaAlpha`、`NEQKOmega`。
8. **3.1.5**：`getSourceVT` → **`getSourceTermVT`**；Mutation2.0I `data/` 为 6 类子目录、191 个物性文件（138 表 + 26 `.mix` + 27 `.ceq`）实测相符。
9. **3.2.1 / 4.1.2**：代码中**不存在 `VertexCenterFVM`**（节点中心离散由 RDS/FluctSplit 承担），已删除相关章节并改写。
10. **3.2.4 / 4.1.5**：FR 修正函数实测为 **VCJH 族**（`VCJH.hh`，能量稳定；参数可覆盖 SD/CU/HU），原"修正函数类型 SD/CU/HU"表述修正。
11. **4.1.1**：`stencil` 实测含 `FaceVertexPlusGhost`。
12. **4.1.6**：SpectralFD 点分布基于 FR 的 `BasePointDistribution`；粘性处理实测含 BR2 与 LocalApproach；"FLIP"无代码对应。
13. **4.2.1**：通量实测清单——删除不存在的 **HLLC、Jameson、AUSMPlusUp2**；补充 Roe 族（RoeFast/RoeSA/RoeVLPA/RoeTurb/RoeLin）、AUSM 族（含 _Mp/_MpW/LiouSteffen/LowMlimit/Prec）、HLL/HLLE、LaxFried、GForce。
14. **4.3.1**：删除不存在的 `LimiterVanAlbada`；限制器实测 BarthJesp/Venktn2D/3D/CustomLimiter/MinMod 族。
15. **4.4.4**：删除不存在的 `Mechanical*` 类；改为低马赫预处理通量（`AUSMFluxPrec`/`AUSMPlusFluxPrec`）+ 不可压算例。
16. **4.6.2**：无独立"隐式残差光顺"模块，表述修正。
17. **5.8.14**：`CFmesh2THOR` 无 `CMakeLists.txt`（未纳入构建）；`XCFcaseConverter` 为命令行工具（`main.cxx`）。
18. **6.1**：分类表补充 **GammaAlpha、LagrangianSolver、NEQKOmega、TecplotWriterNavierStokes**；移除 CFmesh2THOR（未构建）。
19. **6.3.1**：库命名为 `lib<插件名>.so`（如 `libPetscI.so`），无 `libCF_` 前缀；`build/dso/` 实测。
20. **6.3.4 / 8.2.3**：不存在 `coolfluid-<Name>.cmake`；`coolfluid.cmake` 是构建目录中可选 INCLUDE 的 CMake 文件，与个人配置 `coolfluid.conf` 区分。逐插件开关机制（**`prepare.pl` 实测，表述需更精确**）：`prepare.pl:744` 读取 `lib_<NAME>` 键（该键的**模板样例**在 `tools/conf/coolfluid.conf.minimal:21-36`；**本仓库根目录的 `coolfluid.conf` 并不含 `lib_xxx=` 行，而是用 `allactive = 1`（`coolfluid.conf:42`）**）；生成的开关**不止 `CF_BUILD_<LIBNAME>` 一种**——禁用时同时发 `-DCF_BUILD_$_=OFF` 与 `-DCF_COMPILES_$_=OFF`（`prepare.pl:882-883`），启用时只发 `-DCF_COMPILES_$_=ON`（:894，"plugins are ON by default"，见 :878 注释），`install_api` 时另发 `-DCF_BUILD_<lib>_API=ON`（:904）。
21. **7.1.2**：`init_testcases.sh` 为**按需解压**（COCONUT 系列与 SolarCorona），并非解压全部 751 个 `.xz`。
22. **7.3.2**：目录名为大写 `BLAST/`（`blastM6_aoa20_postprocessing.CFcase` 实测）。
23. **7.4.1**：MHD 算例中**无 Brio-Wu**；改为 ShockTube（Powell/投影）、COCONUT 系列（Dipole/Eclipse/MHDRotor/OrszagTang/Quadrupole 等）、SolarWind 等实测清单。
24. **8.5.1**：补齐 `CF_ENABLE_SINGLEEXEC/EXPLICIT_TEMPLATES/GROWARRAY/INTERNAL_DEPS/WARNINGS/STDASSERT/DEBUG_MACROS/LOG4CPP/CURL/GSL/MUTATIONPP/PLATO/VIENNACL/DOCS`、`CF_CUDA_MALLOC`、`CF_SKIP_FORTRAN`、`CF_ENABLE_IBMSTATIC/CRAYSTATIC`、`CF_TESTCASES_NCPUS` 等。
25. **9.3.4 / 10.1.4**：输出变量集选项实测为 `outputVar`（TecplotWriter）与 `updateVar`（AnalyticalEE/ParaViewWriter 等）并存。
26. **11.3.3 / 2.6.2**：插件中**无 `testsuite/` 目录**；单元测试位于 `src/UnitTests/`（`utest-*.cxx`），由 `CF_ENABLE_UNITTESTS` 启用。
27. **0.4**：补充 `COOLFLuiD_Manual.pdf`、`COOLFluiD_RDS_UnsteadyNavierStokes.tex` 等 doc/Manuals 实测清单。
28. **1.3.1 / 1.4.2**：补充 ATD 电弧热等离子体（`ATDModel`）、燃烧（`FiniteVolumeCombustion`）、拉格朗日粒子（`LagrangianSolver`）、太阳物理（COCONUT）。
29. **1.3.3**：补充并行 I/O、混合 MPI/CUDA（官网特性）。
30. **9.5.1 / 7.1.3**：命令行选项与 `--residual/--tolerance` 语义（允许百分比偏差，默认 3.0%）经 `coolfluid-solver.cxx` 实测确认。

---

## 附 C：第二轮源码逐项核对修正记录（2026-08，第 3/4 章算法与模型部分）

本轮针对"**数学物理模型与算法原理必须与源码逐项一致**"的要求，对第 3、4 章的全部公式推导、源码行号、注册名与配置语义做了一次全量复核。以下为修正项（均已给出实测文件:行号）。

### C.1 第 3 章（数学与物理模型）

31. **3.2.1 笛卡尔通量（重要）**：手册引用的 `Euler2DVarSet::computeFlux(State, physdata, flux)`（`Euler2DVarSet.cxx:174-195`）**位于 `#if 0` 之内，是死代码**（`#endif` 在 196 行，注释为"keep this function here untill we implement the FluctSplit MetaSchemes properly"）。实际生效的笛卡尔通量函数是 **`computeStateFlux()`（128-169 行）**，它通过 `EquationSetData::getEqSetVarIDs()` 支持方程子系统。已在手册中改为以 `computeStateFlux` 为主、历史版本折叠为对照。
32. **3.1.2 枚举**：补入 `EulerTerm.hh:85-86` 完整枚举（`RHO=0,P=1,H=2,E=3,A=4,T=5,V=6,VX=7,VY=8,VZ=9,GAMMA=10,XP=11,YP=12,ZP=13`）及"物理数据长度 14、标量变量自下标 14 起"。
33. **3.2.3(5) SA（重要）**：`getExtraPhysicalData` **在代码树中不存在**；实际函数是 **`setDimensionalValuesPlusExtraValues()`**（`EulerSAVarSet.ci:132`，湍流粘度计算段在 168-183）。按旧名检索会一无所获。
34. **3.2.3(6) $k$-$\omega$ 注册名（重要）**：① **不存在** `NavierStokes2DKOmegaSST` / `NavierStokes2DKLogOmegaSST` 这类"物理模型"名——SST/BSL/$k$-$\varepsilon$ 是**变量集**；② 3D 多为 `Pvt` 后缀而非 `Puvt`：实测 `NavierStokes3DKLogOmegaSSTPvt`、`NavierStokes3DKLogOmegaBSLPvt`（旧版写作 `…SSTPuvt`/`…BSLPuvt` 有误）；③ 补入 SST 代码的 `std::max(...) == 0.0` 除零保护、"SST 无 `exp`、无 `std::max(0.,k)`"、以及 `if (_wallDistance > 0.)` 包裹（未算壁面距离时 `mut` 恒为 0）三条实现细节。
35. **3.2.3(7) LES（重要）**：`nuSGS` 的构造**在不同类/不同重载中并不相同**——`Clark2DVarSet:168-171` 用 `Cs=0.18`、`D=radius`、`nuSGS=Cs²D²S`；而 `Smagorinsky2DVarSet::getFlux(state,normal,radius)` 用 `D=3.0*radius`、`nuSGS=D²*mut`，其第 91 行的 `Cs=0.1` **声明后未使用**，且 `dim` 硬编码为 `3.0`（:32）。旧版把两者混为一谈，已补对照表。
36. **3.2.4 MHD（重要，多处）**：
    - "8 个守恒量"仅对**理想 MHD** 成立（`MHDPhysicalModel.ci:49` 直接 `return 8`）；`MHDProjection`/`MHDProjectionDiff` 为 **9**（`MHDProjection.ci:51`，第 9 个分量 `phi`），`MHDProjectionEpsDiff` 为 **11**（`MHDProjectionEpsDiffPhysicalModel.ci:35`），`MHDProjectionPolytropic` 为 8。已补分模型表格。
    - 补 `MHD3DCons.cxx:511`（`p=(γ-1)(ρE-½ρV²-½B²)`，2D 同 `MHD2DCons.cxx:508`）作为"总能量含磁能"的源码依据。
    - **`AUSMPWMHD` 不存在**，实际注册名是 **`AUSMPWMHD2D` / `AUSMPWMHD3D`**（`FiniteVolumeMHD/AUSMFluxMHD.cxx`）。
    - 派生模型名是 `MHD2DProjection`+`Diff`/`EpsDiff`/`Polytropic`（`Projection` 在中间），**不存在** `MHD2DPolytropic`。
    - 补 `MHD` 的 10 个 `PhysicalModelType` 注册名全表与变量集清单（`MHD3DProjectionDiffPrim` 而非 `MHD3DProjectionDiff`）。
37. **3.2.4 多流体 MHD（重要）**：**`RhoiViTi` / `HalfCons` 不是可用注册名**，只是名字片段。实测：物理模型为 `MultiFluidMHD2D`、`MultiFluidMHD2DRhoiViTi`、`MultiFluidMHD2DHalfRhoiViTi`、`MultiFluidMHD3D`、`MultiFluidMHD3DRhoiViTi`；变量集为 `EulerMFMHD2DCons/HalfCons/RhoiViTi/HalfRhoiViTi`、`EulerMFMHD3DCons/RhoiViTi`。
38. **3.2.5 NEQ（多处）**：
    - `PhysicalChemicalLibrary` 三个源项接口的**精确签名与行号**已补（`getMassProductionTerm` :419-426、`getSourceTermVT` :434-439、`getSourceEE` :478-484，另有 `getSource` :455-464）。**`getSourceTermVT` 的末参 `omegaRad` 同时回传辐射源项**——这是流场-辐射耦合的数据通道，此前未说明。
    - **`includeElectronicEnergy` 是物性库子选项**（`MutationLibrary2.cxx:350`、`MutationLibrary2OLD.cxx:322`，各默认 `false`），**不在 `plugins/NEQ` 中注册**；`MutationI` 与 `MutationppI` 不提供该选项。已补选项归属对照表。
    - `nbVibEnergyEqs` 注册于 `EulerNEQ.ci:22` 与 `NavierStokesNEQ.ci:28`（默认 0），决定 `nbEqs = nbEulerEqs + nbSpecies + nbVibEnergyEqs + nbTe`，并经 `setNbTempVib()`（:258）传给物性库。
    - **`NavierStokes2DTCNEQ` / `NavierStokes3DTCNEQ` 作为 `PhysicalModelType` 不存在**。带 `TCNEQ` 的注册名只有源项命令 `NavierStokes2DTCNEQST`（`NavierStokes2DNEQAxiSourceTerm.cxx:58`）与 `NavierStokes2DTCNEQAxiST`（:42）。`NavierStokesTCNEQVarSet` 是**模板基类**（只有 `.hh`+`.ci`，无 `.cxx`，从不注册），由 `NavierStokesNEQRhoivt.cxx:30` 实例化。
    - 补 NEQ 变量集注册名实测全表（Euler 层 18 个 + NS 层 13 个 + 变换器），并澄清 **`RoeVinokur` 是变量集**（`Euler2DNEQRoeVinokur`）而 **`RoeVinokurTCNEQFlux` 是通量分裂器类名**（注册名为 `RoeVinokurTCNEQ2D/3D`、`…2DSA/3DSA`、`…2DVLPA/3DVLPA`、`RoeVinokurEntropyFixTCNEQ1D`，`RoeVinokurTCNEQFlux.cxx:34-72`，其中 3D 变体在 :53/:59/:65 被注释）。
39. **3.6.3 FVMCC 命令计数与全表（重要）**：旧版"129（24+88+18）"不准。实测：三个插件去重注册名分别为 **24**（26 个中含 `"FVMCC"` 与 `"FVMCCSingleState"` 两个**空间方法**名，需剔除）、**89**、**18**，并集因 `CoupledNoSlipWallIsothermalNSrvtLTE_NodesFVMCC` 重复而 **= 130**。同时旧表遗漏了整族命令：**`SubInlet*` 17 个、`SubOutlet*` 16 个、`Unsteady*` 6 个**，以及 `MirrorEuler2D/3DFVMCC`、`MirrorVelocity2DTurb/3DTurbFVMCC`、`SuperInletRhoVTFVMCC`、`CoupledPorousEuler2DFVMCC`、`ComputeVariablesDerivativesFVMCC`。另发现源码拼写遗留 `NoSlipWallIsothermNS2DFVMCC`（缺 `al`）。已全部补入并加"按入口给定量选型"提示。
40. **3.5.5 FR 阶次**：`CFPolyOrder` 枚举支持 `P0`–`P10`，但实际可用上限受单元类型形函数/求积实现限制（Triag/Tetra 较窄）；旧版"P0–P8"过于绝对，已按"以 `testcases` 实际跑通阶次为准"表述。

### C.2 第 4 章（核心算法）

41. **4.2.3(5) `updateRHS()`（重要）**：旧版把右单元累加写成注释形式（"// rhs(lastStateID...) += ..."），与 4.2.2 伪代码第 19 行及本节自述自相矛盾。**实际代码（`FVMCC_ComputeRHS.cxx:492-499`）确实执行 `rhs(lastStateID,iEq,nbEqs) += _rFlux[iEq]*_invr[1]`**；若按旧版理解，内部面通量将不成对抵消、全局不守恒。已更正，并补 `_invr[1]` 仅在轴对称分支赋值、以及 `cf_assert(firstStateID < lastStateID)` 定向不变式。
42. **4.3.6 限制器参数语义（重要，旧版完全反了）**：`limitIter` / `limitRes` **不是**"到某步/某残差才启用限制器"。实测 `FVMCC_PolyRec.cxx:145-163`：当 `residual > limitRes` **且** `iter < limitIter` 时走**分支 A**——先把限制器重置为 `1.0` 再重算（即每步可放松）；否则走**分支 B**——不再重置，而是 `newLimiter = min(old, new)` 单调收紧（利于收敛到机器精度）。`_limitIter` 默认 `1e9`（:58）。`FreezeLimiter` 只在分支 B 生效。此外 **`gradientFactor` 不是 `LinearLS2D` 的标量选项**，而由基类 `Def`/`Vars`（`FVMCC_PolyRec.cxx:25-26`）的函数机制驱动（`Vars = i` 时为迭代号的函数，:108-116）。已重写该节，并同步修正 4.12 与 4.17.1 的表述。
43. **4.4.7 通量格式全表（重要，重做）**：改为全仓库 `FluxSplitter` 注册名实测清单。关键更正：
    - **`RoeFast` → `Fast`**（`RoeFluxFast.cxx`）；**`RoeLin` → `Linearized` / `LinearizedALE`**（`RoeFluxLin.cxx` / `RoeFluxLinALE.cxx`）；`RoeT4` 正确（`RoeFluxT.cxx`）。
    - **低马赫预处理**：类名是 `AUSMPlusFluxPrec` / `AUSMFluxPrec`，**可用注册名是 `AUSMPlusP1D/2D/3D` 与 `AUSMPlusPMS1D/2D/3D`**（`AUSMFluxPrec.cxx:25-60`）。旧版把类名当注册名。
    - **`HLLE` 无维度后缀的形式不存在**，只有 `HLLE1D/2D/3D` 与 `HLLEMS1D/2D/3D`（模板在 `FiniteVolume/HLLEFlux.ci`，实例化于 `FiniteVolumeNavierStokes/HLLEFlux.cxx:29`）。
    - **多流体 MHD**：无 `AUSMFluxMultiFluid`，无 `LaxFriedFluxMultiFluid*ALE`；只有 `AUSMPlusUpMultiFluid2D/3D`（+`ALE`）与 `LaxFriedFluxMultiFluid2D/3D`。
    - 补入此前遗漏的 `LaxFried`、`LaxFriedBCCorr`、`LaxFriedCoupling`、`GForce`、`StegerWarming`、`VanLeer1D/2D/3D`（+`MS`）、`RoeSAGhost`、`RoeFluxALEBDF2`、`AUSMPlus_Mp(_MpW)`、`AUSMPlusUp_Mp(_MpW)`、`AUSMPlusUpMSPvt2D/3D`、`AUSMPlusUpIcp_cp`、`AUSMPlusUpTurb3DLTE`、`AUSMFluxLTE`，以及 NEQ 族（`RoeTCNEQ*`、`RoeVinokurTCNEQ*`）与 MHD 族（`HLLEMHD*`、`MHD*ConsRoe`、`MHD3D*LaxFriedTanaka`、`HLLDecE`）全表。
    - **"每个格式都有 `*ALE` 变体"是错的**（多流体 LaxFried 就没有），已改为逐行标注。
44. **4.5.3(3)（重要）**：`_diffVar->getCurrDensityState(_avState)` **不存在**，实际是 **`_diffVar->getDensity(_avState)`**（`NSFlux.ci:128`）。另补：`computeControlVolume` 与轴对称半径在 `if (!isPerturb)`（:77-100）内，而 `setGradientVars`/`computeGradients`/`computeAverageValues` 在扰动时照常执行（:105-111）——澄清了 4.8.2"扰动模式跳过无关副作用"的准确含义（跳的是几何相关，不是状态相关）。
45. **4.8.3 稀疏模式（重要）**：**不存在名为 `JacobianSparsity` 的配置选项**，且可填值**不带 `Sparsity` 后缀**（带后缀的是 C++ 类名）。实测 `GlobalJacobianSparsity` 注册名：`CellCentered`、`CellVertex`、`CellVertexNoBlock`、`CellCenteredDiffLocalApproach`（`src/Framework/`）与 `FVMCellCentered`、`FVMCellCenteredNoBlock`（`plugins/FiniteVolume/`）。另注 `CellCenteredDiffLocalApproachSparsity::computeMatrixPattern()`（`src/Framework/...:309-315`）目前直接 `throw NotImplementedException`，只实现了 `computeNNz`。
46. **4.11.1 SD 配置（重要）**：`Data.FaceDiffFlux = NSStdBR2` **不存在**。实测 `FaceDiffFlux` 取值为 `NSBR2Approach` / `NSIPApproach` / `NSLocalApproach` / `LESBR2Approach` / `LESIPApproach` / `LESLocalApproach` / `LocalApproach`；而 `NSStd*` 是 `FaceTermComputer` / `BndFaceTermComputer` / `VolTermComputer` 三族的前缀。已补三个选项的分工与取值全表（选项定义见 `SpectralFDMethodData.cxx:41-44, 105-114`）。
47. **4.7.6 时间推进全表**：补 `NewtonIteratorCoupling`、`BDF2Intermediate`、`BDF2_InitCN`、`NonlinearLUSGSCrankNich`、`NonlinearLUSGSIteratorComputDiagJacob`、`L2LUSGS`；并明确 **`CrankNicholsonLim` 是独立注册名**（旧版写作 `CrankNicholson`（±`Lim`）易被理解为加后缀）。
48. **4.7.7 低马赫**：改写为可检索的三层对策（格式 `AUSMPlusP*`/`AUSMLowMlimit`、模型 `Incomp*`、PETSc 侧 `DifferentPreconditionerMatrix`（`PetscLSSData.cxx:45`）+ `"PreconditionerMatrix"`（`ParMFSetup.cxx:154`、`ParJFSetup.cxx:217,225`））。旧版"代码：`Preconditioner` 相关命令"无法检索；并说明 `FVMCC_ComputeRHSSingleState.cxx:90` 的 `PreconditionerData` 是数据结构而非命令。
49. **4.8.4 PETSc 预条件子**：补 `BJacobi`/`BSOR`/`ILU`/`DPLUR`/`LUSGS` 的类名与行号（`plugins/Petsc/*Preconditioner.cxx:35-41`，均为 `ShellPreconditioner` Provider），并补 `FRP0Precond`（`FluxReconstructionPetsc/FRP0Preconditioner.cxx:50`）；明确它们与 PETSc 原生 `PCType` 是两套机制。
50. **4.3.2 / 4.5.5 模板**：`LeastSquareP1Setup.stencil` 不是枚举值，而是 **`ComputeStencil` 的 Provider 注册名**（`LeastSquareP1Setup.cxx:157` 用 `FACTORY_GET_PROVIDER` 动态创建）。实测取值除 `FaceVertex`、`FaceVertexPlusGhost`、`FaceBVertex` 外，还有 **`FaceEdge`** 与 **`Face`**。并澄清法方程规模只由 `getDim()`（2D $2\times2$、3D $3\times3$）决定，与模板宽度无关。
51. **4.17.2 限制器表**：补 `Venktn3DStrict(T/T3F)`、TVD 函数族（`MC`/`OSPRE`/`HQUICK`/`HCUS`/`KOREN`/`SMART`/`Superbee`/`Sweby`/`UMIST`）、`Null`；并澄清**空间限制器（`Limiter<CellCenterFVMData>`，`Data.Limiter`）与时间限制器（`TimeLimiter`，由 `CrankNichLimInit`/`UFEMInit` 的 `TimeLimiter` 选项或 `FVMCC_BDF2TimeRhsLimited:73,78` 选择）是两套 Provider 体系**——时间限制器注册名**不带** `TimeLimiter` 后缀，故 `Superbee` 等名字在两套体系中同时存在，取决于填在哪个选项。另补 `BarthJesp3D` 的 `m_useFullStencil` 默认为 `false`（`BarthJesp.cxx:47-49`）。
52. **4.10.4 配置表**：`PolynomialOrder` 的可用上限说明按 40 条统一口径修正；补此前遗漏的 **`GeoPolynomialOrder`**（`MeshUpgradeBuilder.cxx:50`，曲边网格需 ≥ `P2`）。
53. **4.18.3 源码对照表**：补 `RoeFluxFast.cxx`（`Fast`）、`RoeFluxLin.cxx`（`Linearized`）、`RoeSAFluxGhost.cxx`、`RoeFluxALEBDF2.cxx`、`GForceFlux.cxx`、`LaxFriedFlux.cxx`、`StegerWarmingFlux.cxx`，以及 NEQ / MHD / 多流体 MHD 三族的源码落点。

### C.3 经复核确认无误的关键条目（供信任度参考）

- `Euler2DCons::computePhysicalData` 441-465、`computeStateFromPhysicalData` 469-477：与手册逐行一致 ✓
- `Euler2DVarSet.cxx:93-117` 法向通量：与手册公式 $\mathbf F\cdot\mathbf n=(\rho u_n,\rho uu_n+pn_x,\rho vu_n+pn_y,\rho Hu_n)^T$ 逐行一致 ✓
- `RoeFlux.cxx:120` `compute` / :146-149 特征分解 / :153 `setAbsEigenValues` / :162 Roe 通量（含 `getReductionCoeff()`）/ :165-185 `updateCoeff` ✓
- `NSFlux.ci:59` `computeFlux` 六步流程 ✓
- `MirrorEuler2D.cxx:80-81`（镜面反射）、`NoSlipWallIsothermalNS2D.cxx:100-120`（$T_g=2T_w-T_i$ + ghost 节点动态重置 + `factor` 缩放）✓
- `FVMCC_ComputeRHS.cxx:139` `execute` / :455 `updateRHS` / TRS 跳过规则（`PartitionFaces`、`InnerCells`、`noBCTRS`）✓
- `MUSCLPolyRec.cxx:104` `extrapolateInner`（$\Delta_-,\Delta_c,\Delta_+$ 与 `_r1/_r2`）✓
- `BarthJesp.cxx:60` `limit` ✓（`m_useFullStencil` 分支与 :108-116 的面邻居分支）
- `LDASchemeSys.cxx:67` `distribute` ✓（`_kPlus`、`_sumKplus`、`_invK`、`currBetaMat`）
- `FluxReconstructionSolver.cxx:466` `computeSpaceResidualImpl` 九步流程 ✓
- `NewtonMethod/BDF2.cxx:101` `takeStepImpl` 的 $\alpha$/$\xi$/$\theta$ 与首步退化 ✓
- `FluctSplit/PseudoSteadyTimeRhs.cxx:81` `execute` ✓
- FR 配置项 `RiemannFlux`、`SolutionPointDistribution`、`FluxPointDistribution`、`CorrectionFunctionComputer`、`VCJH.CFactor`（`FluxReconstructionSolverData.cxx:51-59,105-117`；`VCJH.cxx:40,53`）✓
- `MeshUpgrade` Builder + `PolynomialOrder`（`MeshUpgradeBuilder.cxx:43,49-50`）✓
- `CellCenterFVM` 轴对称选项 **`isAxisymm`**（`CellCenterFVMData.cxx:45`）✓；`DiffusiveFlux` 选项（同文件 :36）✓；`NSFlux<NavierStokesVarSet>` 注册名 **`NavierStokes`**（`FiniteVolumeNavierStokes/NSFlux.cxx:23-28`）✓
- 时间推进注册名 `FwdEuler`、`RK`、`RK2`、`RKLS`、`RKRD`、`BwdEuler`、`NewtonIterator`、`BDF2`、`CrankNicholson`、`Linearized`、`LinearizedBDF2`、`NonlinearLUSGSBDF2`、`NonlinearLUSGSGeneralBDF`、`NonlinearLUSGSIterator`、`NewmarkExplicit`、`NewmarkImplicit` ✓
- NEQ 模型注册名 5 个（`Euler1D/2D/3DNEQ`、`NavierStokes2D/3DNEQ`）✓
- Mutation 四个库类与注册名（`Mutation`/`Mutation2`/`Mutation2OLD`/`Mutationpp`）✓
- `PseudoSteadyTimeRhs` 的 `useGlobalDT` 选项（`FVMCC_PseudoSteadyTimeRhs.cxx:43`，默认 `false`）✓
- PolyRec 注册名 `Constant`、`ConstantLin`、`ConstantST`、`LinearLS2D/3D`、`LinearLS2DBcFix/Periodic/Lin/Turb`、`MUSCL` ✓

### C.4 第 5/6/8/9 章（内核、插件、构建、运行）第二轮补核

54. **`TimeTable` 不存在**：全仓库 0 命中（`find . -iname "TimeTable*"` 无结果）。`src/Environment/` 的 45 项中无此文件，已从大纲 2.2.3 / 5.3 删除。
55. **`ConfigRegistry` 归属错误**：它在 **`src/Environment/ConfigRegistry.hh/.cxx`**，不在 `src/Config/`。已修正大纲 2.2.2 / 2.2.3 / 5.2 / 5.3 与第 5 章正文。
56. **`LeastSquareSolver` → `LeastSquaresSolver`**（`src/MathTools/LeastSquaresSolver.hh`，注意 `Squares` 为复数）；其 `.cxx` 为**空文件**（0 字节）。已修正大纲 2.2.5 / 5.5 与第 2 章正文。
57. **`SimpleMaestro` 是注册名而非文件名**：实现文件为 `src/Framework/SMaestro.hh/.cxx`（:33 注册 `"SimpleMaestro"`），耦合场景另有 `LMaestro.hh/.cxx`（`LoopMaestro`）。`apps/Solver/coolfluid-solver.cxx:304` 以字符串 `"SimpleMaestro"` 取 Provider。大纲 5.4.1 已改为"文件名与注册名不同名"的显式提示（第 2 章 2.3.1 与第 5 章 5.4.1 正文原本即写作 `SMaestro.cxx`，无误）。
58. **`CF_BUILD_<LIBNAME>` 机制需补充**（见修正第 20 条的改写）：`prepare.pl` 除 `CF_BUILD_*` 外还生成 `CF_COMPILES_*`（:882-894）与 `CF_BUILD_*_API`（:904）；且**本仓库根目录 `coolfluid.conf` 并不含 `lib_xxx=` 行**（用 `allactive = 1`，:42），`lib_xxx` 键的样例在 `tools/conf/coolfluid.conf.minimal:21-36`。
59. **`OptionArray` 类确认不存在** ✓（仅出现在旧文档中）；`src/Config/` 另有 `OptionMarkers.hh`、`OptionValidation.hh`，已补入。

### C.5 经复核确认无误的规模与运行事实

- 文件计数（`find -type f`）全部与手册一致：`src/` **1186**、`plugins/*.hh` **3301**、`*.cxx` **2930**、`*.CFcase` **1019**、`*.xz` **751**；单插件 `FluctSplit` 920、`FluxReconstructionMethod` 488、`FiniteVolume` 381、`FiniteVolumeNavierStokes` 268、`SpectralFD` 268、`SpectralFV` 163、`FiniteElement` 165、`DiscontGalerkin` 51、`NavierStokes` 835、`NEQ` 208、`MHD` 1093、`MultiFluidMHD` 257、`RadiativeTransfer` 232、`SubSystemCoupler` 206 ✓
- `apps/Solver/` 四项（`coolfluid-solver.cxx`、`coolfluid-solver.xml`、`PluginsRegister.hh`、`coolfluid-solver-wrapper`）✓
- `CFmesh2THOR` **确无** `CMakeLists.txt`，且 `plugins/CMakeLists.txt` 用 `FILE(GLOB PLUGIN_MODULES "*/CMakeLists.txt")` 发现插件 → 确实未纳入构建；`THOR2CFmesh` 正常构建 ✓
- `XCFcaseConverter` 确为命令行工具（含 `main.cxx`）✓；`TecplotMerge/CoefMerge.cxx` ✓
- **20 个 `CF_*` 构建选项全部存在**（顶层 `CMakeLists.txt`：`CF_SKIP_FORTRAN:10`、`CF_NO_LIBRARY_VERSION:147`、`CF_ENABLE_IBMSTATIC:241`、`CF_ENABLE_CRAYSTATIC:247`、`CF_ENABLE_SINGLEEXEC:259`、`CF_ENABLE_VIENNACL:383`、`CF_ENABLE_MUTATIONPP:392`、`CF_ENABLE_PLATO:399`、`CF_ENABLE_TESTCASES:443`、`CF_EXTRA_SEARCH_DIRS:503`；`cmake/DefineGlobalOptions.cmake`：`CF_ENABLE_LONG:12`、`CF_ENABLE_LLONG:17`、`CF_PRECISION_DOUBLE:31`、`CF_CUDA_MALLOC:35`、`CF_ENABLE_LOGALL:46`、`CF_ENABLE_EXPLICIT_TEMPLATES:68`、`CF_ENABLE_GROWARRAY:69`、`CF_ENABLE_INTERNAL_DEPS:70`、`CF_ENABLE_UNITTESTS:73`、`CF_TESTCASES_NCPUS:82`）✓
- `coolfluid-solver` 命令行选项恰为 11 个（:63-73），与手册完全一致；`--tolerance` 默认 **3.0** 且按百分比判定（:84、:360、:365-366、:369）✓
- `Restart` 选项在基类 `src/Framework/SpaceMethod.cxx:35` 声明 → `Simulator.SubSystem.CellCenterFVM.Restart = true` 有效（260+ 算例在用）✓
- `Data.TRSsWithNoBC`（`plugins/FiniteVolume/CellCenterFVMData.cxx:40`）与 `Simulator.SubSystem.Default.listTRS`（`src/Framework/MeshData.cxx:30`）均存在 ✓
- 关键算例文件均存在：`cyl_Pg_M15_FVM_1st2nd.CFcase`、`cyl_Pg_M15_FVM_1st2nd_MeFiAlgo.CFcase`、`doubleEllipseNS_PG.CFcase`、`deNEQ_CRD.CFcase` ✓

### C.6 第三轮核对（第 7、10、11、12 章）— 算例库、后处理、二次开发、附录

60. **7.1.2 总数（重要）**："全库约 1200 个 CFcase" → **实测 1019**（`find plugins -name "*.CFcase"`），并补入 23 个插件的单插件分布表。
61. **7.3.3 FireII 路径（重要）**：两组算例在 **`plugins/NEQ/testcases/TCNEQ/FireII/`**（3 个 CFcase：`fire2_1643s_TCNEQ/_CNEQ/_CNEQ_M++`）与 **`.../TCNEQ/FireII_air11/`**（2 个：`fire2.CFcase`、`fire2_Plato.CFcase`），**不在 `NEQ/testcases/` 顶层**。旧版路径检索会失败。
62. **7.3.4 DoubleCone（重要）**：算例在 **`plugins/NEQ/testcases/TCNEQ/DoubleCone/`**，其下有 `Run42_N2/`（2 个 CFcase）与 `Run35_N2/` 两组；另有**同名但完全气体版**的 `plugins/NavierStokes/testcases/DoubleCone/`，须按插件前缀区分。
63. **7.6.1 ICP（重要）**：① `TorchNEQ/` **不在 `Plasmatron/` 内**，是其同级目录 `plugins/ICP/testcases/TorchNEQ/`（17 个 CFcase）；② `ICP_EQProbe_` 分步法链实测只有 **Step1/2/4/5 四个目录，无 `Step3`**，"Step1…Step5 全流程 5 步法"表述已更正；③ 补 Plasmatron 六个子目录的实测计数（Torch 2、TorchStep1 4、TorchStep2 3、Chamber 7、AirTorch 1、Ablacat 2 = 19）。
64. **7.6.2 ArcJet**：`.inter` 实测 **3** 个（旧版 2），`.gz` 与 `.sh` 各 **1** 个；`testcases/` 下为 `ArcJet/` + `ScalingTest/` 两目录。
65. **7.7.2 共轭传热（重要）**：`plugins/SubSystemCoupler/testcases/` **只有一个 `FSI/` 目录**，CHT 算例与 FSI 同在其中（合计即 35 个）；补路径说明。
66. **7.4.3 MHD**：补漏列的 `Cylinder/`、`MeshFittingMHD/` 两目录（`plugins/MHD/testcases/` 共 18 个子目录）。
67. **7.2.1 Burgers**：标注同目录共 **7** 个 CFcase（1 FVM + 6 FluctSplit）。
68. **7.2.2/7.2.3/7.2.4/7.3.1/7.3.2/7.5.1/7.5.2/7.7.1（大量细节经复核无误）**：`burgersFVM`（`Prim`/`Roe`/`LinearLS2D.limitRes=-14.`/`BarthJesp2D`/`FwdEuler CFL=0.5`/`Residual=-5.00048764`）、`twoPlatesFEM`（`Heat3D`/`cube.CFmesh`/`builderName=FiniteElement`/`polyTypeName=Lagrange`/`Heat3DSourceTDep`/`IndepDef=2000*(y)`/`JacobianStrategy=Numerical`/`ResidualStrategy=StdElementComputer`/`IntegratorOrder=P1`/PETSC PCASM/KSPGMRES/RCM/1e-10/MaxIter=2000/`Residual=4.63803`）、`slab2d`（`convertFrom=Gambit2CFmesh`/`Puvt`/`Cons`/`Roe`/`Constant`/`numberOfRays=10`/`Residual=0.137957`）、`cylinderNS2DFR`（`refValues=1.0 0.1774823934930 … 2.51575`/`FixedKinematicViscosity`/`KinVisc=0.00443706`/`LaxFriedrichsFlux`/GaussLegendre/`VCJH.CFactor=9.5e-4`）、SA 平板（`NavierStokes2DSA`/`refValues=9300. 121.151 … 298.15 0.000002`/`machInf=0.1`/`CFL 200→2000`/`Residual=-5.5743685`）、GReKO 18 个、FSI 35 个、COCONUT（746 xz/28 CFcase/18 dat/9 inter/3 py）——**逐项与源文件一致**。
69. **10.1.1 TecplotWriter**：**不存在 `TecplotWriter/lib/` 子目录**；C 库接口（`TECXXX.h`、`TecplotWriterAPI.hh`、`preutil.c`）在插件根目录。已更正。
70. **10.1.4 `WriteSol`/`outputVar`/`updateVar` 语义（确认）**：两个 Writer 各自的选项体系——`TecplotWriter`：`outputVar`（`WriteTecplot`）、`WriteSol`、`FileFormat`、`SurfaceOnly`、`OnlyNodal`、`NodalOutputVar`、`AppendAuxData`、`MaxBuffSize`、`NbWriters(PerNode)`、`WithEquations`、`CoordinatesOnly`；`ParaViewWriter`：**`updateVar`**（非 `outputVar`）、`WriteSol`、`FileFormat`、`SurfaceOnly`、`VectorAsComponents`、`printExtraValues`。高阶输出命令名 `WriteSolutionHighOrder` **两插件都有** ✓（手册正文 4.10.4/4.18 的 `ParaView/Tecplot.WriteSol = WriteSolutionHighOrder` 表述经实测成立）。
71. **10.2 数据提取（确认）**：`src/Framework/DataHandleOutput.cxx:27` 的 **`CCSocketNames`** 选项存在，且 `plugins/LESDataProcessing/ComputeTurbulenceFunctions.hh:30` 的用法注释与手册 `Tecplot.Data.DataHandleOutput.CCSocketNames = qrad` 完全一致；`LESDataProcessing` Provider 实测为 `TimeAveraging`、`Qcriterion2D/3D`、`Vorticity2D/3D`、`SGSViscosity`、`VelocityGradients2D/3D`、`ComputeTurbulenceFunctions`、`GradientComputerFVMCC`；`AeroCoef` 实测含 `AeroForcesFVMCC`、`AeroForcesFR`、`NavierStokesSkinFrictionHeatFluxCC(3D/NEQ3D)`、`NavierStokesBLExtractionCC`、`Extract2DSectionCC` 等。
72. **6.2.12 AeroCoef 多库结构（确认）**：`plugins/AeroCoef/CMakeLists.txt` 注册 **8 个库**——`AeroCoef`、`AeroCoefFS`、`AeroCoefFVM`、`AeroCoefFVMNEQ`、`DataProcessingHeat`、`AeroCoefFR`、`AeroCoefSpectralFD`、`AeroCoefDG`，故 `Modules.Libs` 中写 `libAeroCoefFVM libAeroCoefFVMNEQ` 是正确的。
73. **11.1 工具目录（确认）**：`tools/` 下 `apply_all_fixes.sh`（根目录）✓、`fix_compile_issues.sh`、`fix_exception_specs.sh`；`tools/scripts/`（`addgplv3header.sh`、`init_testcases.sh`、`install-coolfluid-deps.pl`、`install.sh`、`mesh_IBM.sh`、`run.sh`、`Python/`、`deprecated/`）✓；`tools/style/`（仅 `vim/`）✓；`tools/templates/`（`ci/`、`cxx/`、`hh/`）✓；`tools/dev/`（9 个脚本）✓；`tools/tecplot/`（`.mcr`/`.eqn` + `convergence-monitoring.py`、`convergenceplot.sh`）✓。
74. **11.6.8 装载链路（正文原已正确）**：第 11 章正文写的是"`Simulator.Modules.Libs` → `LibLoader`（dlopen/LoadLibrary）→ 静态 Provider 自注册"，**无误**；错误在大纲 2.7.1/11.3.2 的 `LoadLib()`/`registerPlugins()` 表述，均已改为实测链路（`ModuleLoader.cxx:78` 剥 `lib` 前缀 → `PosixDlopenLibLoader.cxx:46,78` `dlopen(...,RTLD_LAZY|RTLD_GLOBAL)` **无符号查找** → 静态自注册）。
75. **11.3.1 `CF_ADD_PLUGIN_LIBRARY`（确认）**：定义于 `cmake/macros/CFAddPluginLibrary.cmake:4`，仅是 `CF_ADD_LIBRARY(${LIBNAME})` 的薄封装；`cmake/macros/` 另有 `CFAddTest.cmake`、`CFAddTestCase.cmake`、`CFAddLibrary.cmake`、`CFAddKernelLibrary.cmake`、`CFAddPluginApp.cmake`、`CFAddCompilationFlags.cmake` ✓。
76. **11.1.3 基础类型（确认）**：`CFuint`/`CFint`/`CFreal` 定义于 **`src/Common/COOLFluiD.hh:53-64`**（按 `CF_ENABLE_LONG/LLONG` 分支）；`cf_assert`/`cf_always_assert` 于 `src/Common/CFAssert.hh:68-83`；`CF_ENABLE_EXPLICIT_TEMPLATES`（`DefineGlobalOptions.cmake:68`）→ `CF_HAVE_CXX_EXPLICIT_TEMPLATES`（`DefineBuildRules.cmake:123`）✓。
77. **12.6 许可证（确认）**：`LICENSE` 为 GNU LGPL v3；`doc/gpl.txt`、`doc/lgpl.txt` 均存在 ✓。
78. **0.4 / 12.3.2 `doc/Manuals/`（确认并补全）**：实测 21 项，手册所列全部存在（`COOLFluiD_FVM.pdf/.tex`、`COOLFluiD_FVM_MHD/ICP/ATD.pdf/.tex`、`COOLFLuiD_Manual.pdf`、`FluxReconstructionManual.pdf/.tex`、`COOLFluiD_RDS_UnsteadyNavierStokes.tex`、`COCONUT_user_manual.pdf`、`geom_torch.pdf`），另含 `torch_SL_nc.pdf`、`torch_T_initial.pdf`、`torch_T_nc.pdf`、`Acce.png`、`mesh_torch_3.png` 及 2 个样例 CFcase（`convertGmes2CFmesh.CFcase`、`linearadv_LDA.CFcase`）。

### C.7 第三轮补核（第 7/10/11 章正文抽查 + 内核目录计数终核）

79. **11.3.1 物理模型注册示例（重要）**：旧版写 `ObjectProvider<BurgersPhysicalModel, PhysicalModelImpl, BurgersModule, 1> ("BurgersPhysicalModel")`，**两处与实测不符**——① 物理模型类按维度模板化，应为 `BurgersPhysicalModel<DIM_2D>`（`plugins/Burgers/BurgersPhysicalModel.cxx:25`）；② **注册名是 `"Burgers2D"`**（`burgers2DProvider("Burgers2D")`，:30），CFcase 应写 `PhysicalModelType = Burgers2D`。照旧示例抄会注册成无人引用的名字、CFcase 又找不到它。已改为带 `文件:行号` 的实测代码块。
80. **Provider 类体系（确认）**：`Environment::ObjectProvider<CONCRETE,BASE,MODULE,NBARGS>`（`src/Environment/ObjectProvider.hh`，**类模板**而非宏）、`Framework::MethodStrategyProvider<STRATEGY,DATA,MODULE>`（`src/Framework/MethodStrategyProvider.hh:30`）、`cmake/macros/CFAddPluginLibrary.cmake:4` 的 `CF_ADD_PLUGIN_LIBRARY`（仅封装 `CF_ADD_LIBRARY`）——第 11 章正文三者均正确。
81. **`src/` 目录计数终核（全部与手册一致）**：Common **188**、Config **46**、Environment **45**、Framework **567**、MathTools **66**、ShapeFunctions **202**、logcpp **65**、UnitTests **6**（含 `CMakeLists.txt` + `MathTools/` 子目录 + `test-tools-cfmesh-compare.cxx`）、合计 **1186** ✓。
82. **第 10 章输出/合并/派生量（逐项确认）**：`tecplot_merge` 的参数个数为 **3 或 6**（`TecplotMerge.cxx:21`：`(argc != 3) && (argc != 6)` 即报错）、`coef_merge <inFile> <nbFiles>`（`CoefMerge.cxx:44-46`）、`TecplotMergeKopacek` 亦为命令行工具；`CGNSWriter` 选项 `outputVar`/`FileFormat`/`CellCenterSolution`/`VertexSolution`/`WriteSol` 与高阶命令 `CGNSHighOrderWriter`/`ParCGNSHighOrderWriter` ✓；`AeroForcesFVMCC` 选项含 `Alpha`/`Beta`/`OutputFileAero`/`OutputFile`/`OutputFileConv`/`OutputFileWall`/`ConvCL`/`ConvCD`/`ConvCM`/`CheckCL`/`CheckCD`/`CheckCM`/`NbIters`/`MaxIter`/`Aref`/`Lref`/`RefArea`/`RefLength2D`/`PInf`/`IsViscous`/`ProjSurf` ✓。
83. **第 10 章 `DataHandleOutput` 的定性（确认且更精确）**：`DataHandleOutput`（`src/Framework/DataHandleOutput.cxx`）**不是**可独立挂载的 `DataProcessing` 命令，但其 `CCSocketNames`（:27）选项**可在 Writer 命名空间下配置**——`plugins/LESDataProcessing/ComputeTurbulenceFunctions.hh:30` 的用法注释即为 `Simulator.SubSystem.Tecplot.Data.DataHandleOutput.CCSocketNames = Qcriterion Vorticity SGSViscosity`，与第 7 章 `qrad` 的用法一致。10.2.3 的定性正确，本条补充"可在 Writer 命名空间下配置"这一层。
84. **第 7 章细节复核总结论**：除第 60–67 条所列 8 处路径/计数/名目修正外，抽到的全部具体配置——`burgersFVM`、`twoPlatesFEM`、`slab2d`、`cylinderNS2DFR`、SA 平板、GReKO/GammaAlpha、ICP Plasmatron 六子目录、ArcJet、FSI/CHT 35 例、COCONUT 数据构成——**键名、取值、`### Residual` 数值、模块列表均与源文件逐字一致**，算例库章节可信度高。

### C.8 第四轮全量复核（交叉引用 / 术语 / 量纲 / 数值一致性）

本轮按"数学物理模型、算法原理、数值一致性、术语规范、单位量纲"五项对全部 14 章做系统复核。修正 9 处：

85. **第 5 章基名/文件计数（重要，5 处）**：`src/Common/` 基名 **93→128**（实测去重基名，`find` 复核）、`src/Config/` **27→28**、`src/MathTools/` **36→42**、`src/Framework/` 文件 **543→542**（.hh+.cxx 实测）；`5.8.10 RadiativeTransfer` **63→61**。并在 5.1 开头补"计数口径说明"（文件=`.hh+.cxx`，基名=去重文件名），避免读者与大纲的全口径计数（188/46/45/567/66/202）混淆。第 5 章开头"代码量基线"一行同步更正为：6 域 **1054 源文件 / 654 基名**（旧"约 610 个基名"及父级括号内数字与实测均不符）。
86. **第 3 章 3.7.1 `refValues` 示例张冠李戴（重要）**：旧版写"如 Fire II：`refValues = 180000. 2500. 300. 2500.`"。实测该组值出自 **`plugins/NavierStokes/testcases/LongShotProbe/bluntbody-start.CFcase:24`**（行内注释 `#p u v T`）；**FireII 的 `refValues` 实为 NEQ 多值形式** `1e-12 1e-6 1e-6 0.00059826 1e-6 0.00018174 1e-6 1e-6 1e-6 1e-6 1e-6 10480. 10480. 276. 276.`（15 个量，`fire2_1643s_TCNEQ.CFcase` 实测）。已改正并互注出处。
87. **第 9 章 9.2.1 "元组"语法类别系虚构（重要）**：旧表列"元组 `(p,T,vx,vy)`（括号+逗号）"。实测：**代码与全部 CFcase 均无括号逗号向量语法**（`src/Config/ConfigFileReader.cxx` 无括号解析），`refValues` 是空格分隔的 `vector<CFreal>`；且 2D 顺序为 **`(p,u,v,T)`** 而非 `(p,T,vx,vy)`。已删除该行并改 9.3.5 示例为 `refValues = 1.0 1.0 1.0 2.5`。
88. **第 4 章 4.7.4 CFL 表达式（重要）**：旧版给出的简化式 `if(i<600,0.7,min(1e6,cfl*1.05))` 与 `cyl_Pg_M15_FVM_1st2nd.CFcase` 不符，已替换为该算例**逐字原文**（嵌套 `if(i<1400,1.2,…)`、末项 `min(1000.,cfl*1.02^2)`），并注明旧版为示意。
89. **第 1 章全称出处（精确化）**：本仓库 `README.md` 未逐字写出全称，仅描述为 "The object-oriented HPC platform for CFD, plasma and multi-physics simulations"（`README.md` 第 2 行附近）；1.1.2 已加"以官网为准"的准确性说明，大纲附 B-1 同步更正"官网/README 一致"→"官网一致"。
90. **术语统一（新增约定）**：`幽灵单元`（仅大纲 2.5.1 一处）→ **虚拟单元（ghost cell）**；`梯度重建`（大纲 4.2.2）→ **梯度重构**；并在第 3 章开头新增"**全文术语约定**"表（虚拟态/虚拟单元、重构/重建、通量格式/通量分裂器、滑移/镜面、解点/通量点、残差分布法 fluctuation、当地时间步、谱半径），明确"同一概念同一用词、不同语境允许例外"。
91. **量纲与数值自洽复核（全部通过，记录在案）**：① `νA²/V` 与 `λmax·A` 同量纲（m³/s）✓；② 4.19.4 内存估算 `10⁶×6×25×8B = 1.2GB` ✓；③ 邻居非零块数 2D 三角=4、3D 四面体=5（面邻居+自身）✓；④ FR/SD/DG 自由度 `N_c(P+1)^d`、显式步数 `∝1/P²` ⇒ 总代价 `P^{d+2}` ✓；⑤ 3.1.2 单位表（SI）与 Sutherland/Pr/Re/Kn 无量纲数 ✓；⑥ `tecplot_merge` 参数 3 或 6 ✓。
92. **交叉引用全量比对（全部有效）**：第 3 章引用的 4.4/4.9/4.15.3/4.18/3.1.6/3.6.3/6.2.8/7.2/7.3/7.5.2/9.3.9/10.1.1/11.4/12.5 节号，第 4 章引用的 3.1.4/3.6.5/3.7/3.8/4.3.6/4.7.3/4.7.4/4.7.5/4.9.2/4.12/4.14/4.15.3/4.17/4.19.3/6.2.5/6.2.10/7.3.3/9.6/12.5/2.3.1 节号——逐一与实际标题比对全部存在且语义对应；`第 11.4 节（新增边界条件教程）` 与第 11 章正文 11.4 标题一致 ✓。
93. **概念核对（全部通过）**：变量集 `Char`/`Symm`/`Roe`/`Prim`/`Cons`/`Puvt`/`Rhovt` 均实测存在（`plugins/NavierStokes/Euler2DChar.cxx` 等）；6.1 插件分类表所列 **118 个插件目录名全部存在**（`ls plugins/` 实测）；版本号 `2013.9`（`CMakeLists.txt:116-118`）、内核 `2.5.0`（:120-123）、`CMAKE_MINIMUM_REQUIRED 2.8.3`（:20）、Boost `1_42` 分支（:328）均正确。

### C.9 第六轮核对记录（2026-08，第 0/2/6/8/9/12 章——快速上手、逐行走查、插件配置、字段表、FAQ、安装）

本轮按用户五项要求（数学物理模型、算法原理、数值一致性、术语规范、单位量纲），对前五轮未深核的章节做源码级核对。共修正 **9 处**：

94. **0.3.4 场景 C 时间推进方法（重要）**：旧版写"显式时间推进 `libForwardEuler`"。实测 `1_BrioWu.CFcase:146` 实际启用 **`ConvergenceMethod = BDF2`**（文件头部的 `FwdEuler` 与 `NewtonIterator` 均被注释，:122、:127）；`libForwardEuler` 虽在 `Modules.Libs` 中被加载但**未启用**。已改正并注明"加载≠启用"。
95. **6.2.4 多流体通量注册名（重要）**：旧版写 `AUSMPlusUpFluxMultiFluidMHD2D/3D`。实测注册名为 **`AUSMPlusUpMultiFluid2D/3D`**（+`ALE`）与 `LaxFriedFluxMultiFluid2D/3D`——**无 `Flux`、无 `MHD` 中缀**（`FiniteVolumeMultiFluidMHD/*.cxx` 实测，与 4.4.7 表一致）。
96. **6.2.5 辐射命令名（重要）**：旧版启用方式写 `DataProcessing1.Comds = ComputeRadiativeTransfer`。实测 `slab2d.CFcase` 的辐射命令是 **`RadiativeTransferMonteCarlo2DFVMCC`**。
97. **6.2.6 ICP `libRK2` 不存在（重要）**：旧版启用方式含 `libRK2`。实测 `RungeKutta2` 插件的库名是 **`libRungeKutta2`**（`CF_ADD_PLUGIN_LIBRARY(RungeKutta2)`），全库无 `libRK2` 用法；且 ICP 算例实际用 `libNewtonMethod`。已改写为 ICP 算例实测的模块清单。
98. **9.3.7 `Data.stencil` 取值错误（重要）**：旧版写 `Cell / Face / Ghost`。实测 `ComputeStencil` Provider 注册名为 **`Face` / `FaceVertex` / `FaceVertexPlusGhost` / `FaceBVertex` / `FaceEdge`**（`plugins/FiniteVolume/ComputeFace*Neighbors*.cxx`），**无 `Cell`/`Ghost`**。
99. **9.3.2 `SpaceResidualFile` 默认名（次要）**：旧版写默认 `space.plt`。实测 `SpaceResidualFile` 默认 **`spaceResidual.plt`**（`ConvergenceMethod.cxx:95`），键本身在 :45-46 注册。
100. **12.6 `--mpi` 命令行选项不存在（重要）**：旧版称"`mpirun -np N` 与 `--mpi` 不匹配"。实测 `coolfluid-solver` 的 11 个命令行参数**不含 `--mpi`**（`apps/Solver/coolfluid-solver.cxx`），全库也无处理代码；MPI 实现由编译期决定。已改写为"进程数与网格剖分一致性"。
101. **2.4.3 `Tecplot.Data.updateVar` 未消费键（重要）**：`doubleEllipseNS_PG.CFcase` 用 `Tecplot.Data.updateVar = Puvt`，但 `TecplotWriter` 的配置键实为 **`outputVar`**（`TecWriterData.cxx:39`；`updateVar` 只在 `ParaViewWriter` 注册，`ParaWriterData.cxx:40`），因此该键在运行期是**未消费键**（默认仅告警，见 12.3.2）。已加注：欲显式指定 Tecplot 输出变量集应写 `Tecplot.Data.outputVar = Puvt`（第 10.1.4 节）。
102. **2.4.3 `de.inter` 文件缺失（重要）**：`doubleEllipseNS_PG.CFcase` 的 `InteractiveParamReader.FileName = de.inter`，但仓库中 `plugins/NavierStokes/testcases/DoubleEllipse/` 下**无 `de.inter`**（`find plugins -name "de.inter"` 无结果）。已加注运行需自行提供该文件。
103. **8.1.3 依赖清单数量与成员（重要）**：旧版写"`install-coolfluid-deps.pl` 共 36 个定义项"。实测脚本 `%deps` 哈希定义 **33 个**，且清单成员有出入——脚本实际为 `coreutils make wget binutils m4 tar gcc4 gcc3 autoconf automake libtool openssl blas clapack lapack log4cpp zlib cppunit dateshift curl libfaketime mpich mpich2 parmetis hdf5 subversion trilinos petsc gmsh ccache distcc cgnslib cgnstools`（含 `libfaketime`；**无 `boost`/`openmpi`/`mvapich2`/`cmake`**，`cmake` 定义被注释）。

**复核确认无误清单（供信任度参考）**：

- 第 0 章：场景 A（`cyl_Pg_M15_FVM_1st2nd`：9 插件清单、`RoeSA`、`Venktn2D`、`valueNorm=-9.0`、`ResultsDir=RESULTS_Cylinder_1st2nd`、`Residual=-9.1615`、`Restart=true`）、场景 B（FireII 的 `libNEQ/libFiniteVolumeNEQ/libMutation2OLD/libMutation2OLDI/libAeroCoefFVM/libAeroCoefFVMNEQ` 及 CNEQ/M++ 变体存在）、场景 D（`accpulse2d-sfdm` 用 **`RKLS`**、`convertFrom=THOR2CFmesh`/`SolutionOrder=P0`/`Discontinuous=true`；`cylinderEuler2DFR-impl` 用 `BwdEuler`+PETSc）、场景 E（`EmptySpaceMethod` 16 文件、`EmptySolver/StdSetup/StdSolve/StdUnSetup/EmptyStrategy/EmptyMeshDataBuilder`）——逐项与源码一致。0.3.1 布尔参数空格传值（`coolfluid-solver.cxx:63-66`）、`--help=1` 报 `BadMatchException` ✓。
- 第 6 章：6.2.2 `nbVibEnergyEqs`/`includeElectronicEnergy` 归属、6.2.3 MHD 模型注册名、6.2.7 `SpaceMethod=FluctuationSplit` 注册名（`FluctSplit` 插件实测）+ `doubleEllipseRDS_NS_Pvt_adim.CFcase` 存在、6.2.8 `ConvSolveCom=ConvRHSJacobAna`/`SpaceRHSJacobCom`（`FluxReconstructionMethod` 实测）、6.2.10 PETSc 键、6.2.11 `LoopMaestro`（`LMaestro.cxx:33`）——全部一致。
- 第 9 章：9.3.1 CFEnv 16 键全存在、9.3.3 全部 8 个 StopCondition 注册名（`NormCondition/AbsoluteNormAndMaxIter/RelativeNormAndMaxIter/MaxNumberStepsCondition/MaxTimeNumberStepsCondition/NormAndMaxSubIter/RelativeNormAndMaxSubIter/AeroCoef`）、9.3.4 Writer Data 键（`outputVar`/`updateVar` 归属）——全部一致。
- 第 12 章：异常格式（`Exception.cxx:43-53`）、`Unused User Configuration Arguments` + `ConfigOptionException`（`Simulator.cxx:288-293`）、`CFEnv` 键默认值、`CFWarnOrphanFiles`/`OrphanFiles.txt`（`DefineMacros.cmake:35`、`CMakeLists.txt:626`）——全部一致。
- 第 2 章 2.4.3：`FluxSplitter=Centred`/`PolyRec=Constant`/`builderName=FVMCC`/`CFL.Value=0.3`/`listTRS=InnerFaces NoSlipWall SuperInlet SuperOutlet`；2.4.4 `NoSlipWallIsothermalNSPvtFVMCC` 注册于 `plugins/FiniteVolumeNavierStokes/NoSlipWallIsothermalNSPvt.cxx`——全部一致。
- 第 8 章：`cmake/Find*.cmake` 恰 **13 个**（清单与手册一致）、8.2.1 全部 12 个 `CF_ENABLE_*` 默认 ON（`DefineGlobalOptions.cmake`）、8.8 命令行默认 `log=600`（`Priority.hh:80`）/`residual=1.79769e+308`/`tolerance=3`/`conf=coolfluid-solver.xml`（`coolfluid-solver.cxx:82-86`）、`CellTriagLagrangeP1LagrangeP1`（`LagrangeCellTriags.cxx:43`）——全部一致。

### C.10 第七轮复核记录（2026-09，全册通读 + 源码抽查）

本轮对第 0–12 章全文通读，并对未在前六轮深核的"实测"声明做源码级抽查（文件计数、注册名、源码行号、算例配置原文、工具参数）。共发现并**已直接修正正文**的与源码不符项 4 处、口径澄清 2 处：

104. **8.1.3 依赖清单（重要，纠正上一轮的"更正"）**：`install-coolfluid-deps.pl` 的哈希名为 **`my %packages`**（非 `%deps`）；**未注释（激活）条目共 38 个**（非 33/36）；且 **`boost`(1_88_0)、`openmpi`(4.1.6)、`cmake`(3.17.0)、`mvapich2` 均为激活条目**（被注释的只是各旧版本行），清单另含 `google-perftools`。第 103 条修正记录本身有误，正文 8.1.3 与 8.3.3 已按实测重写。
105. **7.3.4 DoubleCone 路径（重要）**：`plugins/NEQ/testcases/TCNEQ/DoubleCone/` 下**仅有 `Run42_N2/`**（2 个 CFcase）；`Run35_N2` 实际位于**完全气体插件侧** `plugins/NavierStokes/testcases/DoubleCone/Run35_N2`。第 62 条修正记录中"其下有 Run42_N2 与 Run35_N2 两组"的表述有误，正文已改。
106. **6.2.1 启用方式出处（重要）**：旧版模块清单含 `libRungeKutta2 libForwardEuler` 并标注"实测，Cylinder 系算例"——实测 Cylinder 目录下**无任何算例加载 `libRungeKutta2`**（该库用于 AccPulse `-sfvm` 族与 FlatPlate RDS 算例）。正文已替换为 `cyl_Pg_M15_FVM_1st2nd.CFcase` 的真实 9 库清单（与 0.3.2 一致）并加更正注。
107. **HLLE 行号微漂**：`HLLE2D` 注册于 `FiniteVolumeNavierStokes/HLLEFlux.cxx:35`（旧记 :29），4.4.7 表与 4.18.3 表已更正。
108. **口径澄清（5.8.10 vs 5.8.16）**：RadiativeTransfer 源码 61（`.hh+.cxx`）与 63（含 2 个 `.cu`：`ParadeRadiatorCUDA.cu`、`RadiativeTransferFVDOMCUDA.cu`）两数各自成立，5.8.10 已补换算说明；`FluctSplit` 900 = 899 + 1 个 `.c/.cu` 同理成立。
109. **大纲滞后数据同步**：`plugins/` 全部文件实测 **9747**（本大纲 1.3.4 写 9746，正文第 1/2 章的 9747 无误）；`plugins/AeroCoef/CMakeLists.txt` 实际注册 **10 个库**（`AeroCoef/AeroCoefFS/AeroCoefFVM/AeroCoefFVMNEQ/DataProcessingHeat/AeroCoefFR/AeroCoefSpectralFD/AeroCoefDG/AeroCoefSpectralFV/AeroCoefFRNEQ`），第 72 条修正记录的"8 个"漏 `AeroCoefSpectralFV` 与 `AeroCoefFRNEQ`。

**本轮复核确认无误的关键声明（供信任度参考）**：文件计数（1019 CFcase、135 插件目录、`.hh` 3977/`.cxx` 3347、src 六模块 175/45/40/542/51/201、Mutation2.0I data 191/26 `.mix`/27 `.ceq`、COCONUT 746 `.xz`、Plasmatron 六子目录 2/4/3/7/1/2、TorchNEQ 17、FireII_air11 2、Cylinder 68、AccPulse 30、Naca0012 41、Wedge 23、DoubleEllipse 13、TwoPlates 18、SA FlatPlate 15）；源码行号（`FVMCC_ComputeRHS.cxx:139/:455`（右单元 `+=` 落于 :497）、`RoeFlux.cxx:120/:199`、`BDF2.cxx:101`、`LDASchemeSys.cxx:67`、`FluxReconstructionSolver.cxx:466`、`Euler2DVarSet.cxx:93/:128/:173-196`、`FVMCC_PolyRec.cxx:58/:145`、`NoSlipWallIsothermalNS2D.cxx:100`、`MirrorEuler2D.cxx:80-81`、`TecWriterData.cxx:39`、`ParaWriterData.cxx:40`、`Venktn2D.cxx:58`、`PluginsRegister.hh` 3097 行）；注册名（`FluctuationSplit`、`LoopMaestro`/`SimpleMaestro`（`LMaestro.cxx:33`/`SMaestro.cxx:33`）、`MultiFluidMHD2DRhoiViTi`、`AUSMPlusUpMultiFluid2D`、`RoeVinokurTCNEQ2D`、`Fast`、`Linearized`、`RoeSAGhost`、`AUSMPlusUpIcp_cp`、`AUSMPlusUpTurb3DLTE`、`Venktn3DStrictT3F`、8 个 StopCondition、`NoSlipWallIsothermNS2DFVMCC` 拼写遗留）；MHD 方程数（8/9/9/11，文件:行逐一命中）；算例配置原文（`cyl_Pg_M15_FVM_1st2nd` 全部细节、BrioWu `BDF2` 于 :146 且 FwdEuler/NewtonIterator 被注释、`fire2_1643s_TCNEQ` 的 `refValues`/`nbVibEnergyEqs=1`/`Mutation2OLD.includeElectronicEnergy=true`/`UpdateVar=RhoivtTv`、`doubleEllipseNS_PG` 的 `de.inter` 缺失与 `Tecplot.Data.updateVar` 未消费键、`accpulse2d-sfdm` 的 `RKLS`/`THOR2CFmesh`/`P0`/`Discontinuous`、`burgersFVM` 缺 `libShapeFunctions`）；机制（`### IncludeCase` 于 `NestedConfigFileReader.cxx:86`、AppOptions 11 参数及默认值、`tecplot_merge` argc 3/6、`coef_merge` 两参数、`.CFmesh` 头键序列、k-ω/log-ω 与 SST 实现细节、SA 源项接口名）。

### C.11 第八轮复核记录（2026-09，代码示例可运行性 + 默认值/结构一致性终核）

本轮聚焦**教程与手册示例的"照着抄就能跑"**：对 0.3.x 场景命令、8.3.6 cmake 变量、9.4.3 结构网格转换、第 11 章二次开发教程代码做可运行性核对，并对第 4/6 章声称的参数默认值与第 0/1/2 章结构一致性做源码级复核。共发现并**已直接修正正文**的与源码不符项 4 处、口径澄清 1 处：

110. **9.4.3 结构网格转换注册名（重要）**：旧版示例给 `ConvertBlockMesh / ConvertQuadMesh / ConvertGridProMesh` 作为启用名——**实测三个转换器注册名是 `Block`/`Quad`/`GridPro`**（`plugins/ConvertStructMesh/ConvertBlockMesh.cxx:37` `convertBlockMeshProv("Block")`、`ConvertQuadMesh.cxx:34` `convertQuadMeshProv("Quad")`、`ConvertGridProMesh.cxx:37` `convertGridProMeshProv("GridPro")`），类名 ≠ 注册名。照手册旧示例运行会报 `NoSuchValueException`（找不到 Provider）。正文已改为实测注册名并加更正注。
111. **11.4.1 `usesTRS()` 归位与默认值双重错误（重要）**：该成员**不在 `NumericalCommand`**，而定义于模板 `MethodCommand<DATA>`（`src/Framework/MethodCommand.hh:94`），且**默认返回 `false`**——旧文把其列入 `NumericalCommand` 清单并写"默认 true：需要 applyTRS"。正文已移出清单并加注：BC 命令必须自行重写 `virtual bool usesTRS() const { return true; }`，否则方法不会注入 TRS 列表。另 `MethodCommand.hh:52-62` 实测签名（`DATA& getMethodData()`、`void setMethodData(const Common::SharedPtr<DATA>&)`）已同步。
112. **11.4.2/11.4.3 教程骨架 `override` 与项目 C++98 风格不符（重要）**：教程示例 `void setup() override;` 无法在项目原始编译标准下编译——**源码全库 0 处 `override`**（C++98/03 风格，模板返回类型均写作 `> >` 带空格，如 `Method.hh`）。骨架已改回 `virtual` 并加注：若按 8.3.5 节迁移 C++17 虽可编译，仍建议与既有代码风格一致便于对照。
113. **11.5.1 `Method` 接口签名精确化（次要）**：`getCommandList` 实际签名 `std::vector< Common::SafePtr<NumericalCommand> > getCommandList() const`（`Method.hh:86`，注意 `> >`）；`getStrategyList` 元素类型为 `Common::SafePtr<Framework::NumericalStrategy>`（:93）。正文示例已按实测改写。
114. **口径澄清（8.3.6 cmake 变量，复核通过无改动）**：本轮开列核对的变量（含 `CF_INSTALL_SUFFIX`/`CF_CMAKE_INSTALL_PREFIX` 等）逐一存在于顶层 `CMakeLists.txt` 与 `cmake/`——正文 8.3.6 命令可原样执行。

**默认值抽查（全部复核通过，正文无需改动）**：① 第 4 章 `Venktn2D.cxx:58` `_coeffEps = 1.0`、`FVMCC_PolyRec.cxx:58` `_limitIter = 1000000000`、`BarthJesp.cxx:47-49` `m_useFullStencil = false` 且正文正确限定为"仅 `BarthJesp3D`"（源码确实 `if (getName() == "BarthJesp3D")`）；② 第 6 章 `PluginsRegister.hh:581` 定义 `registerAll`、`apps/Solver/coolfluid-solver.cxx:165` 处唯一调用、`:304` 默认 `maestro_str = "SimpleMaestro"`——行号与默认值均命中。

**结构一致性抽查（复核通过）**：正文对第 0/1/2 章的一切节号引用（0.3.7、0.4、2.1.2、2.2、2.3、2.7.2 等）逐一与真实标题比对存在且语义对应；11.4 新增教程引用的 8.3.5 节（现代工具链 C++17 迁移，实测清单）确为 `第8章_安装与编译指南.md:186` 的真实小节。文件计数口径沿用 C.8 第 85 条约定。
