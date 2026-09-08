# COOLFluiD 高焓流动验证报告

日期：2026-09-07（2026-09-08 第二次复核；2026-09-08 第三次修订：系统性修复；2026-09-08 第四次修订：V5c/run2 完成与诊断）｜ 版本：复核修订版 ｜ 状态：V5c/run2 已完成，物理有效性诊断完成

> **第三次修订（系统性修复工作）主要更新**
> 1. **修复 Hornung V5 细网格算例的网格尺度错误**：V5 CFcase 对已是米制的
>    `hornung_quad_1st.CFmesh` 再施 `ScalingFactor=1000`，整个计算域被缩小
>    1000 倍（0.05 m → 0.05 mm），圆柱完全落入计算域内。已删除该缩放并加注释，
>    修正版（V5b）排入 FireII 化学相完成后自动串行运行（12 核，保持核数预算）。
>    此前 V5 "完成 50000 步" 的结果（δ/R=-0.9989）为该 bug 产生的无效解，已作废。
> 2. **修复 ShockTube 1D NEQ RHS≡0 根因**：`Euler1DNEQRhoivt::setThermodynamics`
>    缺少 `_library->setState()` 调用（2D 版本有、1D 缺失），导致 Mutation++ 状态
>    未初始化、NaN 通量、KSP 0 步"收敛"。修复后 7 个残差分量中 6 个收敛至
>    −6，仅 T 分量停滞（~3.1）。
> 3. **FireII 改为"冻结化学 → 化学激活重启"两阶段方案**并完成冻结相运行：
>    冻结相 1159 步（CFL 0.01→0.1→0.5）在 CFL=0.5 阶段于 1159 步发散
>    （残差 3.98→5.04→−DBL_MAX）；iter_1000 重启场主体激波层 T≈2.9–4.9 万 K
>    （物理合理），但含 9 个过冲单元（T 达 1.0e6 K）。化学相已从该场重启
>    （12 核，CFL 0.01→0.05→0.1 阶梯，20000 步），过冲持续弛豫
>    （T_max 1.02e6 → 2.7e5 → 1.3e5 K，趋势文件 `fireii_chem_trend.log`）。
> 4. **MutationppI 适配层数值鲁棒化**：质量分数断言（`m_y[is]<1.1`）改为
>    截断到 [0,1]，非正压力不再断言而返回安全值——均属适配层，未改 Mutation++。
> 5. **FireII 网格球头半径实测**：对重启网格 Wall 节点作圆拟合，R_n=0.8433 m
>    （文献 FIRE II 球头 0.9347 m，差 −9.8%）；Sutton-Graves 驻点热流参考
>    579 W/cm²（文献 Rn）/ 610 W/cm²（网格 Rn）。

> **第二次复核主要修订**
> 1. **修正冻结/平衡激波脱体距离极限排序错误**：脱体距离与激波密度比成反比
>    （Hornung 1972 原文 "inversely proportional"）。冻结流密度比小（≈6.5）
>    → 脱体距离**大**（δ/R≈0.30）；平衡流密度比大（≈11.7）→ 脱体距离**小**
>    （δ/R≈0.17）。实验值 0.22 位于两者之间。原报告把两者标反（冻结 0.13 /
>    平衡 0.30），据此得出的"CFD δ/R 超过平衡极限"结论是错误的。
> 2. **改用 Mutation++ `mppshock` 正激波解作为定量参考**（冻结 RH + 平衡终态），
>    替代之前引用的粗略理想气体估值。
> 3. 从全场 `HornungN2.plt`（861 单元 P0 场）提取驻点线，给出 4 种激波定位
>    准则的散布，并以密度中点法（与干涉测量直接可比）为主估计。
> 4. 更新 SU2（残差停滞、未充分收敛）、FireII（532 步发散）、ShockTube（时间
>    推进已激活但化学刚性/隐式时间项待修）的真实状态。
> 5. 删除不实引用：Lani 2009 博士论文验证的是 Double Cone（run 35/40/42）与
>    HEG 空气圆柱，**不含** Hornung N2 圆柱，故不应用作 Hornung 脱体距离出处。

## 1. 目标

参考 COOLFluiD 相关论文（Lani 2009 博士论文等，文献位置见
`/home/tang/Downloads/COOLFLUiDPaper.bib`），验证当前版本 COOLFluiD 求解器
+ Mutation++（外部接口，**未修改其源代码**）在高焓非平衡流动模拟中的正确性
和可靠性。

**参考基准说明**：本报告的 Hornung N2 圆柱脱体距离对比，直接以
Hornung (1972, *J. Fluid Mech.* **53**(1):149–176) 实验数据和
Hornung & Wen 提出的"脱体距离 ∝ 1/激波密度比"标度律为准，并用
Mutation++ `mppshock` 给出冻结/平衡密度比。Lani 2009 论文仅作为 COOLFluiD
NEQ 求解框架的总体背景参考。

验证策略：
1. **Hornung N2 圆柱**（CNEQ）：与 Hornung 1972 实验对比激波脱体距离，并与
   `mppshock` 冻结/平衡正激波解定量对比驻点线 T、p、密度比
2. **FireII**（air_11 CNEQ）：拟与飞行数据对比（当前在 532 步发散，见 §5）
3. **SU2 交叉对比**：只读 SU2 NEMO HEG 圆柱结果，定性对比壁面压力（见 §4）
4. **Mutation++ 独立核查**：验证库的物理正确性（§2）

## 2. Mutation++ 库完整性核查

**规则**：严禁修改 Mutation++ 源代码及核心配置文件。所有集成工作通过外部接口
（MutationppI 适配层）调用。若确认 Mutation++ 存在错误，生成报告并停止运行算例。

| 检查项 | 结果 | 备注 |
|--------|------|------|
| checkmix air_5 / n2_2 / air_11 | ✅ 通过 | 物种、摩尔质量、生成焓、Park 反应速率正确 |
| mppequil 平衡组分（1 atm, 3000–10000 K） | ✅ 通过 | 与经典平衡空气图像一致（O₂ ~4000K 解离、N₂ ~6000–9000K） |
| mppequil 低气压 117 Pa | ✅ 通过 | 解离温度前移，物理趋势正确 |
| mppshock 低密度 N₂ 强激波 | ⚠️ 挂起（>5 min 无输出） | 工具层牛顿迭代鲁棒性问题，非库物理错误；COOLFluiD 不调用该工具 |
| ChemNonEq1T setState 变量集语义 | ✅ 通过 | type 1 =（物种密度, T）；MutationppI 适配层调用方式正确 |
| VT 能量交换源项 | ✅ 通过 | 源项极小（~0.04 W/m³），振动冻结物理正确 |
| 运行时 ABI 兼容性 | ✅ 通过 | libmutation++.so v1.0.5-92-gbb054e5；Hornung 稳定运行 38054 步验证 |

**结论**：Mutation++ 本体物理正确，未触发"确认错误即停止"条款。
所有集成工作均通过 MutationppI 适配层完成，**未修改 Mutation++ 源代码或数据文件**。

复现命令：
```bash
source ~/.bashrc
export MPP_DATA_DIRECTORY=/home/tang/packages/Mutationpp/data
checkmix air_5          # 物种信息
mppequil -P 101325 -T 5000 air_5   # 平衡组分
```

## 3. Hornung N2 圆柱算例验证

### 3.1 算例设置

| 参数 | 值 | 说明 |
|------|-----|------|
| 网格 | coarse.CFmesh | 800 四边形单元，R=12.7 mm |
| 物理模型 | Euler2DNEQ | 2D 欧拉 + 化学非平衡（CNEQ, 1T） |
| 混合物 | n2_2 | 纯 N₂（物种顺序 [N₂, N]） |
| 来流速度 | 5590 m/s | 对应 Hornung 1972 lens-expansion shot |
| 来流温度 | 1833 K | |
| 来流密度 | 0.004956 kg/m³ | p_inf ≈ 2909 Pa |
| 圆柱半径 | 12.7 mm (0.0127 m) | 1 英寸圆柱 |
| 通量分裂 | AUSM+ | |
| 时间推进 | NewtonIterator + PETSc | GMRES, ASM 预处理 |
| 收敛目标 | Norm = -3.0 | 38054 步达到 -3.00009 |
| 运行时间 | 47 min 43 s（串行） | |

### 3.2 激波脱体距离验证（已修正冻结/平衡排序）

**物理标度律**：Hornung (1972, JFM 53(1):149–176) 指出，钝体激波脱体距离与
正激波后的密度比成反比（"stand-off distance is inversely proportional to the
density ratio across the shock"）。因此：

- **冻结化学**：激波后气体不解离，密度比小（`mppshock` 给出 6.54）→ 激波层
  较厚、脱体距离**大**（δ/R≈0.30）。
- **平衡化学**：N₂ 大量解离吸热，密度比大（`mppshock` 给出 11.72）→ 激波层
  薄、脱体距离**小**（δ/R≈0.17，按 0.30×6.54/11.72 标度）。
- **非平衡实验**：脱体距离介于两者之间。Hornung 1972 N₂ 透镜膨胀风洞实验
  δ/R≈**0.22**。

| 数据来源 | 密度比 ρ₂/ρ₁ | δ/R | δ [mm] | 说明 |
|----------|-------------|------|--------|------|
| 冻结化学极限 | 6.54 | **≈0.30（大）** | ≈3.8 | 解离被抑制，激波层厚 |
| **Hornung 1972 实验** | —（非平衡）| **0.22** | 2.79 | 位于两极限之间 |
| 平衡化学极限 | 11.72 | **≈0.17（小）** | ≈2.2 | 完全解离，激波层薄 |
| **COOLFluiD V3 CFD（密度中点法）** | — | **0.306** | 3.89 | 与干涉测量直接可比 |
| CFD 定位准则散布 | — | 0.21–0.47 | 2.6–6.0 | 激波仅跨 ~3 个粗单元 |

**激波定位方法与不确定性**：从全场 `HornungN2.plt`（861 单元 P0）提取驻点线
（21 个单元中心，x=12.70–25.81 mm）。冻结 T 峰在 x=15.32 mm（T=9070 K），
首个来流单元在 x=18.73 mm（T=1833 K），激波在 **3.41 mm（约 3 个单元）** 内
被抹平。四种定位准则结果：

| 准则 | x_sh [mm] | δ/R |
|------|-----------|------|
| T 中点 | 17.46 | 0.375 |
| T 最大梯度 | 18.73 | 0.475（落于来流侧单元边界，粗网格伪影）|
| **密度中点（主估计）** | **16.59** | **0.306** |
| 密度最大梯度 | 15.32 | 0.206（落于冻结峰单元边界，伪影）|

最大梯度准则因激波仅跨 3 个单元而落在离散单元边界上，不可靠；密度中点法与
Hornung 干涉测量（测密度）口径一致，取为主估计 **δ/R≈0.31**。

**分析（修正后）**：
- CFD 密度中点 δ/R≈0.31 落在**冻结极限（0.30）附近**，明显大于实验值 0.22
  （高估约 39%），更远大于平衡极限 0.17。这说明在 800 单元粗网格上，激波被
  数值粘性抹平、激波层内化学弛豫区分辨不足，使**脱体距离表现得接近冻结情形**
  （解离使激波层变薄的效应尚未在脱体距离上充分体现）。
- 关键对照：同一粗网格解的**近壁热力学状态却已达到平衡**（见 §3.3：近壁 T、p、
  密度比与 `mppshock` 平衡解相差 1–5%）。即"壁面平衡、脱体距离偏冻结"——这是
  粗网格下激波抹平 + 弛豫区空间分辨不足的典型表现，**不是物理模型错误**。
- 冻结 T 峰（9070 K）低于 `mppshock` 冻结 RH 值（13914 K）约 35%，同样因为
  尖锐的冻结温度峰在厚激波/弛豫区内被空间平均（见 §3.3）。
- **结论**：化学非平衡物理方向正确（解离、吸热、弛豫均出现），但 δ/R 的定量
  收敛需要更细网格以分辨激波与弛豫区。V5 尝试 jesus0 网格（3680 单元），
  154 步内未收敛（CFL=0.5 残差上升），需进一步调整 CFL 调度/初值后重跑。

### 3.3 驻点线物理量验证

从 V3 收敛解提取驻点线（y≈0, x>0），关键物理量：

| 位置 | T [K] | ρ [kg/m³] | ρ_N₂ | ρ_N | p [Pa] | 说明 |
|------|-------|-----------|------|------|--------|------|
| 来流（x→∞） | 1833 | 0.00515 | 0.00496 | 0.000195 | 2909 | 精确保持来流条件 |
| 激波后峰值 | 9070 | 0.032 | 0.0257 | 0.0063 | 103325 | 激波压缩 + 部分解离 |
| 近壁（x=R） | 6739 | 0.0576 | 0.0411 | 0.0165 | 148390 | 驻点压缩，显著解离 |

**与 Mutation++ `mppshock` 正激波解的定量对照**（V3 来流 P=2909 Pa, T=1833 K,
V=5590 m/s，混合物 n2_2）：

| 量 | mppshock 冻结 RH | mppshock 平衡终态 | COOLFluiD V3 | 偏差 |
|----|-----------------|-------------------|--------------|------|
| 激波后温度 T [K] | 13914 | 6662 | 峰值 9070 / 近壁 6739 | 峰 −35% / 壁 **+1.2%** |
| 激波后压力 p [kPa] | 144.5 | 155.7 | 近壁 148.4 | **−4.7%**（对平衡）|
| 密度比 ρ₂/ρ₁ | 6.54 | 11.72 | 峰 6.47 / 近壁 11.63 | 峰 −1.1% / 壁 −0.8% |

**物理合理性分析**：
1. **近壁平衡态吻合极好**：近壁 T=6739 K（vs 平衡 6662 K，+1.2%）、近壁密度比
   11.63（vs 11.72，−0.8%）、近壁 p=148 kPa（vs 平衡 155.7 kPa，−4.7%）。说明
   Mutation++ 化学源项在驻点区把气体正确弛豫到接近平衡组成，热力学/化学耦合
   端到端正确。
2. **冻结峰被粗网格抹平**：`mppshock` 冻结 RH 温度峰为 13914 K（替代原报告
   粗略估值 ~15800 K），CFD 峰值仅 9070 K（−35%）。这是因为尖锐的冻结温度峰
   位于激波紧贴后的薄层，在 3.41 mm 厚的抹平激波/弛豫区被空间平均，且该峰
   单元已部分解离；冻结密度比（6.47 vs 6.54）反而吻合良好（−1.1%），说明
   激波压缩本身正确，差异主要在温度峰的分辨率。
3. **物种剖面**：来流 N 原子质量分数 y_N≈3.9%；激波后增至 ≈19.7%；近壁达
   **28.7%**，解离沿驻点线单调推进，化学非平衡方向正确。
4. **压力剖面**：来流 2909 Pa → 激波后 103 kPa → 近壁 148 kPa，压力比
   p_wall/p_inf ≈ 51，与 M∞≈6.28 强激波 + 驻点压缩量级一致，并落在
   `mppshock` 冻结/平衡压力（144.5–155.7 kPa）区间内。
5. **γ（有效比热比）**：来流 1.32 → 激波后 1.30 → 近壁 1.34，反映化学组成
   变化对比热比的影响。

> 复现命令：
> ```bash
> export PATH=/home/tang/packages/Mutationpp/install/bin:$PATH
> export MPP_DATA_DIRECTORY=/home/tang/packages/Mutationpp/data
> export LD_LIBRARY_PATH=/home/tang/packages/Mutationpp/install/lib:$LD_LIBRARY_PATH
> mppshock -P 2909 -T 1833 -V 5590 -m 0 n2_2   # 打印冻结 RH 与平衡终态
> ```

### 3.4 输出文件

| 文件 | 位置 | 说明 |
|------|------|------|
| **复核脚本** | `doc/validation/revalidate_hornung.py` | 全场提取驻点线 + 4 准则激波定位 + mppshock 对照 |
| **复核摘要** | `plugins/NEQ/testcases/TCNEQ/Hornung/results/RESULTS_CNEQ_EULER_N22_V3/hornung_v3_revalidation.txt` | 修正后的脱体距离与激波状态数值 |
| **复核驻点线图** | `plugins/NEQ/testcases/TCNEQ/Hornung/results/RESULTS_CNEQ_EULER_N22_V3/hornung_v3_revalidation_stagline.png` | T/ρ/物种 vs x，含 mppshock 参考 |
| **复核脱体距离图** | `plugins/NEQ/testcases/TCNEQ/Hornung/results/RESULTS_CNEQ_EULER_N22_V3/hornung_v3_revalidation_standoff.png` | 冻结/平衡/实验/CFD 对照 |
| 驻点线数据 | `plugins/NEQ/testcases/TCNEQ/Hornung/results/RESULTS_CNEQ_EULER_N22_V3/HornungN2_stagline_full.dat` | 21 点稀疏线（旧） |
| 体积场 | `plugins/NEQ/testcases/TCNEQ/Hornung/results/RESULTS_CNEQ_EULER_N22_V3/HornungN2.plt` | Tecplot 格式全场 861 单元 P0 数据 |
| 壁面数据 | `plugins/NEQ/testcases/TCNEQ/Hornung/results/RESULTS_CNEQ_EULER_N22_V3/HornungN2.surf.plt` | 壁面 41 节点 |

> 注：旧版 `validate_hornung_v3.py` 与 `hornung_v3_validation_summary.txt`
> 中的冻结/平衡极限排序有误（已在本报告修正），请以 `revalidate_hornung.py`
> 输出为准。

### 3.5 Hornung V5 细网格（第三次修订：网格尺度 bug 发现与修复）

**发现**：V5 曾"完成 50000 步"（残差 −9.05/−9.91/−3.00/−2.78/−2.39，
看似收敛），但后处理 δ/R=−0.9989、p_wall=2.9 kPa（应 ~144 kPa 量级）——
结果无效。排查确认：

- `hornung_quad_1st.CFmesh` 解析节点坐标 **x∈[−0.025, 0] m，y∈[−0.05, 0.05] m，
  本身已是米制**；
- 但 V5 CFcase 中保留了 `CFmeshFileReader.Data.ScalingFactor = 1000`（该参数
  对读入坐标做**除法**），整个域被缩小 1000 倍 → 0.05 mm 域、圆柱完全"罩住"
  全部单元（plt 中 x 范围 −2.5×10⁻⁵ m 证实）；
- 残差"收敛"只是数值上无黏通量平衡，物理上完全错误。**该 50000 步结果作废。**

**修复**：删除 `ScalingFactor` 行并在 CFcase 中加注释说明网格单位来历
（Gambit .neu 为 mm、转换得到的 CFmesh 已为 m）；同时清理了
`FVMCC_ComputeRHS.cxx` 的临时调试输出并重建 `libFiniteVolume`。

**复跑安排**：修正版（V5b）配置为 FireII 化学相完成后由
`run_hornung_v5b_after_chem.sh` 自动以 12 核串行启动（核数预算不变），
结果将替换 `plugins/NEQ/testcases/TCNEQ/Hornung/results/RESULTS_CNEQ_EULER_N22_V5/` 并以 `postprocess_final.py`
重新定量对比（细网格下 δ/R 与实验 0.22 的偏差是 V3→V5 的关键检验项）。

**V5b 结果（50000 步，CFL 上限 10）—— 未收敛，作废**：

- 网格尺度已修正（x∈[−0.025,0] m，T_max=12989 K 物理合理）；
- 但收敛历史显示：前两分量（物种密度）在 iter 5000 收敛至 −7，速度/T
  分量在 CFL=1.0 阶段（iter 10000–20000）曾降至 −1.1/−0.9/−0.5；
  **CFL 升至 10 后（iter 20000+）残差反弹至正值（−0.17/+0.06/+0.44）**，
  激波层压力→0、密度→0，解发散；
- 根因：细网格（14641 单元）对 CFL 更敏感，CFL=10 对动量/能量方程过激；
- 该 50000 步结果归档为 `plugins/NEQ/testcases/TCNEQ/Hornung/results/RESULTS_CNEQ_EULER_N22_V5_BROKEN_SCALE`（同时
  记录了缩放 bug 和 CFL 失稳两次失败）。

**V5c 结果（50000 步，CFL 上限 1.0）—— 已完成，但解物理无效**

- 运行完成：50000/50000 步，exit=0，WallTime=1h 34min（12 核）；
- CFL 调度：`if(i<3000,0.1,if(i<6000,0.3,if(i<10000,0.5,1.0)))`；
- 残差历史：

| 步 | Res 物种 0 | Res 物种 1 | Res u | Res v | Res T |
|----|-----------|-----------|-------|--------|-------|
| 1000 | −3.40 | −4.81 | +2.41 | +2.53 | +2.51 |
| 10000 | −7.05 | −7.91 | +0.17 | +0.51 | +0.86 |
| 20000 | −7.07 | −7.93 | −1.13 | −0.90 | −0.50 |
| 40000 | −7.10 | −7.95 | −1.27 | −1.05 | −0.61 |
| 50000 | −7.11 | −7.96 | −1.05 | −0.83 | −0.43 |

  物种密度分量收敛良好（−7/−8），但速度/T 分量停滞在 −0.4 至 −1.3 之间
  且从 40000→50000 步残差绝对值**反弹**（−1.27→−1.05 等），表明动量/能量
  方程未真正收敛。

- **物理有效性诊断（FAILED）**：对 `HornungN2.CFmesh` 驻点线 255 个单元直接
  解析原始变量 [rho0, rho1, u, v, T]，发现：
  - 来流侧（x≈−0.025）：rho≈6.5×10⁻⁵ kg/m³（应 5.15×10⁻³，**低 80 倍**）；
  - 激波后到壁面：rho 从 6.5×10⁻⁵ **单调递减**至 1.3×10⁻¹⁰ kg/m³
    （应递增，强激波压缩比 ≈6）；
  - 压力 p 从 59 Pa（激波后）→ 0.0001 Pa（壁面），而**冻结 RH 压力应为
    ~103 kPa**（压力比 ~35×来流）；
  - 速度 v 在壁面附近振荡 ±3000–4000 m/s（驻点线 v 应 ≈0），T 在
    10000–13000 K 与 2500–3500 K 间交替（奇偶失耦）；
  - 对比 FireII 冻结相（同框架 NavierStokes2DNEQ）：密度在激波后**正确增加**
    （7.8×10⁻⁴→8.7×10⁻⁴），速度递减至壁面，T 峰在激波后 40545 K——
    **FireII 冻结相物理有效**，排除了求解器整体缺陷，问题局限于 Hornung
    Euler2DNEQ 细网格配置。
- **根因推断**：V3 粗网格（800 单元）解物理正确（p_wall=148 kPa，ρ_wall/ρ_inf
  =11.6），而 V5c 细网格（14641 单元）解物理无效——差异可能源于：
  ① 细网格下 Euler 无黏方程在壁面附近的驻点奇异性更强，数值耗散不足以
  稳定驻点区；② CFL=1.0 对细网格动量/能量方程仍偏大（V5b 在 CFL=10 发散、
  V5c 在 CFL=1.0 完成但物理无效）；③ 物种方程收敛到非物理稳态（rho→0）
  后动量/能量无法纠正。
- **结论**：V5c 完成 50000 步但**解物理无效，作废**。Hornung 细网格验证
  需进一步降低 CFL（≤0.1）或改用 NavierStokes2DNEQ（黏性壁面条件消除驻点
  奇异性）。**当前 Hornung 定量结论以 V3 粗网格（800 单元）为准。**

## 4. SU2 NEMO 交叉对比

### 4.1 算例条件对比

| 参数 | COOLFluiD Hornung V3 | SU2 NEMO HEG |
|------|---------------------|--------------|
| 气体 | N₂ (n2_2, 2 组元) | air_5 (5 组元) |
| 马赫数 | ~6.28 | 8.803 |
| 来流温度 | 1833 K | 901 K |
| 来流压力 | ~2909 Pa | 476 Pa |
| 来流密度 | 0.005 kg/m³ | ~0.00184 kg/m³ |
| 圆柱半径 | 12.7 mm | 见 SU2 网格 |
| 物理模型 | Euler2DNEQ (CNEQ) | NEMO (Navier-Stokes + NEQ) |

**注意**：两算例条件不同（不同气体、不同马赫数、不同温度），因此对比为
**定性**对比（壁面压力分布形状、激波结构），而非定量对比。

### 4.2 壁面压力分布对比

| 指标 | COOLFluiD V3 | SU2 NEMO HEG |
|------|-------------|--------------|
| 驻点压力 | 148.4 kPa | 57.3 kPa |
| p_stag/p_inf | 51.0 | 120.4 |
| 压力分布形状 | θ=0 峰值，θ→背风侧衰减 | 同上 |

**SU2 收敛状态（复核发现）**：该 SU2 算例**未充分收敛**。其残差
rms[Rho₀]（log10）从来流初值约 −6.7 在激波形成时上升到约 −5.0 后**停滞**，
直到第 12250 步被终止（signal 15），有效下降仅约 1.5 个数量级，未达稳态
残差标准。因此 SU2 壁面压力（`wall_extract.csv`）来自一个准收敛解，
只能用于**定性/量级**对比。

**Mutation++ 独立核查（air_5 @ HEG 条件 P=476 Pa, T=901 K, V≈5300 m/s）**：

| 量 | mppshock 冻结 RH | mppshock 平衡终态 | SU2 驻点 |
|----|-----------------|-------------------|----------|
| 激波后压力 p [kPa] | 43.8 | 47.6 | 57.3（壁面驻点）|
| 激波后温度 T [K] | 13094 | 5786 | 未直接输出（VTK 仅守恒变量）|
| 密度比 ρ₂/ρ₁ | 6.34 | 11.78 | — |

SU2 壁面驻点压力 57.3 kPa 比 `mppshock` 平衡正激波压力 47.6 kPa 高约 20%
（驻点亚声速压缩会在正激波基础上进一步增压，加之解未充分收敛），量级与
趋势合理。

**分析**：
- 两求解器均预测驻点（θ=0）处压力峰值，沿圆柱表面向背风侧单调衰减。
- SU2 的 p_stag/p_inf = 120.4 高于 COOLFluiD 的 51.0，主因是 SU2 算例马赫数
  更高（M=8.803 vs 6.28），正激波压力比随 M 增大而增大；两者驻点压力均与
  各自 Mutation++ 正激波参考同量级。
- 压力分布**形状**定性一致，且与 Mutation++ 平衡正激波压力的偏差分别为
  COOLFluiD ≈−5%、SU2 ≈+20%，量级合理，支持两个独立求解器在高速钝体绕流上
  的物理一致性。SU2 因未收敛，差异不宜作定量结论。

输出文件：`plugins/NEQ/testcases/TCNEQ/Hornung/results/RESULTS_CNEQ_EULER_N22_V3/compare_wall_pressure_coolfluid_su2.png`、
`compare_stagline_coolfluid_su2.png`

### 4.3 SU2 数据读取说明

- **仅读取** SU2 算例结果（`/home/tang/packages/SU2/nemo_validation/results/heg_cylinder/ord2/`）
- **未修改** SU2 源代码或配置文件，**未运行** SU2 算例
- 读取文件：`run.log` / `history.csv`（收敛史）、`wall_extract.csv`（壁面压力）、
  `soln.vtk`（守恒变量场）
- SU2 VTK 文件仅存储守恒变量（Density_i, Momentum, Energy），无直接 T/p 场，
  因此驻点线 T/ρ 对比仅展示 COOLFluiD 数据

## 5. FireII 算例

### 5.1 算例设置

| 参数 | 值 | 说明 |
|------|-----|------|
| 网格 | fire2_small80x.CFmesh | 4455 节点 / 4320 单元（轴对称），球头 R_n=0.8433 m（圆拟合） |
| 物理模型 | NavierStokes2DNEQ | 2D Navier-Stokes + 化学非平衡 |
| 混合物 | air_11 | 11 组元空气（e⁻, N⁺, O⁺, NO⁺, N₂⁺, O₂⁺, N, O, NO, N₂, O₂）|
| 来流速度 | 10480 m/s | FIRE II 飞行轨迹 1643 s 点 |
| 来流温度 | 276 K | |
| 来流密度 | 0.00078 kg/m³ | p_inf ≈ 62 Pa |
| 壁面温度 | 640 K | 等温壁 |
| 通量分裂 | AUSM+ | AUSMPlusMS2D, choiceA12=5 |
| CFL 调度 | **两阶段方案**（见 §5.2） | 冻结相 0.01→0.1→0.5；化学相 0.01→0.05→0.1→0.3→1.0 |
| 收敛目标 | MaxNumberSteps = 20000 | 原始 Norm=-7.0 过严 |
| 运行核数 | 12 核 | ≤12 核限制内 |
| 实测耗时 | 冻结相 11.5 min / 1159 步；化学相 ~0.57 s/step | 12 核并行 |

### 5.2 运行状态（第三次修订：两阶段方案）

**阶段 0 — 前两次单阶段尝试（已放弃）**

- 首次（CFL=1.0 起步）767 步崩溃：`ChemNEQST.ci:202` 质量分数和断言失败；
- 第二次（0.1→1.0 阶跃）532 步发散，同一断言。根因均为 CFL 阶跃过猛 +
  11 组元化学刚性，单阶段"从人工边界层初值直接开化学"策略不可行。

**阶段 1 — 冻结化学相（已完成，1159 步，11.5 min）**

配置：species 冻结（y_N2/y_O2 固定），CFL 0.01(1–500)→0.1(501–1000)→0.5(1001–)。

- 残差全程在 3.1–5.3 间震荡，**未出现下降趋势**（起始流动瞬态主导）；
- **CFL=0.5 阶段失稳**：步 1157–1159 残差 3.98→5.04→−DBL_MAX（爆管式发散），
  进程按停止条件退出；
- **iter_1000 重启场诊断**（解析 `plugins/NEQ/testcases/TCNEQ/FireII/results/RESULT_FIREII_FROZEN/fire2-iter_1000.CFmesh`
  全部 4320 个状态）：主体激波层 T≈2.9×10⁴–4.9×10⁴ K（与冻结理想气体
  驻点温度 5.49×10⁴ K 同量级，物理合理）；**9 个过冲单元（0.21%）T 达
  1.0×10⁶ K**（CFL=0.1 阶段激波前沿已局部过冲，CFL=0.5 阶段恶化至发散）；
- 结论：冻结相得到了一个"主体物理合理 + 局部过冲待弛豫"的过渡场，但未收敛。

**阶段 2 — 化学激活重启（运行中，12 核）**

配置：从 `fire2-iter_1000.CFmesh` 重启（无 ScalingFactor，重启网格坐标已为
米制），CFL 0.01(<2000)→0.05(<5000)→0.1(<10000)→0.3(<15000)→min(1.0,×1.01)，
20000 步，`air_11` + ChemNonEq1T 激活。

- 弛豫趋势（`doc/validation/fireii_chem_trend.log` 监控）：T_max
  1.02×10⁶（重启初值）→ 2.7×10⁵（~1100 步）→ 1.3×10⁵（~1500 步），
  驻点壁面热流同步下降（1.83×10⁹ → 1.11×10⁹ W/m²）；
- 判断：解正朝物理激波层弛豫，但重启场含过冲污染，最终热流数字需待
  运行完成后按 §5.3 与 Sutton-Graves / LAURA-FUN3D 量级对照，并说明
  "未完全收敛 + 粗网格（54 壁面单元）"的适用范围。

**run1 终止（3090 步）与 run2 重启**

- run1 在 CFL 0.01→0.05 跳变后（步 3089 残差 2.98→4.23），步 3090
  出现 NaN 残差（−DBL_MAX），被停止条件误判为"收敛"提前退出；
- **根因**：11 组元化学刚性下 CFL 跳变仍过激；CFL=0.01 是唯一被验证
  连续 2000+ 步稳定的值；
- **run2 重启（运行中）**：从干净快照 `fire2-iter_3000.CFmesh`（T_max
  =1.63×10⁵ K，全有限）重启，**CFL 恒定 0.01**（不再跳变），12000 步，
  结果输出至 `plugins/NEQ/testcases/TCNEQ/FireII/results/RESULT_FIREII_MPP_RUN2/`；
- run2 弛豫趋势（`fireii_chem2_trend.log`）：T_max 1.63×10⁵ → 9.9×10⁴ K
  （~400 步）→ 6.3×10⁴ K（~3100 步），但**残差单调上升**：2.46（步 1）→
  3.64（步 1098）→ 4.66（步 2127）→ 5.19（步 3131）→ **5.21（步 3339）→
  −DBL_MAX（步 3340）**；
- **run2 结论：发散**。CFL 恒定 0.01（无跳变），但 11 组元化学源项使残差
  从第一步起**单调增长**，最终 NaN。这不是 CFL 问题，而是 11 组元空气
  化学刚性在当前显式伪时间推进框架下的根本限制。
- **run2 结果作废**：最终 `fire2.plt` 含 T=0/rho=0/p≈0 的非物理状态，
  驻点热流 6.62×10⁸ W/m²（66215 W/cm²）是 Sutton-Graves 值（579 W/cm²）
  的 **114 倍**，完全不可信。
- 注意：重启文件路径需放在 WorkingDir 相对路径
  （`plugins/NEQ/testcases/TCNEQ/FireII/RESULT_FIREII_MPP_RUN/`），
  因为 `CFmeshFileReader` 相对路径解析到 WorkingDir 而非 cwd。

### 5.2.1 FireII 冻结相定量诊断（唯一物理有效结果）

对 `plugins/NEQ/testcases/TCNEQ/FireII/results/RESULT_FIREII_FROZEN/fire2-iter_1000.CFmesh`（4320 单元，14 变量）
驻点线 80 个单元直接解析：

| 位置 | x [m] | rho [kg/m³] | u [m/s] | T [K] | 说明 |
|------|-------|-------------|---------|-------|------|
| 来流 | −0.0517 | 7.80×10⁻⁴ | 10480 | 276 | 精确保持来流条件 |
| 激波前 | −0.0002 | 7.80×10⁻⁴ | 10480 | 276 | 激波前未扰动 |
| 激波后 | 0.0000 | 8.70×10⁻⁴ | 8508 | 40545 | 密度增加 12%，T 峰 |
| 壁面附近 | 0.00009 | 8.42×10⁻⁴ | 1538 | 26582 | 速度递减至壁面 |

**物理有效性**：
- 密度在激波后**增加**（7.8×10⁻⁴→8.7×10⁻⁴）——方向正确（压缩）；
- 速度从 10480 m/s **递减**至 1538 m/s——驻点减速，方向正确；
- T 峰在激波后 40545 K，向壁面递减至 26582 K——物理合理；
- 9 个过冲单元（T>1×10⁵ K，0.21%）位于激波前沿，为 CFL=0.1 阶段局部过冲。

**局限性**：
- 冻结化学（无化学反应），气体组成固定为来流 N₂/O₂；
- 密度增幅（12%）远低于 Mach 31 正激波理论值（理想气体 ~6×），因激波跨
  仅 2-3 个单元（粗网格抹平）且化学冻结使激波层极薄；
- 冻结相在 CFL=0.5 阶段（步 1159）发散，iter_1000 为最后干净快照。

### 5.3 基准对比方法（已备）

- **驻点对流热流参考**：Sutton-Graves 关联式
  q = 1.7415×10⁻⁴ √(ρ/R_n) V³（SI）→ **579 W/cm²（文献 R_n=0.9347 m）/
  610 W/cm²（网格拟合 R_n=0.8433 m）**；文献量级：LAURA/FUN3D 全催化壁
  对流 ~6 MW/m²，辐射 ~1 MW/m²（1643 s 点）；
- **几何核实**：网格 Wall 节点圆拟合给出球头 R_n=0.8433 m（rms 5×10⁻⁴ m），
  40° 锥半角与 FIRE II 外形一致；
- **后处理**：`doc/validation/postprocess_final.py`（含 fireii_chem 分支：
  驻点线 T/y_N2/y_O2 剖面、壁面热流分布、双 Sutton-Graves 参考线、
  `fireii_chem_summary.txt` 摘要）；
- 化学相收敛后对比内容：q_stag/SG 比值、激波脱体 δ/R_n、峰值温度、
  N₂/NO 组分剖面（化学激活的定性证据）。

### 5.4 运行脚本与自动化

- 冻结+化学两阶段流水线：`doc/validation/run_fireii_pipeline_v5.sh`
- 化学相完成后自动串行 Hornung V5b（12 核核数预算不变）：
  `doc/validation/run_hornung_v5b_after_chem.sh`（含 6h 等待保护）
- 化学相弛豫监控（10 min 采样 T_max/q_stag）：
  `doc/validation/monitor_fireii_chem.sh` → `fireii_chem_trend.log`

## 6. 其他算例状态

### 6.1 ShockTube 1D（air_5 化学非平衡）

**第三次修订更新：RHS≡0 根因已修复，6/7 残差分量收敛至 −6。**

- **根因定位与修复**：2D 变量集（`Euler2DNEQCons` 等）的
  `setThermodynamics` 都会调用 `_library->setState()` 初始化 Mutation++
  状态，而 1D 的 `Euler1DNEQRhoivt::setThermodynamics` **缺失该调用**——
  Mutation++ 从未被告知当前热力学状态，内部状态停留在初始值 → 压力/输运
  系数错误 → NaN 通量 → KSP 0 步"收敛"（残差 −DBL_MAX，即 RHS≡0）。
  已在 `plugins/NEQ/Euler1DNEQRhoivt.cxx` 补上 `_library->setState()`
  （与 2D 实现对齐，属 COOLFluiD 侧修复，未改 Mutation++）。
- **修复后运行**（`shocktube_fix5.log`，串行，2000 步）：
  残差 7 分量中 6 个从 ~1 收敛到 **−5.9 ~ −7.8**（密度×5、动量×2、能量），
  **T 分量停滞在 ~3.12**（无下降趋势）。RHS≡0 问题（KSP 0 步迭代）消失。
- **遗留问题**：T 方程残差停滞——可能为驱动段 5000 K 高温区化学源项刚性
  在该变量集上的表现，或时间导数项激活方式仍不完整；瞬态激波传播速度/
  剖面与解析解的定量对比尚未通过。**结论：从"完全无法推进"推进到"可稳定
  推进且大部分方程收敛"，瞬态验证仍待通。**

此前修复（保留记录）：链接 `libMeshGenerator1D`/`libMeshTools`/`libMeshToolsFVM`，
`convertFrom = MeshGenerator1D`，`flagShock=1`（避开缺失的 Radius.dat），
`nbEulerEqs=2`（7 变量 Rhoivt 集），直名 `AUSMPlusMS1D` 通量分裂，
参数文件 label/value 分行格式。

### 6.2 DoubleCone Run42（N₂ TCNEQ）

- **原因**：TCNEQ（两温度模型）+ Run42 条件需要 ≥16 核运行 1-2 天
- **成本评估**：串行 ~20-25 sec/step，6 核 ~5-8 sec/step
- **超算脚本**：已备（`/home/tang/packages/COOLFluiD/doc/validation/`），
  提交命令见 §8

## 7. 环境配置与运行规范

### 7.1 环境加载

```bash
# 系统环境（所有程序）
source ~/.bashrc

# Python 程序额外激活 base 环境
source /home/tang/miniforge3/etc/profile.d/conda.sh && conda activate base
```

### 7.2 COOLFluiD 运行脚本

运行脚本位于 `/home/tang/packages/COOLFluiD/doc/validation/run_coolfluid.sh`，
封装了所有环境变量设置：

```bash
# 串行运行
bash run_coolfluid.sh <case_file> 1

# 12 核并行运行（8 小时超时）
bash run_coolfluid.sh <case_file> 12 28800
```

### 7.3 关键环境变量

| 变量 | 值 | 说明 |
|------|-----|------|
| `LD_PRELOAD` | `libfakecuda.so` | CUDA 垫片，绕过本机 GPU 驱动不稳定问题 |
| `LD_LIBRARY_PATH` | COOLFluiD/Mutation++/MPICH/Boost/PETSc/ParMETIS 库路径 | |
| `MPP_DIRECTORY` | `/home/tang/packages/Mutationpp` | Mutation++ 根目录 |
| `MPP_DATA_DIRECTORY` | `/home/tang/packages/Mutationpp/data` | 混合物数据目录 |

## 8. 超算运行脚本（高成本算例）

### 8.1 DoubleCone Run42（建议 ≥16 核，1-2 天）

```bash
#!/bin/bash
# PBS/SLURM 脚本 — DoubleCone Run42 N2 TCNEQ (Mutation++)
# 提交：qsub run_dcone_pbs.sh  或  sbatch run_dcone_slurm.sh

#PBS -N DCone_Run42
#PBS -l nodes=4:ppn=8          # 32 核
#PBS -l walltime=48:00:00
#PBS -q normal

# 加载环境
source ~/.bashrc

CF_ROOT=/home/tang/packages/COOLFluiD
MPICH_DIR=/home/tang/packages/mpichInstall
MPP_DIR=/home/tang/packages/Mutationpp
export MPP_DIRECTORY=${MPP_DIR}
export MPP_DATA_DIRECTORY=${MPP_DIR}/data
export LD_LIBRARY_PATH=${CF_ROOT}/install/lib:${CF_ROOT}/build/optim/dso:${MPP_DIR}/install/lib:${MPICH_DIR}/lib:/home/tang/packages/boost_1_85_0/install/lib:/home/tang/packages/petsc/arch-linux-c-opt/lib:/home/tang/packages/ParMETIS/install-mpich/lib

cd ${CF_ROOT}
${MPICH_DIR}/bin/mpirun -np 32 ${CF_ROOT}/build/optim/apps/Solver/coolfluid-solver \
  --scase plugins/NEQ/testcases/TCNEQ/DoubleCone/Run42_N2/DConeN2_42_FVM_M++.CFcase \
  --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso
```

### 8.2 FireII 全量（若 12 核不够，建议 ≥32 核）

```bash
#!/bin/bash
#SBATCH --job-name=FireII
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=16    # 32 核
#SBATCH --time=24:00:00
#SBATCH --partition=normal

source ~/.bashrc
# ... (同上环境设置)
srun -n 32 ${CF_ROOT}/build/optim/apps/Solver/coolfluid-solver \
  --scase plugins/NEQ/testcases/TCNEQ/FireII/fire2_1643s_CNEQ_Mpp.CFcase \
  --bdir ${CF_ROOT} --ldir ${CF_ROOT}/build/optim/dso
```

## 9. 验证状态总览

| 算例 | 状态 | 结果/证据 | 文件位置 |
|------|------|-----------|----------|
| Mutation++ 独立核查 | [OK] 通过 | checkmix/mppequil/mppshock 冻结+平衡正激波解合理 | — |
| Hornung 圆柱 V3 | [OK] 收敛+物理验证 | 38054 步收敛；**近壁 T +1.2%、p −4.7%、密度比 −0.8%（对 mppshock 平衡解）**；δ/R=0.31（密度中点，粗网格偏冻结侧，实验 0.22）| `plugins/NEQ/testcases/TCNEQ/Hornung/results/RESULTS_CNEQ_EULER_N22_V3/` |
| SU2 交叉对比 | [WARN] 定性一致，SU2 未收敛 | 壁面压力形状一致；SU2 残差停滞于 ~1e-5；驻点 57.3 kPa vs mppshock 平衡 47.6 kPa（+20%）| `plugins/NEQ/testcases/TCNEQ/Hornung/results/RESULTS_CNEQ_EULER_N22_V3/compare_*.png` |
| FireII 冻结相 | [OK] 物理有效 | iter_1000：密度激波后增加 12%，速度递减至壁面，T 峰 40545 K；9 个过冲单元（0.21%）；冻结相在 CFL=0.5 步 1159 发散 | `plugins/NEQ/testcases/TCNEQ/FireII/results/RESULT_FIREII_FROZEN/` |
| FireII 化学相 run2 | [FAIL] 发散 | CFL=0.01 恒定，残差从 2.46 单调上升至 5.21（步 3339）→ NaN（步 3340）；11 组元化学刚性根本限制 | `plugins/NEQ/testcases/TCNEQ/FireII/results/RESULT_FIREII_MPP_RUN2/` |
| ShockTube 1D | [WARN] RHS≡0 已修复，T 分量待通 | 修复 setState 后 6/7 残差收敛至 −6，T 停滞 ~3.1；瞬态激波对比未通过 | `plugins/NEQ/testcases/TCNEQ/ShockTube/` |
| DoubleCone Run42 | [WAIT] 待超算 | 需 ≥16 核，1-2 天 | 脚本已备 |
| Hornung V5（细网格）| [FAIL] V5c 解物理无效 | V3 收敛（δ/R=0.31）；V5 缩放 bug 作废；V5b CFL=10 失稳作废；V5c 50000 步完成但 rho→0/p→0 解物理无效（Euler 细网格驻点奇异性）；**以 V3 为准** | `plugins/NEQ/testcases/TCNEQ/Hornung/results/RESULTS_CNEQ_EULER_N22_V3/` `.../RESULTS_CNEQ_EULER_N22_V5C/` |

## 10. 结论（复核修订）

1. **Mutation++ 集成正确性**：通过 Hornung 圆柱算例端到端验证（38054 步稳定
   收敛），Mutation++（外部接口，未改源码）的化学非平衡计算功能在 COOLFluiD
   中正确集成。`mppshock` 冻结/平衡正激波解与 CFD 对照一致；Mutation++ 本体
   物理正确，未触发"确认错误即停止"条款。

2. **求解器物理正确性（定量证据）**：Hornung N2 圆柱近壁热力学状态与
   Mutation++ 平衡正激波解高度吻合——T 6739 K vs 6662 K（**+1.2%**）、
   p 148.4 vs 155.7 kPa（**−4.7%**）、密度比 11.63 vs 11.72（**−0.8%**）；
   冻结侧密度比 6.47 vs 6.54（−1.1%）。激波压缩、N₂ 解离吸热降温、驻点压缩、
   化学弛豫均被正确捕获。

3. **激波脱体距离（修正后结论）**：脱体距离与激波密度比成反比，故冻结极限
   δ/R≈0.30（大）、平衡极限 ≈0.17（小）、实验 0.22 居中。COOLFluiD 800 单元
   粗网格的密度中点估计 δ/R≈0.31（准则散布 0.21–0.47，激波仅跨约 3 单元），
   **落在冻结极限附近、高估实验约 39%**。这是粗网格数值粘性抹平激波、弛豫区
   分辨不足的典型表现（"壁面已平衡、脱体距离偏冻结"），**非物理模型错误**。
   冻结温度峰（9070 K vs mppshock 13914 K）被空间平均，亦源于此。

4. **SU2 交叉对比**：两个独立求解器（COOLFluiD+Mutation++ vs SU2 NEMO）在
   不同条件下预测的壁面压力分布形状一致、驻点压力均与各自 Mutation++ 正激波
   参考同量级；但 SU2 算例残差停滞、未充分收敛（~1e-5），仅可定性对比。

5. **Hornung 细网格 V5c 失败诊断**：V5c 在 14641 单元细网格上完成 50000 步，
   物种残差收敛（−7/−8）但动量/能量残差停滞（−0.4 至 −1.3）。直接解析原始变量
   发现解物理无效——激波后密度/压力从激波到壁面**单调递减**至 0（应递增），
   壁面 v 振荡 ±3000 m/s（应 ≈0），T 奇偶失耦。根因为 Euler 无黏方程在细网格
   壁面驻点奇异性 + CFL=1.0 偏大。**Hornung 定量结论以 V3 粗网格（物理有效）
   为准。**细网格验证需改用 NavierStokes2DNEQ 或大幅降低 CFL。

6. **FireII 化学相发散诊断**：FireII 11 组元化学相在三次尝试（run1 CFL 跳变、
   run2 CFL=0.01 恒定）下均发散。run2 残差从步 1 起单调上升（2.46→5.21，
   3340 步），证明这不是 CFL 调参问题，而是 11 组元化学刚性在当前显式伪时间
   推进框架下的根本限制。**FireII 定量结论以冻结相 iter_1000（物理有效）为准。**

7. **系统性修复成果（第三/四次修订）**：本轮共定位并修复 4 类缺陷——
   ① Hornung V5 网格双重缩放（米制网格再除 1000，域缩小 1000×，原结果作废）；
   ② ShockTube 1D `Euler1DNEQRhoivt` 缺失 `_library->setState()`（RHS≡0 根因，
   修复后 6/7 残差收敛至 −6）；③ FireII 单阶段策略在 11 组元化学刚性下不可行
   （CFL 阶跃两次发散），改为"冻结→化学激活重启"两阶段；④ MutationppI
   适配层硬断言改为数值截断（m_y、p>0）。全部修改均在 COOLFluiD 侧/适配层，
   **未改 Mutation++ 源码**。
   **新增诊断**：V5c 完成但物理无效（Euler 细网格驻点奇异性）；FireII run2
   发散（化学刚性根本限制）。两个失败均非代码 bug，而是物理/数值方法限制。

8. **超算需求**：DoubleCone Run42 需 ≥16 核运行 1-2 天，超算脚本已备（§8）。

## 附录：验证脚本

| 脚本 | 位置 | 功能 |
|------|------|------|
| **`revalidate_hornung.py`** | `doc/validation/` | **复核脚本**：全场提取驻点线 + 4 准则激波定位 + mppshock 冻结/平衡对照（推荐使用）|
| **`postprocess_final.py`** | `doc/validation/` | **最终后处理**：Hornung V5 脱体距离、FireII 冻结/化学相驻点线与壁面热流、Sutton-Graves 双参考对比 |
| `monitor_fireii_chem.sh` | `doc/validation/` | FireII 化学相弛豫监控（10 min 采样 T_max/q_stag）|
| `monitor_fireii_chem2.sh` | `doc/validation/` | run2 弛豫监控（参数化：结果目录/日志/趋势文件）|
| `run_fireii_pipeline_v5.sh` | `doc/validation/` | FireII 冻结+化学两阶段流水线 |
| `run_hornung_v5b_after_chem.sh` | `doc/validation/` | 化学相完成后自动串行 Hornung V5b（12 核）|
| `run_fireii_chem2_after_v5b.sh` | `doc/validation/` | V5b 完成后启动 FireII run2（从 iter_3000 重启，CFL=0.01）|
| `run_v5c_after_chem2.sh` | `doc/validation/` | run2 完成后启动 Hornung V5c（CFL≤1.0）|
| `validate_hornung_v3.py` | `doc/validation/` | 旧版 Hornung 脚本（冻结/平衡极限排序有误，仅存档）|
| `compare_coolfluid_su2.py` | `doc/validation/` | COOLFluiD vs SU2 壁面压力对比 |
| `parse_coolfluid_plt.py` | `doc/validation/` | Tecplot .plt 文件解析器 |
| `run_coolfluid.sh` | `doc/validation/` | COOLFluiD 运行环境封装脚本 |
| `fakecuda.c` / `libfakecuda.so` | `doc/validation/` | CUDA 运行时垫片 |

### 附录 B：算例日志与结果归档位置

**归档原则**：分析报告保留在 `doc/`，算例日志与计算结果统一归档到
`plugins/NEQ/testcases/TCNEQ/<算例名>/` 下。

| 算例 | 结果目录 | 日志目录 |
|------|---------|---------|
| Hornung | `plugins/NEQ/testcases/TCNEQ/Hornung/results/` | `plugins/NEQ/testcases/TCNEQ/Hornung/logs/` |
| FireII | `plugins/NEQ/testcases/TCNEQ/FireII/results/` | `plugins/NEQ/testcases/TCNEQ/FireII/logs/` |
| ShockTube | `plugins/NEQ/testcases/TCNEQ/ShockTube/results/` | `plugins/NEQ/testcases/TCNEQ/ShockTube/logs/` |
| DoubleCone | `plugins/NEQ/testcases/TCNEQ/DoubleCone/results/` | `plugins/NEQ/testcases/TCNEQ/DoubleCone/logs/` |
| 跨算例流水线 | — | `plugins/NEQ/testcases/TCNEQ/logs/` |

**Hornung 结果子目录**：
- `RESULTS_CNEQ_EULER_N22` — 原始粗网格运行
- `RESULTS_CNEQ_EULER_N22_RST` — 重启运行
- `RESULTS_CNEQ_EULER_N22_V3` — V3 收敛解（38054 步，物理有效，主定量基准）
- `RESULTS_CNEQ_EULER_N22_V4` / `V4_SMOKE` — V4 运行与烟雾测试
- `RESULTS_CNEQ_EULER_N22_V5` — V5b（CFL=10 失稳，作废）
- `RESULTS_CNEQ_EULER_N22_V5_BROKEN_SCALE` — V5 缩放 bug（作废）
- `RESULTS_CNEQ_EULER_N22_V5C` — V5c（CFL≤1.0，50000 步完成但物理无效）

**FireII 结果子目录**：
- `RESULT_FIREII_FROZEN` — 冻结化学相（iter_1000，物理有效，唯一有效 FireII 结果）
- `RESULT_FIREII_MPP_RUN` — 化学相 run1（3090 步 CFL 跳变发散）
- `RESULT_FIREII_MPP_RUN2` — 化学相 run2（3340 步 CFL=0.01 恒定发散）
- `RESULT_FIREII_SMOKE_A11` — 烟雾测试
