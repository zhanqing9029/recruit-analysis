# -*- coding: utf-8 -*-
"""
大数据招聘岗位数据集（recruit_clean.csv）可视化脚本
============================================================
产出 4 张图表，对应作品集《大数据岗位招聘数据洞察》的四个分析动作：

    图 1  技能需求热度榜        —— 10 项技能在 JD 中的覆盖率，回答"先学什么"
    图 2  岗位技能要求数量分布  —— 一份 JD 要求几项技能，回答"学到多宽"
    图 3  技能共现热力图        —— 技能之间的绑定强度，回答"怎么组合"
    图 4  薪资维度体检          —— 薪资与经验/岗位的关系，回答"哪些结论可信"

运行方式：
    python recruit_viz.py [csv路径]
默认读取桌面上的 recruit_clean.csv，图片输出到 ../assets/charts/

依赖：pandas / numpy / matplotlib
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")          # 无界面后端，保证在脚本/服务器环境中也能出图
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter

# ============================================================
# 一、全局中文与样式设置
# ============================================================
# 关键点：matplotlib 默认字体不含中文，必须显式指定中文字体，
# 并关闭 unicode_minus，否则负号会显示成方块。
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "Noto Sans SC", "SimHei", "Arial Unicode MS"],
    "font.family": "sans-serif",
    "axes.unicode_minus": False,          # 正常显示负号
    "figure.dpi": 200,                    # 显示与输出清晰度
    "savefig.dpi": 200,
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "axes.edgecolor": "#D8DEE4",
    "axes.linewidth": 0.9,
    "text.color": "#16212B",
    "axes.labelcolor": "#39434D",
    "xtick.color": "#5C6874",
    "ytick.color": "#5C6874",
    "font.size": 11,
})

# 统一配色：一个主色 + 一个强调色，避免彩虹色干扰阅读
INK        = "#16212B"   # 主文字
SUB        = "#6B7885"   # 次要文字
ACCENT     = "#2F6F8F"   # 主色（深青蓝）
ACCENT_LT  = "#D9E6ED"   # 主色浅版
HIGHLIGHT  = "#C1694A"   # 强调色（陶土红），只用于"要读者注意的那一个元素"
GRID       = "#E9EDF1"

# 数据集中的技能字段（13 个字段里有 3 个在全部 29,999 条记录中均为 0）
SKILL_COLS = [
    "skill_Python", "skill_SQL", "skill_Hadoop", "skill_Hive", "skill_Spark",
    "skill_Flink", "skill_MySQL", "skill_机器学习", "skill_数据仓库",
    "skill_Linux", "skill_Java", "skill_Excel", "skill_BI",
]
# 展示用中文名（去掉 skill_ 前缀，便于图表阅读）
SKILL_LABEL = {c: c.replace("skill_", "") for c in SKILL_COLS}


def tidy_axes(ax, grid_axis="y"):
    """统一坐标轴风格：去掉上/右边框，只保留浅色网格。"""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.9, zorder=0)
    ax.set_axisbelow(True)


def add_header(ax, title, subtitle):
    """标题 + 副标题：副标题用 axes 坐标定位，避让标题的 pad 空间。"""
    ax.set_title(title, fontsize=15.5, fontweight="bold", color=INK,
                 loc="left", pad=36)
    ax.text(0.0, 1.028, subtitle, transform=ax.transAxes,
            fontsize=10, color=SUB, ha="left", va="bottom")


def add_caption(fig, lines, y=0.012):
    """在图底部加数据来源/口径说明，作品集里显得严谨。"""
    fig.text(0.011, y, "\n".join(lines), ha="left", va="bottom",
             fontsize=8.2, color="#8A96A2", linespacing=1.7)


def save(fig, path, caption_lines):
    add_caption(fig, caption_lines)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.3, facecolor="white")
    plt.close(fig)
    print(f"[OK] 已输出 {path}")


# ============================================================
# 二、图 1：技能需求热度榜（横向条形图）
# ============================================================
def chart_skill_demand(df, out_dir):
    """
    图表类型：横向条形图（Horizontal Bar）
    Y 轴：技能名称（按覆盖率降序，自上而下）
    X 轴：要求该技能的职位占比（%）
    业务意义：一眼看出"哪些技能是入场券、哪些只是加分项"，
             为"先学什么"的结论提供依据。
    """
    valid = [c for c in SKILL_COLS if df[c].sum() > 0]
    zero = [c for c in SKILL_COLS if df[c].sum() == 0]

    rate = (df[valid].mean() * 100).sort_values(ascending=True)   # 升序画横条，最高的落在顶部
    labels = [SKILL_LABEL[c] for c in rate.index]
    values = rate.values

    fig, ax = plt.subplots(figsize=(9.4, 5.9))
    # SQL 用强调色，其余用主色：视觉上只让读者记住一个数字
    colors = [HIGHLIGHT if v == values.max() else ACCENT for v in values]
    bars = ax.barh(labels, values, color=colors, height=0.62, zorder=3)

    # 数值标签直接标在条形末端，省掉读者对刻度
    for bar, v in zip(bars, values):
        ax.text(v + 1.1, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}%", va="center", ha="left",
                fontsize=10.5, color=INK, fontweight="bold")

    # 基准线：帮助读者看出"35% 是这批技能的基准水位"
    baseline = float(np.mean(values[values < values.max()]))
    ax.axvline(baseline, color=SUB, linestyle=(0, (4, 3)), linewidth=1.1, zorder=2)
    ax.text(baseline + 0.9, len(labels) - 0.55,
            f"其余技能基准水位 {baseline:.1f}%", fontsize=9, color=SUB)

    ax.set_xlim(0, 70)
    ax.set_ylim(-0.7, len(labels) - 0.25)
    ax.set_xlabel("要求该技能的职位占比（%，n = 29,999）", labelpad=9)

    add_header(ax,
               "SQL 是唯一的高频硬技能，其余 9 项几乎等概率",
               "技能覆盖率排名 · 大数据类岗位 JD 文本解析结果 · 标注线为扣除 SQL 后的均值")

    tidy_axes(ax, grid_axis="x")
    ax.tick_params(axis="y", length=0, labelsize=11)
    ax.tick_params(axis="x", length=0)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0f}%"))
    fig.subplots_adjust(bottom=0.19)

    # 3 个零覆盖字段单独说明：这是数据缺口，不能解读成市场结论
    zero_txt = "、".join(SKILL_LABEL[c] for c in zero)
    save(fig, os.path.join(out_dir, "01_skill_demand.png"), [
        "数据来源：recruit_clean.csv（29,999 条清洗后职位记录）｜指标：技能字段取值为 1 的职位占比",
        f"注：{zero_txt} 三个技能字段在全部记录中均为 0，属采集缺口，不可解读为“市场无需求”",
    ])


# ============================================================
# 三、图 2：岗位技能要求数量分布（柱状图）
# ============================================================
def chart_skill_count(df, out_dir):
    """
    图表类型：柱状图（Bar Chart）+ 区间高亮带
    X 轴：单个岗位要求的技能项数（2 ~ 6 项）
    Y 轴：该技能项数对应的职位占比（%），柱顶同时标注职位数量
    业务意义：回答"简历该铺多宽"——几项技能是主流、继续堆技能是否有额外收益。
    """
    valid = [c for c in SKILL_COLS if df[c].sum() > 0]
    cnt = df[valid].sum(axis=1)

    dist = cnt.value_counts().sort_index()
    share = dist / dist.sum() * 100
    cum = share.cumsum()

    fig, ax = plt.subplots(figsize=(9.4, 5.8))

    # 高亮 2~5 项区间：这是 93% 岗位所在的区间
    ax.axvspan(1.55, 5.45, color="#F5F8FA", zorder=0)
    ax.text(3.5, 29.6, "2~5 项：93.0% 的岗位",
            ha="center", va="center", fontsize=9.8, color=SUB)

    median_cnt = int(cnt.median())
    colors = [HIGHLIGHT if i == median_cnt else ACCENT_LT for i in dist.index]
    bars = ax.bar(dist.index.astype(str), share.values, color=colors,
                  width=0.56, zorder=3)

    # 柱顶标占比，柱内标岗位数：比双 Y 轴更好读，也不会互相压字
    for bar, share_v, jobs, idx in zip(bars, share.values, dist.values, dist.index):
        is_key = (idx == median_cnt)
        ax.text(bar.get_x() + bar.get_width() / 2, share_v + 0.5,
                f"{share_v:.1f}%", ha="center", va="bottom",
                fontsize=11.5, color=INK, fontweight="bold")
        ax.text(bar.get_x() + bar.get_width() / 2, share_v * 0.5,
                f"{jobs:,}", ha="center", va="center",
                fontsize=9.2, color="white" if is_key else "#4A5A68")

    ax.set_ylim(0, 31.5)
    ax.set_xlim(-0.6, 5.6)
    ax.set_xlabel("单个岗位要求的技能项数", labelpad=9)
    ax.set_ylabel("职位占比（%）")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0f}%"))

    add_header(ax,
               "主流岗位要求 4 项技能，93% 的 JD 不超过 5 项",
               f"均值 {cnt.mean():.2f} 项 · 中位数 {median_cnt} 项 · "
               f"仅 7.0% 的岗位要求到 6 项")

    tidy_axes(ax, grid_axis="y")
    ax.tick_params(length=0)
    fig.subplots_adjust(bottom=0.19)

    save(fig, os.path.join(out_dir, "02_skill_count.png"), [
        "数据来源：recruit_clean.csv｜口径：13 个技能字段中有效 10 项，逐行求和得到每岗技能项数",
        f"累计口径：≤4 项 {cum.loc[4]:.1f}% ｜ ≤5 项 {cum.loc[5]:.1f}% ｜ 6 项 {share.loc[6]:.1f}%",
    ])


# ============================================================
# 四、图 3：技能共现热力图
# ============================================================
def chart_skill_cooccurrence(df, out_dir):
    """
    图表类型：热力图（Heatmap），带数值标注
    Y 轴：触发技能（该技能已在 JD 中出现）
    X 轴：条件技能（同时出现的技能）
    单元格：P(列技能 | 行技能) × 100%
    业务意义：找出"技能捆绑套餐"——哪些技能必须一起学、哪些互不相干。
             对角线置灰，避免 100% 自相关压缩色阶。
    """
    valid = [c for c in SKILL_COLS if df[c].sum() > 0]
    labels = [SKILL_LABEL[c] for c in valid]

    mat = np.zeros((len(valid), len(valid)))
    for i, a in enumerate(valid):
        sub = df[df[a] == 1]
        for j, b in enumerate(valid):
            mat[i, j] = sub[b].mean() * 100
    np.fill_diagonal(mat, np.nan)          # 对角线屏蔽

    fig, ax = plt.subplots(figsize=(9.6, 7.6))
    cmap = LinearSegmentedColormap.from_list(
        "demand", ["#F7F9FB", "#DCE9F0", "#9FC4D6", "#4E88A6", "#2F6F8F"])
    cmap.set_bad("#EDEFF2")               # 对角线（NaN）显示为浅灰

    im = ax.imshow(mat, cmap=cmap, vmin=28, vmax=62)

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=38, ha="right", fontsize=10)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("条件技能：该技能也同时出现", labelpad=10)
    ax.set_ylabel("触发技能：JD 中已出现该技能")

    # 数值标注：>50% 的格子用白字加粗，其余小字号，形成视觉层级
    for i in range(len(labels)):
        for j in range(len(labels)):
            if np.isnan(mat[i, j]):
                continue
            strong = mat[i, j] > 50
            ax.text(j, i, f"{mat[i, j]:.0f}", ha="center", va="center",
                    fontsize=9.4 if strong else 8.6,
                    color="white" if strong else "#39434D",
                    fontweight="bold" if strong else "normal")

    # 网格线让单元格边界更清楚
    ax.set_xticks(np.arange(-.5, len(labels), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(labels), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.6)
    ax.tick_params(which="both", length=0)

    cbar = fig.colorbar(im, ax=ax, fraction=0.036, pad=0.03)
    cbar.set_label("条件出现概率 P(列 | 行)（%）", fontsize=10)
    cbar.outline.set_visible(False)
    cbar.ax.tick_params(length=0, labelsize=9)

    # 把唯一显著的一组格子框出来（SQL 行→MySQL 列，及反向的 100%）
    i_sql, j_mysql = labels.index("SQL"), labels.index("MySQL")
    i_mysql, j_sql = j_mysql, i_sql
    for (r, c) in [(i_sql, j_mysql), (i_mysql, j_sql)]:
        ax.add_patch(plt.Rectangle((c - .5, r - .5), 1, 1, fill=False,
                                   edgecolor=HIGHLIGHT, linewidth=2.4, zorder=6))

    add_header(ax,
               "除 SQL 与 MySQL 外，10 项技能之间基本互不绑定",
               "红框：SQL→MySQL 60%、MySQL→SQL 100%｜其余 72 个格子稳定在 30.8%~32.8%，接近独立")
    fig.subplots_adjust(bottom=0.21)

    save(fig, os.path.join(out_dir, "03_skill_cooccurrence.png"), [
        "数据来源：recruit_clean.csv｜读法：第 i 行第 j 列 = 已要求行技能时，列技能同时出现的概率",
        "解读：MySQL 岗位 100% 要求 SQL，SQL 岗位 60% 要求 MySQL（基准 35%，提升 1.7 倍），二者实为同一技能栈",
    ])


# ============================================================
# 五、图 4：薪资维度体检（双面板箱线图）
# ============================================================
def chart_salary_check(df, out_dir):
    """
    图表类型：箱线图（Box Plot），左右双面板
    X 轴：左 = 工作经验分组；右 = 岗位名称分组
    Y 轴：月薪中位值 salary_avg（k/月）
    业务意义：不是"展示薪资差异"，而是验证"薪资维度能否支撑结论"。
             两组面板的四/五个箱子几乎完全重合 → 该字段不具备区分度，
             不能用于择业或谈薪判断。这是分析流程里必要的可信度检查。
    """
    exp_order = ["应届生", "1-3年", "3-5年", "5-10年"]
    job_order = ["数据专员", "数据运营", "数据分析工程师", "大数据运维", "大数据开发工程师"]

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 6.0), sharey=True,
                             gridspec_kw={"width_ratios": [1, 1.2], "wspace": 0.10})

    def draw(ax, groups, order, color, title, xlabel, rotate=0):
        names = [g for g in order if g in groups]
        data = [groups[g].dropna().values for g in names]
        bp = ax.boxplot(data, patch_artist=True, widths=0.55,
                        medianprops=dict(color=INK, linewidth=1.8),
                        whiskerprops=dict(color="#9AA7B4", linewidth=1),
                        capprops=dict(color="#9AA7B4", linewidth=1),
                        flierprops=dict(marker="o", markersize=2.6,
                                        markerfacecolor="#B8C3CE",
                                        markeredgecolor="none", alpha=0.55))
        for patch in bp["boxes"]:
            patch.set_facecolor(color)
            patch.set_edgecolor("#8FA3B0")
            patch.set_linewidth(0.9)
        ax.set_xticks(range(1, len(names) + 1))
        ax.set_xticklabels(names, fontsize=10.2, rotation=rotate,
                           ha="right" if rotate else "center")
        ax.set_title(title, fontsize=12, fontweight="bold", color=INK, loc="left", pad=10)
        ax.set_xlabel(xlabel, labelpad=8)
        ax.set_ylim(2, 30)
        tidy_axes(ax, grid_axis="y")
        ax.tick_params(length=0)
        # 标出各组中位数，让"几乎相等"这件事可以被读数验证
        for pos, arr in enumerate(data, start=1):
            ax.text(pos, np.median(arr) + 1.1, f"{np.median(arr):.1f}k",
                    ha="center", fontsize=9.2, color=INK, fontweight="bold")

    draw(axes[0], {g: d["salary_avg"] for g, d in df.groupby("工作经验")},
         exp_order, "#CFE0E9", "按工作经验：四个箱子几乎完全重合", "工作经验")

    draw(axes[1], {g: d["salary_avg"] for g, d in df.groupby("岗位名称")},
         job_order, "#E7D5CB", "按岗位名称：五组中位数集中在 16.5~17.0k", "岗位名称", rotate=24)

    axes[0].set_ylabel("月薪中位值（k）")
    axes[1].spines["left"].set_visible(False)

    # 整图标题用 fig 坐标定位，避免与两个子图的标题打架
    fig.text(0.011, 0.985, "薪资与经验、岗位均无解释力，该字段不适合承载结论",
             fontsize=15.5, fontweight="bold", color=INK, ha="left", va="top")
    fig.text(0.011, 0.928,
             "salary_avg 与经验 (r = −0.006)、学历 (r = −0.002) 相关性接近 0；"
             "五个岗位中位数 16.5~17.0k，组内标准差 6.1~6.2k",
             fontsize=10, color=SUB, ha="left", va="top")
    fig.subplots_adjust(top=0.79, bottom=0.21, left=0.075, right=0.985)

    save(fig, os.path.join(out_dir, "04_salary_check.png"), [
        "数据来源：recruit_clean.csv｜口径：salary_avg =（下限 + 上限）/ 2；箱体为 P25~P75，须为 1.5 IQR 内极值",
        "读法：若薪资随经验增长，四个箱子应呈阶梯状右移；实际四组中位数仅差 0.5k，说明该字段在本次数据中无信号",
    ])


# ============================================================
# 六、主流程
# ============================================================
def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\zhanqing\Desktop\recruit_clean.csv"
    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "assets", "charts"))
    os.makedirs(out_dir, exist_ok=True)

    # utf-8-sig 用于处理带 BOM 的中文表头
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    print(f"读取 {len(df):,} 条记录，{df.shape[1]} 个字段")

    chart_skill_demand(df, out_dir)
    chart_skill_count(df, out_dir)
    chart_skill_cooccurrence(df, out_dir)
    chart_salary_check(df, out_dir)


if __name__ == "__main__":
    main()
