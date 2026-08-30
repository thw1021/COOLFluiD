# COOLFluiD 高焓高超声速算例全面系统评估报告

> 评估对象：`/home/tang/packages/COOLFluiD` 工作区（master 分支）
> 评估方式：逐一读取全部相关 `*.CFcase` 配置文件与配套网格文件的真实内容，并核实本机构建产物（`build/optim/dso`、`install/bin`）
> 日期：2026-08-28

---

## 1. 总体结论

仓库内高焓/高超声速算例集中分布在 **3 个插件** 的 testcases 目录，共 **43 个 `.CFcase` 文件**：

| 插件 | 算例数 | 物理定位 |
|---|---|---|
| `plugins/NEQ/testcases` | 27 | 化学非平衡（CNEQ）/ 热化学非平衡（TCNEQ）高焓流动核心算例集 |
| `plugins/LTE/testcases/IXV` | 4 | 局部热力学/化学平衡（LTE）高超飞行器算例 |
| `plugins/ArcJet/testcases` | 15 | 电弧加热器（ArcJet）等离子体，LTE + 电磁 + 辐射耦合 |

另有 `plugins/Chemistry/testcases/TwoPlatesCH4`（CH4 燃烧，非高超声速）不纳入本报告。

**关键判断：**

1. **"高焓"谱系完整**：从 LTE 平衡气体（IXV）→ 单温度化学非平衡 CNEQ（Hornung、FireII-CNEQ、CateIXV、Mach38、Catalicity）→ 双温度热化学非平衡 TCNEQ（FireII-TCNEQ、DoubleCone、Prabhu、ICP2Cat、ShockTube）→ 多振动温度 + 电子温度（Nozzle1D MultiTvTe，含 95 组分碰撞-辐射模型）全覆盖。
2. **化学反应模型全部为 Park 系列**（park5 / park5T / parkN2 / parkair93 / parkair93cneq）+ Nompelis（nompelisN2，双锥）+ 1 个 CR 模型（Abba_At）；**仓库中没有 Dunn-Kang 模型算例**。
3. **热化学库 5 种**：Mutation 1.x（旧 F77）、Mutation2OLD（F77 v2.0）、Mutation2、Mutation++（M++）、PLATO。
4. **空间方法两大类**：单元中心有限体积 FVM（通量几乎全部为 AUSM+ 多组元版 `AUSMPlusMS`/`AUSMPlusUpMS`，Venkatakrishnan 限制器）与残差分布 RDS/FluctSplit（DoubleCone 的 CRD+Gnoffo 激波捕捉、Prabhu 的 CRD+SysNC）。
5. **可运行性**：输入文件（网格/重启解/交互文件）**齐全**的算例 17 个；缺网格或缺数据的 26 个。结合**本机构建仅编译了 Mutation++ 接口**（`libMutationppI.so`，旧版 Mutation/Mutation2OLD/PLATO 均未编译），**当前构建下真正开箱即跑的只有 7 个算例**（见 §4）。

---

## 2. 算例详细配置

### 2.1 Hornung 圆柱绕流（N2 高焓实验标模，9 个变体）

路径：`plugins/NEQ/testcases/TCNEQ/Hornung/`
物理背景：Hornung 高焓氮气圆柱实验，脱体弓形激波 + 粘性边界层 + 壁面热流标模。

| 项目 | 配置 |
|---|---|
| 维度 | 2D 平面（圆柱横截面绕流） |
| 气体 | 氮气 2 组分 N/N2（`nitrogen2` / M++ 的 `N2_neut`、`N2_TTv`） |
| 来流 | u∞=5590 m/s，T∞=1833 K（TCNEQ 版 Tv=1833 K），p∞≈2909 Pa，ρ∞≈5.15e-3 kg/m³（约 M≈6 高焓工况） |
| 空间方法 | CellCenterFVM，`AUSMPlusMS2D`（choiceA12=5），二阶 `LinearLS2D` + `Venktn2D` 限制器（limitIter=3500）；RoeTCNEQ2DSA（含 carbuncle 修正）仅以注释备选 |
| 求解器 | 隐式稳态：NewtonIterator + PETSc（PCASM/KSPGMRES/RCM，200 Krylov 空间，RelTol=1e-4），伪瞬态 CFL 爬坡至 100 |
| 边界条件 | 壁面：无滑移等温非催化壁 `NoSlipWallIsothermalNSrvtMultiFVMCC`，TWall=1000 K；入口 SuperInletFVMCC；出口 SuperOutletFVMCC；初始场含人工边界层 |
| 典型特征 | 弓形激波、边界层、壁面热流/摩阻后处理（`NavierStokesSkinFrictionHeatFluxCCNEQ`）、并行壁距计算 |
| 网格 | `jesus0_quad.neu` **已提供**（Gambit 在线转换，缩放 1000）；Euler 版用 `coarse.CFmesh`（800 四边形，已提供） |

9 个变体差异：

| 文件 | 模型 | 库/反应 | 可运行性 |
|---|---|---|---|
| `hornung_FVM_NS_CNEQ.CFcase` | CNEQ 单温度 | Mutation2OLD，parkN2 | 网格在；但本机未编译 Mutation2OLD |
| `hornung_FVM_NS_CNEQ_M++.CFcase` | CNEQ 单温度 | **Mutation++**，ChemNonEq1T | **可直接运行** |
| `hornung_FVM_NS_CNEQ_M++_Debug.CFcase` | CNEQ | MutationppDebug 接口 | **可直接运行** |
| `hornung_FVM_NS_CNEQ_Plato.CFcase` | CNEQ | PLATO 库 | 需 PLATO 数据库，不可直接跑 |
| `hornung_FVM_NS_TCNEQ.CFcase` | **TCNEQ 双温度**（1 振动温度方程，RhoivtTv） | Mutation2OLD，parkN2 | 本机缺库 |
| `hornung_FVM_NS_TCNEQ_M++.CFcase` | TCNEQ 双温度 | **Mutation++**，ChemNonEqTTv | **可直接运行** |
| `hornung_FVM_NS_TCNEQ_Plato.CFcase` | TCNEQ | PLATO | 不可直接跑 |
| `hornung_FVM_NS_CNEQ_euler_M++.CFcase` | **无粘 Euler CNEQ**（滑移壁 MirrorVelocity） | Mutation++ | **可直接运行**（coarse.CFmesh） |
| `hornung_FVM_NS_CNEQ_M++_MeFiAlgo.CFcase` / `_Firas` | CNEQ + **网格自适应移动（r-型激波贴合 MeshFittingAlgorithm）** | Mutation++ | **可直接运行**（Firas 版用 HornungFirasStart/Restart.CFmesh，均提供） |

### 2.2 FIRE II 再入飞行试验（t=1643 s 弹道点，5 个变体）

路径：`plugins/NEQ/testcases/TCNEQ/FireII/` 与 `FireII_air11/`
物理背景：FIRE II 阿波罗类返回舱再入飞行试验，典型高焓验证标模。

| 项目 | 配置 |
|---|---|
| 维度 | 2D **轴对称**（isAxisymm + 轴对称源项） |
| 气体 | **air11**（11 组分电离空气：e⁻, N, O, N2, NO, O2, N2⁺, NO⁺, N⁺, O2⁺, O⁺） |
| 来流 | u∞=10480 m/s（约 Ma 31），T∞=Tv∞=276 K，ρ∞≈7.8e-4 kg/m³，p∞=62 Pa |
| 空间方法 | FVM，`AUSMPlusMS2D`，LinearLS2D + Venktn2D（经 `fire2.inter` 交互升二阶） |
| 求解器 | Newton + PETSc PCASM，伪稳态 CFL 交互，目标 Norm=-7 |
| 边界条件 | 壁面等温 **TWall=640 K 非催化**（前 1000 步绝热以助激波脱体）；Symmetry 镜像；SuperInlet/SuperOutlet |
| 典型特征 | 强弓形激波、激波层化学/振动非平衡、壁面热流后处理（每 10 步） |
| 网格 | `fire2_small80x.neu` **已提供**（Gambit 转换，缩放 1e6）；另附 TCNEQ 二阶收敛解 `final_1643_2nd.CFmesh`（10260 四边形）可重启 |

| 文件 | 模型 | 库/反应 |
|---|---|---|
| `fire2_1643s_CNEQ.CFcase` | CNEQ 单温度（14 变量） | Mutation2OLD，**parkair93cneq** |
| `fire2_1643s_CNEQ_M++.CFcase` | CNEQ | **Mutation++**，air11nasa9，ChemNonEq1T → **本机可直接运行** |
| `fire2_1643s_TCNEQ.CFcase` | **TCNEQ 双温度**（含电子能，15 变量） | Mutation2OLD，**parkair93** |
| `FireII_air11/fire2.CFcase` | TCNEQ 双温度 | Mutation2OLD，parkair93 |
| `FireII_air11/fire2_Plato.CFcase` | TCNEQ | PLATO（**路径硬编码失效**，不可跑） |

### 2.3 双锥 Run 42（NATO RTO AVT-136，激波-激波/激波-边界层干扰，2 个变体）

路径：`plugins/NEQ/testcases/TCNEQ/DoubleCone/Run42_N2/`
物理背景：双锥 N2 试验，type IV 激波-激波干扰、分离泡、再附热流峰值——高超声速干扰流动经典标模。

| 项目 | 配置 |
|---|---|
| 气体 | N/N2 2 组分，**TCNEQ 双温度** |
| 来流 | ρ_N2=1.468e-3 kg/m³，u∞=3849.3 m/s，T∞=268.7 K，**Tv∞=3160 K（来流本身热非平衡）**，约 Ma 11 |
| 边界条件 | 壁面等温 **TWall=294.7 K 非催化**；超声速入口/出口；对称面 |
| 反应模型 | **nompelisN2**（Nompelis N2 离解模型） |
| 典型特征 | 激波-激波干扰、激波/边界层干扰、分离与再附、壁面热流 |

| 文件 | 空间方法 | 库 | 网格 |
|---|---|---|---|
| `DConeN2_42_CRD_Weak.CFcase` | **RDS/FluctSplit：CRD 格式 + SysBCxMS 激波捕捉分裂器（Gnoffo 探测器）**，P1 连续有限元，弱壁面 BC | Mutation 1.x（旧 F77） | `DConeN2-P0-CRD_BX_2.CFmesh`（65280 三角形）**已提供** |
| `DConeN2_42_FVM.CFcase` | FVM + AUSMPlusMS2D 二阶 + Venktn2D，带 **MeshFittingAlgorithm 网格自适应（密度监控量）** | Mutation2OLD | `DConeN2_B.plt`（Tecplot 在线转换）**已提供** |

两者输入齐全，但均依赖旧版 Mutation 库，本机构建需补编译后方可运行。

### 2.4 CateIXV —— IXV 飞行器 45° 攻角、**双材料催化壁**（1 个）

路径：`plugins/NEQ/testcases/TCNEQ/CateIXV/IXV_CATE_M25_air5_CNEQ.CFcase`

- 维度：2D 轴对称（8 进程设计）
- 模型：**CNEQ 单温度，air5**（N, O, N2, NO, O2），Mutation2OLD，**park5T**
- 来流：**Ma 25**，u∞=7188 m/s，p∞=1.87 Pa，T∞=205.7 K
- 边界条件（本仓库催化壁最完整算例）：**分材料催化壁** `NoSlipWallIsothermalNSrvtCatFVMCC` —— wall 段 Γ_N,O=0.019，Cate1/Cate2 段 Γ_N,O=0.19；**辐射平衡壁温**（RadEquilibrium，发射率 0.8，TWall 初值 1000 K，UseStefanMaxwell）
- 求解：Newton+PETSc，CFL 爬坡 5→1000，AUSMPlusMS2D + 限制器（从重启文件恢复）
- 网格：`final12961.CFmesh`（33072 四边形，含收敛解 + limiter 状态）**已提供**
- 特征：激波 + 化学非平衡边界层 + **壁面催化复合 + 辐射平衡壁温**
- 可运行性：输入齐全；需 Mutation2OLD 库

### 2.5 LTE IXV —— 平衡气体 Mach 25（4 个变体）

路径：`plugins/LTE/testcases/IXV/`
与 §2.4 同一 IXV/CATE 几何、同一来流（Ma 25, 7188 m/s, 1.87 Pa, 205.73 K），但采用 **LTE 平衡气体模型**：变量 `PuvtLTE=[p,u,v,T]`，平衡组分由物性库内部求解，**air11**。

| 文件 | 方程 | 库 | 壁面 | 说明 |
|---|---|---|---|---|
| `ixvLTE.CFcase` | 2D **轴对称 Navier-Stokes** | Mutation2OLD | 等温 1000 K 非催化 | 含热流/摩阻后处理 |
| `ixvLTE_Mutation++.CFcase` | 同上 | **Mutation++** | 同上 | **本机可直接运行**（解压网格后） |
| `ixvLTE_Euler.CFcase` | 2D 无粘 Euler | Mutation2OLD | 滑移壁 | nbSteps=0，网格转换验证 |
| `ixvLTE_Euler_Mutation++.CFcase` | 同上 | **Mutation++** | 滑移壁 | 库对比变体 |

- 空间方法：FVM，`AUSMPlus2D`（choiceA12=1），一阶起步、经 `IXV.inter` 升二阶 + Venktn2D
- 网格：`CATE_v7_small.neu.gz` **已提供（需先 gunzip）**，Gambit 在线转换
- 特征：Mach 25 高超绕流、激波 + 边界层（NS 版）、壁面热流；无催化（LTE 平衡壁）

### 2.6 SphereCO2 Mach 38 —— 球体电离空气绕流（1 个）

路径：`plugins/NEQ/testcases/CNEQ/SphereCO2Mach28/Mach38_FVM_NS_CNEQ_M++_interpolate.CFcase`

- 维度：2D（轴对称布局球体绕流）
- 模型：**CNEQ 单温度（Mutation++ ChemNonEq1T）**，7 组分电离空气 `air7_sahadeo_reordered`（e⁻, N, O2, NO, O, NO⁺, N2）——注意：目录名/注释写 "CO2"，实际配置为空气 7 组分
- 来流：**Mach 38**，u∞=11125 m/s，T∞=206.5 K，p∞≈2 Pa
- 空间方法：FVM 二阶（LinearLS2D + Venktn2D），AUSMPlusMS2D
- 边界：球面等温 **TWall=2527 K**（辐射平衡壁温值）非催化，前 2000 步绝热启动；对称轴镜像；SuperInlet/SuperOutlet
- 求解：双子系统 —— 先用 Tecplot2CFmesh 把粗网格解 `OLD.plt` 插值到 `NEW.CFmesh`，再 Newton 重启 10 步
- 网格：`NEW.CFmesh`（6860 四边形）+ `OLD.plt` + `Mach38.inter` **全部提供**
- 特征：极端高焓（11 km/s）弓形激波、电离、化学非平衡
- 可运行性：输入齐全 + Mutation++ 已编译，但混合物 `air7_sahadeo_reordered` 数据需外部 Mutation++ 数据包

### 2.7 Catalicity —— 高温空气圆柱**催化壁**（2 个变体）

路径：`plugins/NEQ/testcases/CNEQ/Catalicity/`

- 维度：2D 圆柱绕流
- 模型：**CNEQ 单温度，air5**，Mutation 1.x，**park5**（Park 5 反应：3 离解 + 2 交换）
- 来流：u∞=1019.85 m/s，**T∞=6000 K**（来流已部分离解：N 2.77e-4 / O 1.12e-4 / N2 9.19e-5 / NO 2.87e-7 / O2 1.74e-9 kg/m³），p∞=1500 Pa
- 边界条件：**等温催化壁 Tw=400 K**，**Γ_N=0.254、Γ_O=0.105**（N/O 原子复合效率，Nr=2）；两侧对称面镜像；远场超声速入口
- 空间方法：FVM **一阶**（AUSMPlusMS2D；二阶在注释中）
- 特征：化学非平衡边界层 + **壁面催化复合热流**（heat-skin-cylin.plt 后处理）
- 变体：`Testcase_TCNEQ.CFcase` 用 `...Cat_oldFVMCC`（Γ 在 BC 内设）；`Test_for_Cyl.CFcase` 用 `...Cat_nadFVMCC`（Γ 在物理模型层全局设）——两种催化壁 BC 实现的对比
- 可运行性：**网格 `mesh-cylind.neu` 缺失 → 不可直接运行**

### 2.8 PrabhuCylinder —— RDS 双温度圆柱（1 个）

路径：`plugins/NEQ/testcases/PrabhuCylinder/PrabhuCylRDS_TCNEQ.CFcase`

- 维度：2D 圆柱绕流
- 模型：**TCNEQ 双温度，air5**（9 变量 RhoivtTv），Mutation 1.x，**park5**
- 来流：u∞=4678 m/s，T∞=Tv∞=241 K，ρ∞=9.2e-3 kg/m³（未离解空气）
- 空间方法：**RDS/FluctSplit：CRD 格式 + SysNC 系统分裂器**（LRD/SysN 备选），Cons 变量，数值雅可比
- 边界：等温无滑移非催化壁 **TWall=811 K**（Prabhu 高焓圆柱实验条件）；对称面；超声速入口
- 特征：脱体激波 + 双温度松弛 + 粘性扩散
- 可运行性：**网格 `grid2.neu` 缺失 → 不可直接运行**

### 2.9 Nozzle1DNEQ —— 高焓喷管多温度热非平衡（2 个）

路径：`plugins/NEQ/testcases/TCNEQ/Nozzle1DNEQ/`

- 维度：**1D 准一维喷管**（面积变化源项）
- 来流（入口总条件）：Tt=10000 K，Pt=1 atm，平衡组分入口 `SubInletEuler1DTtPtYiMultiTvTeFVMCC`，出口超声速
- 空间方法：FVM 一阶，`AUSM PlusMS1D`
- 特征：高温空气膨胀中的**组分冻结、振动/电子温度解耦（热冻结）**；无激波/无壁面

| 文件 | 模型 | 网格 |
|---|---|---|
| `nozzle1DFVM_ThermNEQMultiTvTe.CFcase` | **air11，3 个振动温度 + 电子温度 Te**（17 变量），Mutation2，parkair93 | `nozzle.CFmesh`（767 单元，含重启解）**已提供** |
| `nozzle1DFVM_ThermNEQMultiTvTeCR_Pvt.CFcase` | **95 组分碰撞-辐射（CR）模型 air11starB**（含激发态，反应 Abba_At，BoltzmannIDs=86..94，辐射逃逸因子 Escape=1.0），从完全气体解重启 | `nozzle1DFVM_PG_Newton_100.CFmesh` **已提供** |

可运行性：网格齐全；需 Mutation2 库（本机未编译）。

### 2.10 ShockTube —— 1D 双温度空气激波管（1 个）

路径：`plugins/NEQ/testcases/TCNEQ/ShockTube/shocktubeNEQ.CFcase`

- 维度：1D；模型：**TCNEQ air5**（5 组分 + 1 振动温度），Mutation2，park5
- 空间：FVM 一阶 AUSM PlusMS1D；显式推进（隐式段被注释），100 步
- 初始：x=0.5 处左右间断；边界：两端镜像反射（封闭激波管）
- 特征：激波、接触间断、膨胀波在振动/化学非平衡下的传播
- 可运行性：**网格参数文件 `ParametersST.CFmesh` 缺失 → 不可直接运行**（且文件较老旧）

### 2.11 ICP2Cat —— 感应耦合等离子体炬 + 变催化壁（1 个）

路径：`plugins/NEQ/testcases/TCNEQ/ICP2Cat/restart.CFcase`

- 维度：2D；模型：**TCNEQ air11**（11 组分 + Tv + 电子能），Mutation2OLD，parkair93
- 流动：**亚声速高焓等离子体射流**（核心约 8000 K，610 m/s，2000 Pa），**无激波**
- 空间：FVM，`AUSMPlusUpMS2D`（machInf=0.34），y<0.07 区域二阶 + Venktn2D
- 边界：入口 `SubInletInterpYiVTTv` 从 `inlet.dat` 插值给定剖面（已提供）；IsoWall 等温 350 K；**CatWall 变催化效率壁**（Γ_N,O 沿 x 分段 0.008/0.7/0.008，发射率 0.85，辐射平衡）；定压亚声速出口
- 特征：高焓射流、**壁面催化对热流的影响**（ICP 风洞材料测试模拟）
- 可运行性：**网格 `start6000.CFmesh` 缺失 → 不可直接运行**

### 2.12 EXPERT3D —— 3D 后处理算例（1 个，非求解）

路径：`plugins/NEQ/testcases/TCNEQ/EXPERT3D/expertM13.5_postprocessing.CFcase`

- 维度：**3D**（EXPERT 飞行器，Ma 13.5，45° 攻角，air5 TCNEQ，Mutation2 + park5）
- 性质：**纯后处理**（PrePostProcessingSubSystem）——读入已收敛 3D 解，用 `NavierStokesSkinFrictionHeatFluxCCNEQ3D` 计算并输出壁面热流/摩阻；壁面为 LTE 壁（从 EXPERT.dat 读温度分布）
- 可运行性：**`expert.CFmesh.START`、`EXPERT.dat` 均缺失 → 不可运行**（需先获得 3D 收敛解）

### 2.13 ArcJet —— 电弧加热器等离子体（15 个，全部 3D）

路径：`plugins/ArcJet/testcases/ArcJet/`（14 个）与 `ScalingTest/`（1 个）

**共同特征**：全部 **3D**；全部求解电势 φ（双线性系统 NSLSS + ELSS，焦耳加热源 `ArcJetPhiST`，无外加磁场）；CellCenterFVM + `AUSMPlusUp3D`；LinearLS3D + Venktn3D；PETSc PCASM/GMRES；气体为氩 `argon3`（phi 系列）或 11 组分空气 `air11`（8flow/3D 系列）；高焓来源为**电弧焦耳加热**（电流 0.346~700 A，温度 500~10500 K），属 LTE 范畴（非化学非平衡）。

| 分组 | 算例 | 模型/库 | 时间推进 | 辐射 | 可运行性 |
|---|---|---|---|---|---|
| torch+chamber+probe 100 kW（氩） | `arcjet_phi.CFcase` | ArcJetLTE3D + Mutation2OLD | Newton 伪稳态 | 无 | 缺 `cylinder.CFmesh` |
| | `arcjet_phi_Mut1.CFcase` | LTE + Mutation 1.x | 同上 | 无 | 网格 `bl1.neu.gz` **提供** |
| | `arcjet_phi_Mut1_LTE_Test.CFcase` | LTE + Mut1（0.346 A 小电流验证） | 同上 | 无 | 网格提供 |
| | `arcjet_phi_Mut1_PG.CFcase` | **理想气体对比版 ArcJetPG3D** | 同上，50 步 | 无 | 网格提供 |
| 并行扩展性 | `ScalingTest/arcjet_phi_Mut1_LTE_Test.CFcase` | LTE 圆管（电极-入口合一 BC），4 步纯回归 | Newton | 无 | 缺 `Tube188300.CFmesh` |
| 8 电极空气 + 辐射耦合（层流 LTE） | `arcjet_flow_rad_LTE.CFcase` | ArcJetLTE3D + Mutation2OLD | Newton+SER CFL，100 步 | 射线法 nDirs=24，2 辐射命名空间，**100 谱带** | 缺 `SOL`/`ArcJet3D.CFmesh`/`air-100Bands.dat` |
| | `arcjet_8flow_8rad.CFcase` | 同上 | 交互 CFL | 8 方向 × 8 命名空间（16 核） | 同上缺文件 |
| | `arcjet_8flow_24rad.CFcase` | 同上 | 同上 | 24 方向（32 核） | 同上 |
| | `arcjet_8flow_24rad_null.CFcase` | 同上但 **ComputeRHS=Null**（纯耦合开销测试） | 同上 | 24 方向 | 同上 |
| 8 电极空气 + 辐射（**SA 湍流 SALTE**） | `arcjet_8flow_8rad_SALTE_BDF2.CFcase` | ArcJetSALTE3D（LTE+SA 一方程湍流）+ **Mutation++**，7 方程 | **BDF2 非定常**，dt=1e-6 | 8 方向 | 缺文件 |
| | `arcjet_8flow_24rad_SALTE_BDF2.CFcase` | 同上 | BDF2，dt=2.5e-3 | 24 方向 | 缺文件 |
| | `arcjet_8flow_24rad_SALTE_CN.CFcase` | 同上 | **Crank-Nicholson**（BDF2/CN 对比） | 24 方向 | 缺文件 |
| | `arcjet_8flow_100rad_SALTE_BDF2.CFcase` | 同上 | BDF2 | **100 谱带 × 8 方向，按谱带 100 核并行**（108 核） | 缺文件 |
| 纯流动 SALTE | `arcjet3D_SALTE_MPP_BDF2.CFcase` / `_CN.CFcase` | SALTE + Mutation++，无辐射 | BDF2 / CN 对比 | 无 | 缺 `SOL` |

- 辐射耦合架构：`ConcurrentCoupler` 多命名空间（Flow 8 核 + Rad N 核），Flow→Rad 传 p,T，Rad→Flow 传辐射热汇 divq（`QRadST`）；谱带表 `air-100Bands.dat` 可在 `plugins/RadiativeTransfer/testcases/` 下找到同名文件
- 入口：电极间**径向质量流量喷射**（35 g/s，550 K，7 环）；壁/电极 TWall=10500 K（辐射算例）或 500 K（phi 系列）
- 特征：电弧焦耳加热、高温等离子体射流、辐射输运耦合、SA 湍流、非定常（BDF2/CN）

---

## 3. 全量汇总表

| # | 算例 | 维度 | 高焓特征 | 气体/模型 | 反应模型 | 数值格式 | 催化壁 | 输入齐全 | 本机构建可跑 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Hornung CNEQ M++ | 2D | 化学非平衡 | N2，单温度 | parkN2 | FVM+AUSM+MS | 否 | ✔ | ✔ |
| 2 | Hornung TCNEQ M++ | 2D | 热化学非平衡 | N2，双温度 | parkN2 | FVM+AUSM+MS | 否 | ✔ | ✔ |
| 3 | Hornung CNEQ Euler M++ | 2D | 化学非平衡(无粘) | N2 | parkN2 | FVM+AUSM+MS | 滑移壁 | ✔ | ✔ |
| 4 | Hornung CNEQ M++ MeFiAlgo ×2 | 2D | 化学非平衡+网格自适应 | N2 | parkN2 | FVM+AUSM+MS | 否 | ✔ | ✔ |
| 5 | Hornung CNEQ/TCNEQ（Mutation2OLD 版）×2 | 2D | CNEQ/TCNEQ | N2 | parkN2 | FVM+AUSM+MS | 否 | ✔ | ✘(缺库) |
| 6 | Hornung Plato ×2 | 2D | CNEQ/TCNEQ | N2 | parkN2 | FVM+AUSM+MS | 否 | ✔(网格) | ✘(PLATO) |
| 7 | FireII CNEQ M++ | 2D 轴对称 | 化学非平衡 | air11 | parkair93(M++默认) | FVM+AUSM+MS | 否 | ✔ | ✔ |
| 8 | FireII CNEQ / TCNEQ / fire2 / Plato | 2D 轴对称 | CNEQ / TCNEQ 双温度 | air11 | parkair93(cneq) | FVM+AUSM+MS | 否 | ✔ | ✘(缺库/路径) |
| 9 | DoubleCone CRD / FVM | 2D | TCNEQ，来流 Tv=3160K 热非平衡 | N2 | nompelisN2 | **RDS-CRD** / FVM+网格自适应 | 否 | ✔ | ✘(缺库) |
| 10 | CateIXV | 2D 轴对称 | 化学非平衡+**分材料催化+辐射平衡壁** | air5 | park5T | FVM+AUSM+MS | **是 Γ=0.019/0.19** | ✔ | ✘(缺库) |
| 11 | IXV LTE NS M++ / Euler M++ | 2D 轴对称 | **LTE 热化学平衡** | air11 平衡 | 平衡(库内) | FVM+AUSM+ | 否 | ✔(需 gunzip) | ✔ |
| 12 | IXV LTE NS / Euler（Mut2OLD） | 2D 轴对称 | LTE | air11 平衡 | 平衡 | FVM+AUSM+ | 否 | ✔(需 gunzip) | ✘(缺库) |
| 13 | SphereCO2 Mach38 | 2D | 化学非平衡(电离) | air7 | M++ 混合物默认 | FVM+AUSM+MS 二阶 | 否 | ✔ | △(需外部混合物数据) |
| 14 | Catalicity ×2 | 2D | 化学非平衡+**催化壁** | air5，6000 K 来流 | park5 | FVM+AUSM+MS 一阶 | **是 Γ_N=0.254, Γ_O=0.105** | ✘(缺网格) | ✘ |
| 15 | PrabhuCylinder RDS | 2D | TCNEQ 双温度 | air5 | park5 | **RDS-CRD+SysNC** | 否 | ✘(缺网格) | ✘ |
| 16 | Nozzle1D MultiTvTe / CR | 1D | **多振动温度+电子温度** / 95 组分 CR | air11 / air11starB | parkair93 / Abba_At | FVM 1D 一阶 | 无壁面 | ✔ | ✘(缺库) |
| 17 | ShockTube | 1D | TCNEQ | air5 | park5 | FVM 1D 显式 | 无壁面 | ✘(缺网格) | ✘ |
| 18 | ICP2Cat | 2D | TCNEQ 亚声速高焓射流+**变催化壁** | air11 | parkair93 | FVM+AUSM+-up | **是(分段 Γ)** | ✘(缺网格) | ✘ |
| 19 | EXPERT3D | **3D** | TCNEQ 后处理 | air5 | park5 | — | LTE 壁 | ✘ | ✘ |
| 20 | ArcJet phi 系列 ×3（含网格） | 3D | **LTE 电弧加热** | argon3 | — | FVM+AUSM+-up | 电极/绝缘壁 | ✔ | ✘(缺 Mut1 库) |
| 21 | ArcJet 8flow/3D 系列 ×11 | 3D | LTE+电弧+**辐射耦合**(+SA 湍流) | air11 | — | FVM+AUSM+-up(+Turb) | 电极/绝缘壁 | ✘ | ✘ |

---

## 4. 运行前提与"开箱即跑"清单

**本机构建状态**（`build/optim/dso` + `install/bin/coolfluid-solver` 已存在）：
- 已编译：`libMutationppI`（Mutation++ 接口）、`libMarcoTest`、`libNEQ`、`libLTE`、`libArcJet`、`libFluctSplitNEQ`、`libFiniteVolumeNEQ` 等
- **未编译**：旧版 `libMutation`（Mut1）、`libMutation2OLD`、`libMutation2`、`libPlatoI` → 所有依赖这些库的算例在本机当前构建下不能直接运行，需安装相应第三方库并在 CMake 中开启对应选项重新编译

**当前构建下开箱即跑（网格 + 库均满足）共 7 个：**

1. `NEQ/testcases/TCNEQ/Hornung/hornung_FVM_NS_CNEQ_M++.CFcase`（CNEQ，N2 圆柱）
2. `NEQ/testcases/TCNEQ/Hornung/hornung_FVM_NS_TCNEQ_M++.CFcase`（TCNEQ 双温度）
3. `NEQ/testcases/TCNEQ/Hornung/hornung_FVM_NS_CNEQ_euler_M++.CFcase`（无粘 CNEQ）
4. `NEQ/testcases/TCNEQ/Hornung/hornung_FVM_NS_CNEQ_M++_MeFiAlgo.CFcase` 及 `_MeFiAlgo_Firas.CFcase`（网格自适应）
5. `NEQ/testcases/TCNEQ/FireII/fire2_1643s_CNEQ_M++.CFcase`（FIRE II 再入，air11）
6. `LTE/testcases/IXV/ixvLTE_Mutation++.CFcase` 与 `ixvLTE_Euler_Mutation++.CFcase`（LTE Ma25；**需先 `gunzip CATE_v7_small.neu.gz`**）

**补齐旧版 Mutation 库后可增加运行**：FireII 其余 4 个、DoubleCone 2 个、CateIXV、Nozzle1D 2 个、ArcJet phi 系列 3 个（输入均已齐全）。

**缺失输入、需另行获取网格/数据的**：Catalicity ×2（mesh-cylind.neu）、PrabhuCylinder（grid2.neu）、ShockTube（ParametersST.CFmesh）、ICP2Cat（start6000.CFmesh）、EXPERT3D（expert.CFmesh.START/EXPERT.dat）、ArcJet 8flow/3D 全部 11 个（SOL/ArcJet3D.CFmesh）、ScalingTest（Tube188300.CFmesh）。

---

## 5. 按物理特征的算例索引

- **激波（弓形激波/脱体激波）**：Hornung、FireII、IXV（LTE 与 CateIXV）、Mach38、Prabhu、Catalicity、DoubleCone、ShockTube
- **激波-激波/激波-边界层干扰、分离再附**：DoubleCone Run 42
- **边界层 + 壁面热流后处理**：Hornung、FireII、CateIXV、IXV、Mach38、Catalicity（`NavierStokesSkinFrictionHeatFluxCCNEQ` 系列）
- **壁面催化效应**：CateIXV（分材料 Γ=0.019/0.19 + 辐射平衡壁）、Catalicity（Γ_N=0.254/Γ_O=0.105）、ICP2Cat（分段变 Γ）；其余算例均为非催化壁
- **热力学/化学平衡（LTE）**：LTE/IXV 4 个、ArcJet 全部 15 个（其中 1 个为理想气体对比）
- **化学非平衡（CNEQ，单温度）**：Hornung CNEQ 系列、FireII CNEQ ×2、CateIXV、Mach38、Catalicity ×2
- **热化学非平衡（TCNEQ，双温度 T-Tv）**：Hornung TCNEQ 系列、FireII TCNEQ ×3、DoubleCone ×2、Prabhu、ICP2Cat、ShockTube
- **多振动温度 + 电子温度（热非平衡高级模型）**：Nozzle1D MultiTvTe（3Tv+Te）与 CR 版（95 组分碰撞-辐射）
- **网格自适应（激波贴合）**：Hornung MeFiAlgo ×2、DoubleCone FVM
- **辐射输运耦合**：ArcJet 8flow 系列（射线法，最多 100 谱带）；CateIXV/ICP2Cat 壁面辐射平衡边界
- **电磁耦合（焦耳加热）**：ArcJet 全部
- **湍流**：ArcJet SALTE 系列（Spalart-Allmaras 一方程，LTE 湍流）；其余高焓算例均为层流
- **3D 算例**：EXPERT3D（后处理）、ArcJet 全部 15 个；其余 NEQ/LTE 算例均为 2D/2D 轴对称/1D
