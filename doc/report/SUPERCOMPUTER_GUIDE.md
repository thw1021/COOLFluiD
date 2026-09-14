# COOLFluiD 高焓算例超算运行指南

目的：在超算上完成三个高焓非平衡流动算例的验证计算（本地 2 核限额不够的量），
对比 Lani 2009 博士论文（CUBRC 双锥 Run 42 实验数据）与 FIRE II 文献结果，
验证 COOLFluiD + Mutation++（外部接口调用，未改 M++ 源码）求解器正确性。

本指南随 COOLFluiD 源码树走——把整个源码目录（排除 `build/`/`install/`/`.git/`）
拷到超算即可。各算例目录自包含：CFcase + 网格 + SLURM 脚本 + 后处理脚本。

## 上传与执行

```bash
# 1) 上传 COOLFluiD 源码树（排除 build/install/.git）
rsync -a --exclude build --exclude install --exclude .git \
  /home/tang/packages/COOLFluiD user@supercomputer:~/

# 2) 超算上先跑预检（~15 min @4 核）：
cd ~/COOLFluiD/plugins/NEQ/testcases/TCNEQ/Hornung
sbatch slurm_hornung.sh          # walltime 1 h；日志 hornung_slurm.log

# 3) 预检通过后（残差 -3.0 + 脱体距离 0.209 R + 峰值 T≈9800 K），并行提交：
cd ../DoubleCone/Run42_N2
sbatch slurm_dcone.sh            # walltime 48 h；日志 dcone_slurm.log
cd ../FireII
sbatch slurm_fireii.sh           # walltime 24 h；日志 fireii_slurm.log
```

**前置**：COOLFluiD 与 Mutation++ 已在超算上构建完成（`build/optim/apps/Solver/coolfluid-solver` 存在），
`mpirun` / Mutation++ 库路径已在 `PATH`/`LD_LIBRARY_PATH` 中（由超算 `~/.bashrc` 或 module 加载）。
SLURM 脚本通过 `source ~/.bashrc` 继承环境，自动定位源码根并调 `coolfluid-solver`。
如超算 `#SBATCH --partition=normal` 不适用，改脚本头的 `--partition` 一行即可。

---

## 一、待运行算例总览

| # | 算例 | 物理模型 | 网格 | 参考目标（通过判据） | SLURM 脚本 | 资源 |
|---|------|----------|------|---------------------|------------|------|
| 0 | **Hornung HEG 圆柱**（预检） | Euler + N₂ 化学非平衡（n2_2, ChemNonEq1T） | 800 四边形 | 收敛残差 **-3.00009**；激波脱体 **0.209 R**（±0.01）；激波后峰值 T≈9800 K | `slurm_hornung.sh` | 4 核 1 h |
| 1 | **CUBRC 双锥 Run 42**（主验证） | NS 轴对称 + N₂ 两温 TCNEQ（n2_2, ChemNonEqTTv） | 65280 三角形 | 壁面压力/热流 vs 实验：25°锥平台 P≈9–10 kPa，交接峰 P≈45–50 kPa @x≈0.105 m，再附着峰 q≈(4–6)×10⁵ W/m²；残差目标 -5.5（老求解器参考 -5.84） | `slurm_dcone.sh` | 16 核 48 h |
| 2 | **FIRE II t=1643 s** | NS 轴对称 + 11 组元空气 CNEQ 1T（air_11, ChemNonEq1T） | ~16 万三角形 | 残差 -4.0（内置 Mutation2 老算例参考 -4.0033）；驻点热流 ~10⁶ W/m² 量级；激波层 N/O 解离与 NO 分层合理 | `slurm_fireii.sh` | 32 核 24 h |

执行顺序：**先 0（预检，软件栈正确性证明），后 1、2（可并行提交）**。

---

## 二、目录清单

每个算例目录自包含，含运行所需全部输入文件：

```
plugins/NEQ/testcases/TCNEQ/
├── Hornung/                       预检算例
│   ├── slurm_hornung.sh           #SBATCH 4 核 1 h
│   ├── hornung_FVM_NS_CNEQ_EULER_n2_2_V3.CFcase   求解器配置
│   ├── coarse.CFmesh              网格（800 四边形，米制×1000 缩放）
│   └── script/
│       └── postprocess_hornung.py  驻点线提取 + 脱体距离计算
│
├── DoubleCone/Run42_N2/           主验证算例
│   ├── slurm_dcone.sh             #SBATCH 16 核 48 h
│   ├── DConeN2_42_FVM_M++.CFcase  求解器配置（M++ n2_2, ChemNonEqTTv）
│   ├── DConeN2_B.CFmesh           网格（65280 三角形）
│   ├── DConeFVM.inter             交互参数（CFL / limiter / 梯度阶）
│   └── script/
│       ├── postprocess_run42.py    壁面 P/q 对比图
│       └── exp_run42_digitized.dat CUBRC LENS I 实验数字化数据
│
└── FireII/                        FIRE II 再入算例
    ├── slurm_fireii.sh            #SBATCH 32 核 24 h
    ├── fire2_1643s_CNEQ_Mpp.CFcase 求解器配置（M++ air_11, ChemNonEq1T）
    ├── fire2_small80x.CFmesh      网格（~16 万三角形，μm 制×1e6 缩放）
    └── fire2.inter               交互参数（CFL / limiter / 梯度阶）
```

---

## 三、结果判读

### Hornung 预检

```bash
cd plugins/NEQ/testcases/TCNEQ/Hornung
python3 script/postprocess_hornung.py RESULTS_CNEQ_EULER_N22_V3/HornungN2.CFmesh
```
核对三项：残差 -3.00009、脱体距离 0.209 R、峰值 T≈9800 K。**通过才继续生产算例**。

### 双锥 Run 42（主验证，vs 实验）

```bash
python3 plugins/NEQ/testcases/TCNEQ/DoubleCone/Run42_N2/script/postprocess_run42.py \
  plugins/NEQ/testcases/TCNEQ/DoubleCone/Run42_N2/RESULTS_Dcone_TCNEQ_MPP
```
自动输出关键指标 + 对比图 `dcone_wall_comparison.png`（红=计算，蓝方块=实验数字化点）。
判读标准（来自论文图 6.18a/6.19a）：

| 量 | 实验参考 | 计算应落在 |
|----|----------|-----------|
| 25° 锥压力平台（x=0.055–0.09 m） | ~9.5–10.6 kPa | ±15% 内 |
| 锥-锥交接压力峰（x≈0.105 m） | ~40.5 kPa（峰值位置） | 45–50 kPa，位置 ±0.005 m |
| 再附着热流峰（x≈0.105–0.11 m） | ~5.1×10⁵ W/m² | (4–6)×10⁵ W/m² |
| 第二锥热流平台（x≈0.13 m） | ~1.5×10⁵ W/m² | ±30% 内 |

注：计算曲线在交接区会出现比实验点更尖的峰值（网格分辨率效应，论文中 COOLFluiD
CRD/Nompelis FVM 同样如此），对比看平台值与峰位置而非峰值绝对一致。

### FIRE II

跑完检查：`RESULT_FIREII_MPP_A11_A11/` 下壁面热流文件与流场 plt；
驻点热流量级、激波脱体距离、NO 峰值层位置。与老版（内置 Mutation2）同算例
参考残差 -4.0033 对齐收敛深度后，两者流场应定性一致（M++ 用 NASA-9/RRHO 与
老库数据源略有差别，允许小百分比差异）。

---

## 四、排障速查（全部为本地实际踩过的坑）

1. **启动即 `GeometricEntityRegister ... Assertion failed`**：
   CFcase 的 `Simulator.Modules.Libs` 首位必须有 `libShapeFunctions`（三个算例已加，勿删）。
2. **并行读网格 `PMPI_Allreduce` abort**：ParMETIS 与 MPI 不一致 → 自建 ParMETIS（确保链接的 MPI 与 `mpirun` 一致）。
3. **`CudaDeviceManager` 断言/`CUDA error`**：构建必须 `withcuda = 0`（`coolfluid.conf` 已设）。
4. **日志里大量 `NoSuchValueException ... provider not found`**：是被捕获的兜底噪声（Identity 回退），不影响运行。
5. **`Unused User Configuration Arguments` 警告**：无害。
6. **`CorrectedDerivative2D ... nbNodes() == 4 Assertion`**：MeFiAlgo 网格拟合与三角形网格冲突，算例中已禁用（标着 DISABLED-MeFiAlgo 的注释块），勿恢复。
7. **Mutation++ 报 `file: mixtures/xxx.xml not found`**：环境缺 `MPP_DIRECTORY`/`MPP_DATA_DIRECTORY`（在 `~/.bashrc` 或 SLURM 脚本中 `export` 这两个变量）。
8. **想要更快收敛/改收敛深度**：改 CFcase 里 `Norm.valueNorm` 一行即可（双锥 -5.5→-5.0 省 30%+ 时间；热流对比建议不浅于 -5.0）。
9. **不要用 mppshock 做健康检查**：低密度工况它会挂起（M++ 工具层问题，与库物理无关）；用 checkmix/mppequil。
10. **作业被杀重启**：本代码树不支持从存档 CFmesh 重启（读存档会触发未实现虚函数）。提交前把 walltime 留足；中断后只能从头跑。

---

## 五、跑完之后

1. 拷回结果：双锥 `RESULTS_Dcone_TCNEQ_MPP/`（重点 `DConeFVM_heat.plt-P0Side0` 与 `convergence.plt-P0.Default`）、FireII `RESULT_FIREII_MPP_A11_A11/`、预检 `HornungN2.CFmesh`。
2. 本地 `python3 plugins/NEQ/testcases/TCNEQ/DoubleCone/Run42_N2/script/postprocess_run42.py <结果目录>` 出对比图，交回给出最终验证报告。
3. 记录每个算例的：残差历史末值、达到步数、总核时——写入报告。
