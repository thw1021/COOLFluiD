# COOLFluiD 高焓算例超算运行指南

目的：在超算上完成三个高焓非平衡流动算例的验证计算（本地 2 核限额不够的量），
对比 Lani 2009 博士论文（CUBRC 双锥 Run 42 实验数据）与 FIRE II 文献结果，
验证 COOLFluiD + Mutation++（外部接口调用，未改 M++ 源码）求解器正确性。

本指南与全部脚本随 COOLFluiD 源码树走（把整个源码目录拷到超算即可）。布局：

| 路径（相对源码根） | 内容 |
|------|------|
| `SUPERCOMPUTER_GUIDE.md` | 本指南 |
| `coolfluid.conf.supercomputer` | 超算构建配置模板（TODO 标注待填路径） |
| `check_env.sh` | 环境体检 |
| `01_build_mutationpp.sh` / `02_build_parmetis.sh` / `03_build_coolfluid.sh` | 依赖与主程序构建 |
| `run_dcone_pbs.sh` / `run_fireii_slurm.sh` | 生产算例作业脚本（按调度器改编提交） |
| `postproc/` | 实验数据数字化文件 + 对比绘图脚本 |
| Mutation++ 源码需另行拷贝（本机 /home/tang/packages/Mutationpp，排除 .git/build/install） |

**三个算例的就地运行脚本**（推荐，自动定位源码根与环境）：
- `plugins/NEQ/testcases/TCNEQ/Hornung/run_on_supercomputer.sh`
- `plugins/NEQ/testcases/TCNEQ/DoubleCone/Run42_N2/run_on_supercomputer.sh`
- `plugins/NEQ/testcases/TCNEQ/FireII/run_on_supercomputer.sh`

用法统一为 `./run_on_supercomputer.sh [NP]`（NP=核数，默认值见脚本头注释）。
日志写在各自算例文件夹内；结果目录也落在算例文件夹内，方便整目录拷回。

---

## 一、待运行算例总览

| # | 算例 | 物理模型 | 网格 | 参考目标（通过判据） | 预估规模 |
|---|------|----------|------|---------------------|----------|
| 0 | **Hornung HEG 圆柱**（预检） | Euler + N₂ 化学非平衡（n2_2, ChemNonEq1T） | 800 四边形 | 收敛残差 **-3.00009**；激波脱体 **0.209 R**（±0.01）；激波后峰值 T≈9800 K | 4 核 ~15 分钟（本地串行 48 分钟） |
| 1 | **CUBRC 双锥 Run 42**（主验证） | NS 轴对称 + N₂ 两温 TCNEQ（n2_2, ChemNonEqTTv） | 65280 三角形 | 壁面压力/热流 vs 实验：25°锥平台 P≈9–10 kPa，交接峰 P≈45–50 kPa @x≈0.105 m，再附着峰 q≈(4–6)×10⁵ W/m²；残差目标 -5.5（老求解器参考 -5.84） | 16 核 1–2 天 |
| 2 | **FIRE II t=1643 s** | NS 轴对称 + 11 组元空气 CNEQ 1T（air_11, ChemNonEq1T） | ~16 万三角形 | 残差 -4.0（内置 Mutation2 老算例参考 -4.0033）；驻点热流 ~10⁶ W/m² 量级；激波层 N/O 解离与 NO 分层合理 | 32 核 数小时 |

执行顺序：**先 0（预检，软件栈正确性证明），后 1、2（可并行提交）**。

---

## 二、部署步骤

### 0. 传输

```bash
# 源码树（本目录，排除 build/install/.git）+ Mutation++ 源码
rsync -a --exclude build --exclude install --exclude .git \
  /home/tang/packages/COOLFluiD user@supercomputer:~/
rsync -a --exclude .git --exclude build --exclude install \
  /home/tang/packages/Mutationpp user@supercomputer:~/
ssh user@supercomputer
cd ~/COOLFluiD
```

### 1. 加载环境、体检

```bash
module load compiler mpi petsc   # 按超算习惯；确保 MPI全家桶一致
bash check_env.sh
```
体检要点：mpicc/mpirun 是**同一个 MPI 实现**；Boost ≥ 1.85；Eigen3 存在；
ParMETIS 检查输出若显示 OpenMPI 版（libmpi.so.40）而集群默认是别的 MPI → 必须执行第 3 步自建。

### 2. 构建 Mutation++

```bash
./01_build_mutationpp.sh ~/Mutationpp ~/Mutationpp/install
source env.supercomputer.sh   # 生成的环境片段（之后每个新终端/作业都要 source）
```
自检自动跑 checkmix（n2_2/air_5/air_11 必须通过）。

### 3. 自建 ParMETIS（若体检发现 MPI 不一致；断网集群先在本地克隆三个仓库打包带上去）

```bash
./02_build_parmetis.sh $(which mpicc) $PWD/parmetis-install
```

### 4. 构建 COOLFluiD

```bash
cp coolfluid.conf.supercomputer coolfluid.conf
vi coolfluid.conf                # 填全部 TODO 路径；withcuda 保持 0
./03_build_coolfluid.sh $PWD     # 在源码根运行
```
构建脚本最后自动跑完美气体 Burgers 基线（通过才算构建成功）。
若编译报错，对照包内 `COOLFluiD/INSTALL_NOTES.md`（源码兼容性修复已含在本树中，正常无需再改）。

### 5. 预检算例（必跑）

```bash
cd plugins/NEQ/testcases/TCNEQ/Hornung
./run_on_supercomputer.sh 4
# 收敛后（就地）：
python3 ~/COOLFluiD/postproc/postprocess_hornung.py RESULTS_CNEQ_EULER_N22_V3/HornungN2.CFmesh
```
核对三项：残差 -3.00009、脱体距离 0.209 R、峰值 T≈9800 K。**通过才继续**。

### 6. 生产算例

```bash
# 就地运行（推荐）：
cd plugins/NEQ/testcases/TCNEQ/DoubleCone/Run42_N2 && ./run_on_supercomputer.sh 16
cd ../FireII && ./run_on_supercomputer.sh 32
# 或走调度器：改根目录 run_dcone_pbs.sh / run_fireii_slurm.sh 里的 CF 路径后 qsub/sbatch
```

---

## 三、结果判读

### 双锥 Run 42（主验证，vs 实验）

```bash
python3 postproc/postprocess_run42.py plugins/NEQ/testcases/TCNEQ/DoubleCone/Run42_N2/RESULTS_Dcone_TCNEQ_MPP
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

跑完检查：`RESULT_FIREII_MPP_A11/` 下壁面热流文件与流场 plt；
驻点热流量级、激波脱体距离、NO 峰值层位置。与老版（内置 Mutation2）同算例
参考残差 -4.0033 对齐收敛深度后，两者流场应定性一致（M++ 用 NASA-9/RRHO 与
老库数据源略有差别，允许小百分比差异）。

---

## 四、排障速查（全部为本地实际踩过的坑）

1. **启动即 `GeometricEntityRegister ... Assertion failed`**：
   CFcase 的 `Simulator.Modules.Libs` 首位必须有 `libShapeFunctions`（三个算例已加，勿删）。
2. **并行读网格 `PMPI_Allreduce` abort**：ParMETIS 与 MPI 不一致 → 用 `02_build_parmetis.sh` 自建。
3. **`CudaDeviceManager` 断言/`CUDA error`**：构建必须 `withcuda = 0`（模板已设）。
4. **日志里大量 `NoSuchValueException ... provider not found`**：是被捕获的兜底噪声（Identity 回退），不影响运行。
5. **`Unused User Configuration Arguments` 警告**：无害。
6. **`CorrectedDerivative2D ... nbNodes() == 4 Assertion`**：MeFiAlgo 网格拟合与三角形网格冲突，算例中已禁用（标着 DISABLED-MeFiAlgo 的注释块），勿恢复。
7. **Mutation++ 报 `file: mixtures/xxx.xml not found`**：环境缺 `MPP_DIRECTORY`/`MPP_DATA_DIRECTORY`（source env.supercomputer.sh）。
8. **想要更快收敛/改收敛深度**：改 CFcase 里 `Norm.valueNorm` 一行即可（双锥 -5.5→-5.0 省 30%+ 时间；热流对比建议不浅于 -5.0）。
9. **不要用 mppshock 做健康检查**：低密度工况它会挂起（M++ 工具层问题，与库物理无关）；用 checkmix/mppequil。
10. **作业被杀重启**：本代码树不支持从存档 CFmesh 重启（读存档会触发未实现虚函数）。提交前把 walltime 留足；中断后只能从头跑。

---

## 五、跑完之后

1. 拷回结果：双锥 `RESULTS_Dcone_TCNEQ_MPP/`（重点 `DConeFVM_heat.plt-P0Side0` 与 `convergence.plt-P0.Default`）、FireII `RESULT_FIREII_MPP_A11/`、预检 `HornungN2.CFmesh`。
2. 本地 `python3 postproc/postprocess_run42.py <结果目录>` 出对比图，交回给出最终验证报告。
3. 记录每个算例的：残差历史末值、达到步数、总核时——写入报告。
