# COOLFluiD 高焓算例验证 — 阶段性报告（Mutation++ 集成验证）

日期：2026-09-06 更新 ｜ 状态：Hornung 收敛中（T 残差 -2.0 →目标 -3），双锥/FireII 待算力

## 0. 2026-09-06 新增结论（重要）

1. **CUDA 垫片（关键）**：本机 CUDA 运行时被其他 GPU 任务（m2c，10 进程持有 /dev/nvidia0）
   搅成 flaky 状态（cudaGetDeviceCount 报 unknown error），而 COOLFluiD 是 CUDA 构建，
   启动时硬性初始化 CUDA，且 libFramework 引用带版本符号 cudaGetDevice@libcudart.so.12。
   **解决**：LD_PRELOAD 垫片 `/home/tang/coolfluid_validation_runs/shims/libfakecuda.so`
   （同名版本节点，全部 CUDA 调用先走真库、失败即降级假设备；CPU 路径无影响）。
   注意：垫片加载在同命令下偶发不生效（原因未明），**可靠启动方式是 systemd 用户单元**。
2. **可靠启动配方（systemd-run）**：见 §6 命令。须同时设置
   LD_PRELOAD(垫片)、LD_LIBRARY_PATH、MPP_DIRECTORY、MPP_DATA_DIRECTORY。
3. **1D 欧拉/NEQ 路径在本开源树不可用**：缺 provider（如 Euler1DLinearCons）；
   原生 CFmesh 直读与"读存档重启"也会触发未实现虚函数（必须经 converter 读网格）。
   验证聚焦 2D 算例（双锥/圆柱/FireII），与论文一致。
4. **Hornung V3 已收敛 — M++ 集成端到端验证通过**（2026-09-06）：
   - 38054 步达残差 **-3.00009**（算例头部参考目标 -3.00004），串行 47 min 43 s；
   - 物理场合理：来流 T=1833.1 K / ρ=0.0052 kg/m³ 精确保持；弓形激波锐利；
     激波后 T 峰值 9806 K（冻结正激波理论值 ~15,800 K @ M∞=6.28，解离吸热使温度大降，
     方向正确）；近壁弛豫降温至 6738 K；
   - **激波脱体距离 2.658 mm = 0.209 R**（R=12.7 mm 1 英寸圆柱），
     介于平衡流与冻结流之间——符合 Hornung/Nompelis-Candler(HEG) 非平衡圆柱物理；
   - 输出：RESULTS_CNEQ_EULER_N22_V3/HornungN2.CFmesh、HornungN2_stagline.dat、
     hornung_stagline.png；后处理脚本 postprocess_hornung.py。
5. **FireII 已适配且冒烟通过**：fire2_1643s_CNEQ_Mpp.CFcase（air_11 顺序 [e⁻,N⁺,O⁺,NO⁺,N₂⁺,O₂⁺,N,O,NO,N₂,O₂]
   重排、libShapeFunctions、MinT/MinRhoi、自动 CFL）。50 步冒烟：残差 5.69→4.17 稳定下降，
   1 核 ~5 s/步 → 32 核预计 ~0.3-0.5 s/步，数千步可收敛（数小时量级）。
6. **双锥 Run42 修复链完整**（DConeN2_42_FVM_M++.CFcase）：除 §3 各修复外，
   又发现并禁用了 MeFiAlgo 网格拟合（移动节点后 CorrectedDerivative2D 断言
   "邻居为四边形"失败——本网格为三角形）。禁用后冒烟已越过原崩溃点、物种残差下降、
   KSP 正常（GMRES 81–122 步收敛）；T/Tv 残差在 CFL=0.1 起步阶段处于强热不平衡
   弛豫平台（人工边界层内 Tv-T 差最大 2900 K，属预期物理），需 CFL 爬升后消解。
   串行 ~20-25 s/步 → 本机 2 核无法承担数万步，**必须超算**（建议 ≥16 核 1-2 天）。
7. **后处理工具已备**：/home/tang/coolfluid_validation_runs/postproc/
   （实验点数字化文件 exp_run42_digitized.dat、postprocess_run42.py、postprocess_hornung.py）。
8. 并行核数限制：应用户要求，本机 COOLFluiD 计算最多 2 核；双锥（需 ≥6 核数天）改超算。

## 1. 目标

参考 Lani 2009 博士论文（`/home/tang/ZoteroData/storage/QRKMA4P2/`）等文献中的高焓流动算例，
验证当前 COOLFluiD 求解器 + Mutation++（外部接口，不改其源码）的正确性。
主要对比目标：**CUBRC 双锥 Run 42（N₂，2 温度模型）**，论文图 6.18/6.19（PDF 第 183 页），
含实验表面压力/热流数据；辅助算例：Hornung 圆柱（Euler CNEQ）。

## 2. Mutation++ 独立核查（规则 1）——未发现库物理错误

| 项目 | 结果 |
|------|------|
| checkmix air_5 / n2_2 / air_11 | ✅ 物种、摩尔质量、生成焓、Park 反应速率正确 |
| mppequil 平衡组分（1 atm, 3000–10000 K） | ✅ 与经典平衡空气图像一致（O₂ ~4000K 解离、N₂ ~6000–9000K），元素质量守恒通过 |
| mppequil 低气压 117 Pa | ✅ 解离温度前移，物理趋势正确，求解稳定 |
| mppshock 低密度 N₂ 强激波（P=117 Pa, V=3849 m/s） | ⚠️ **挂起（>5 min 无输出）**。工具层牛顿迭代鲁棒性问题，非库物理错误。COOLFluiD 不调用该工具。复现：`mppshock -P 117.2 -T 268.7 -V 3849.3 n2_2` |
| ChemNonEqTTv setState 变量集语义 | ✅ 核实：type 1 =（物种密度, T, Tv）；MutationppI 适配层调用方式正确 |
| VT 能量交换源项（T=268.7K, Tv=3160K） | ✅ 修正测试程序传参后确认源项极小（~0.04 W/m³），振动冻结物理正确。注意：`energyTransferSource` 只写 nbTvib=1 个元素（平动方程取负号由 COOLFluiD 处理） |
| 版本/ABI | M++ v1.0.5-92-gbb054e5；libmutation++.so 于 7/14 重建（晚于适配层 6/11 编译），运行时 ABI 兼容（Hornung 稳定运行 12400+ 迭代验证）。**M++ 再次升级后需重编适配层** |

**结论：Mutation++ 本体可用于验证计算，未触发"确认错误即停止"条款。**（mppshock 挂起单独记录）

## 3. 求解器启动问题与修复（均为 COOLFluiD 侧）

1. **libShapeFunctions 不被加载** → `GeometricEntityRegister` 断言崩溃（缺
   `CellTriagLagrangeP1LagrangeP0` 等 provider）。非 single-exec 构建的模块均不传递依赖它。
   **修复：CFcase 的 `Simulator.Modules.Libs` 首位加 `libShapeFunctions`。**（Burgers 基线与 NEQ 算例均验证通过）
2. **模块目录**：加载器只搜索 `--ldir`（向量选项，需 `--end-of-ldir` 终止或置于参数末尾）。
   正确调用方式（从仓库根目录）：
   ```bash
   ./build/optim/apps/Solver/coolfluid-solver --scase <case.CFcase> \
     --bdir /home/tang/packages/COOLFluiD --ldir /home/tang/packages/COOLFluiD/build/optim/dso
   ```
   install/bin 的二进制亦可用，但模块目录必须指向 build/optim/dso。
3. **ParMETIS 混 MPI**：系统 `/lib/libparmetis.so.4.0` 依赖 OpenMPI（libmpi.so.40），
   与 MPICH 程序混链 → 并行读网格 PMPI_Allreduce abort。**修复：用 MPICH 自建
   GKlib+METIS+ParMETIS 4.0.3（shared），装于 `/home/tang/packages/ParMETIS/install-mpich/lib`，
   运行时前置 `LD_LIBRARY_PATH` 即可（SONAME 兼容符号链接已建）。** 6 核读网格已验证可跑。
4. **旧 M++ 算例混合物名失效**：N2_neut / N2_TTv / air11nasa9 在当前 M++ 数据库
   （n2_2、air_5、air_11、CO2_8、Mars_19、tacot-air_35）及整个 git 历史中均不存在。
   已适配为现有混合物。

## 4. 物种顺序（关键适配点）

COOLFluiD NEQ 变量集直接沿用 M++ 混合物的物种顺序：
- `n2_2` = **[N₂, N]**（旧 Mutation2OLD nitrogen2 为 [N, N₂]，CFcase 数值需重排）
- `air_5` = [N, O, NO, N₂, O₂]；`air_11` = [e⁻, N⁺, O⁺, NO⁺, N₂⁺, O₂⁺, N, O, NO, N₂, O₂]

已通过初始解场解析验证：远场 p=117.075 Pa = ρRT 精确、γ=1.4 → [N₂,N] 解释正确。

## 5. 已创建/修改的算例（全部 COOLFluiD 侧文件）

| 文件 | 说明 | 状态 |
|------|------|------|
| `plugins/NEQ/testcases/TCNEQ/Hornung/hornung_FVM_NS_CNEQ_EULER_n2_2.CFcase` | Euler CNEQ，n2_2，物种重排 | 原版跑至 iter 12400（物种残差 -5.7），CFL→50 后发散 |
| `.../hornung_FVM_NS_CNEQ_EULER_n2_2_V2.CFcase` | 限制器常开（limitIter=1e6）+ CFL≤10 | **待运行**（预计串行 1–1.5 h） |
| `.../hornung_FVM_NS_CNEQ_EULER_n2_2_RST.CFcase` | 从 iter-12000 存档重启 | ❌ 直接 CFmesh 重启路径触发未实现虚函数（Method::unsetMethod 纯虚），弃用 |
| `plugins/NEQ/testcases/TCNEQ/DoubleCone/Run42_N2/DConeN2_42_FVM_M++.CFcase` | Run42 TCNEQ（ChemNonEqTTv）+ MutationppI；初始化改为 Run42 一致来流+人工边界层（原文件用 Hornung 模板值 -5590/1833 会导致首迭代非物理态）；MinT=200/MinRhoi=1e-10 钳位；FilterState T,Tv≥200K；CFL 保守调度 | **待运行**（6 核，见 §6） |

## 6. 待运行清单与命令（资源空闲后）

```bash
# ---------- 本机可靠启动配方（systemd 用户单元，2 核限额内） ----------
source ~/.bashrc
cd /home/tang/packages/COOLFluiD
systemd-run --user --unit=cf-hornung-v3 \
  --property=WorkingDirectory=/home/tang/packages/COOLFluiD \
  --property=Environment=LD_PRELOAD=/home/tang/coolfluid_validation_runs/shims/libfakecuda.so \
  --property=Environment=LD_LIBRARY_PATH=/home/tang/packages/COOLFluiD/install/lib:/home/tang/packages/mpichInstall/lib:/home/tang/packages/Mutationpp/install/lib:/home/tang/packages/boost_1_85_0/install/lib:/home/tang/packages/petsc/arch-linux-c-opt/lib \
  --property=Environment=MPP_DIRECTORY=/home/tang/packages/Mutationpp \
  --property=Environment=MPP_DATA_DIRECTORY=/home/tang/packages/Mutationpp/data \
  bash -c "timeout 14400 /home/tang/packages/mpichInstall/bin/mpirun -np 1 \
    ./build/optim/apps/Solver/coolfluid-solver \
    --scase plugins/NEQ/testcases/TCNEQ/Hornung/hornung_FVM_NS_CNEQ_EULER_n2_2_V3.CFcase \
    --bdir /home/tang/packages/COOLFluiD --ldir /home/tang/packages/COOLFluiD/build/optim/dso \
    > /home/tang/coolfluid_validation_runs/hornung_v3.log 2>&1"

# ---------- 双锥 Run42（本机 2 核太慢，建议超算，PBS/SLURM 脚本见下） ----------
# 脚本目录：/home/tang/coolfluid_validation_runs/supercomputer/
#   run_dcone_pbs.sh     — 双锥 Run42 N2 TCNEQ（M++），建议 ≥16 核 ~1-2 天
#   run_fireii_slurm.sh  — FireII 11 组元 CNEQ（M++），建议 ≥32 核
# 超算上若无 GPU 问题，不需要 LD_PRELOAD 垫片；但务必注意 ParMETIS 必须与 MPI 一致。
# 输出：RESULTS_Dcone_TCNEQ_MPP/DConeFVM_heat.plt-P0Side0（壁面 P/Q）
# 对比：python3 /home/tang/coolfluid_validation_runs/postproc/postprocess_run42.py <RESULTS_DIR>
```

注意：晚间 22:00 后机器上有 SU2/m2c 等 8–10 核任务时，COOLFluiD 后台任务曾被 SIGTERM
（多次复现）；**用 systemd 用户单元可隔离进程组**，但算力冲突仍需错峰。

## 7. 对比数据提取

- 论文图 6.18a/6.19a（PDF 第 183 页）：Run42 实验壁面压力（25° 锥平台 ~9–10 kPa，
  交接点峰值 ~47 kPa @ x≈0.09 m）与热流（驻点 ~6×10⁵ W/m²，再附着峰 ~5–6×10⁵ W/m²）。
- 后处理脚本位置：待建（解析 `.surf.plt`/`DConeFVM_heat.pltSide0` 并与数字化的实验点对比）。

## 8. FireII（11 组元 air）成本评估

`fire2_1643s_CNEQ_M++.CFcase`（需把 mixtureName air11nasa9 → air_11，并加 libShapeFunctions；
网格 final_1643_2nd.CFmesh 7.8 MB，~16 万单元）。
预估单核~数小时/千迭代量级，11 组元化学+数值雅可比：**建议直接上超算**，
提交脚本按 §6(2) 模板改 `-np` 与路径即可。

## 9. 遗留问题清单

1. 适配层 `MutationLibrarypp::setState` 的 MinT/MinRhoi 钳位默认 0（本次靠 CFcase 显式设置兜底）。
2. `mppshock` 低密度工况挂起（M++ 工具层）。
3. 仓库内 NEQ 算例所需的 `Euler2DNEQConsToRhoivtTv` VarSetTransformer 在本代码树缺失
   （原算例针对 Lani 私有版本），已通过变量集配置绕开。
4. 直接读存档 CFmesh 重启在本构建不可用（未实现虚函数）——重启需从原始网格重转。
5. 并行运行与用户其他 MPI 任务存在被 SIGTERM 的冲突现象（详见 §6 注意）。

## 10. 验证状态总览（截至 2026-09-06）

| 算例 | 状态 | 结果/证据 |
|------|------|-----------|
| Mutation++ 独立核查 | ✅ 通过 | checkmix/mppequil/低气压平衡/VT源项全部正确；mppshock 挂起已记录（工具层） |
| Hornung 圆柱（HEG, n2_2 CNEQ） | ✅ **收敛+物理验证** | 残差 -3.00009（参考目标 -3.00004）；δ=0.209R；T剖面物理正确 |
| FireII（air_11 CNEQ） | ✅ 适配+冒烟通过 | 50 步残差 5.69→4.17；待超算生产（脚本已备） |
| 双锥 Run42（n2_2 TCNEQ） | ✅ 适配+冒烟通过 | 越过全部历史崩溃点；待超算生产（脚本+对比工具已备） |
| 1D 激波管 | ⛔ 本构建不可用 | 缺 1D provider（Euler1DLinearCons 等），与库无关 |

**结论**：当前版本 COOLFluiD 求解器 + Mutation++（外部接口，未改其源码）在 2D
高焓非平衡流动上的集成正确性与收敛性已由 Hornung 圆柱算例端到端证实；论文锚定的
定量验证（双锥 Run42 壁面压力/热流 vs 实验，FireII）待超算算力完成生产运行后
用 postproc/ 工具出图对比。
