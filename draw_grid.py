import matplotlib.pyplot as plt
import numpy as np

def plot_accuracy(ax, config, show_legend=False):
    """
    绘制单个子图的准确率曲线。
    
    参数:
    - ax: 子图对象。
    - config: 配置字典，包括 accuracies, times, colors, markers, labels 等信息。
    - show_legend: 是否显示图例。
    """
    # 绘制每一条线
    for i, (accuracy, color, marker, label) in enumerate(zip(config['accuracies'], config['colors'], config['markers'], config['labels'])):
        linestyle = '--' if i == 1 or i == 3 else '-'
        ax.plot(config['times'], accuracy, marker=marker, color=color, label=label, linewidth=1.5, linestyle=linestyle)

    # 显示图例
    if show_legend:
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2), ncol=3, handletextpad=0.5, borderaxespad=0.5)

    # 设置子图属性
    ax.set_xlabel('Eavesdropping Duration(s)')
    ax.set_ylabel(f"Accuracy in {config['scenario']} Scenario")
    ax.set_xticks(config['times'])
    ax.set_yticks(np.linspace(0, 1, 11))
    ax.set_ylim(0, 1)
    ax.grid(True, linestyle='--', linewidth=1.0, color='gray')

def plot_multiple_accuracies(scenario_configs):
    """
    绘制多个垂直排列的准确率子图。

    参数:
    - scenario_configs: 子图配置的列表，每个配置是一个字典，包含 accuracies, times, colors, markers, labels, scenario 和 show_legend 等信息。
    """
    num_plots = len(scenario_configs)
    fig, axs = plt.subplots(num_plots, 1, figsize=(5, 4 * num_plots), sharex=False) #sharex=True可以所有图共用X轴的刻度值

    # 处理单个子图的情况
    if num_plots == 1:
        axs = [axs]

    # 绘制每个子图
    for ax, config in zip(axs, scenario_configs):
        plot_accuracy(ax, config, show_legend=config.get('show_legend', False))

    # 调整子图间的间距
    plt.tight_layout()

    # 保存图形
    plt.savefig(r'data/multi_comp_group_vertical.pdf', bbox_inches='tight')
    plt.show()

def plot_grid_accuracies(scenario_configs, ncols=2):
    """
    绘制一个网格排列的子图，可以指定每行显示的子图数。

    参数:
    - scenario_configs: 子图配置的列表，每个配置是一个字典，包含 accuracies, times, colors, markers, labels, scenario 和 show_legend 等信息。
    - ncols: 每行的子图数量。
    """
    num_plots = len(scenario_configs)
    nrows = (num_plots + ncols - 1) // ncols  # 计算需要的行数

    fig, axs = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows), squeeze=False)

    for i, config in enumerate(scenario_configs):
        row = i // ncols
        col = i % ncols
        ax = axs[row][col]
        
        # 绘制当前配置的子图
        plot_accuracy(ax, config, show_legend=config.get('show_legend', False))

        # 仅为最底行的子图设置 x 轴标签
        if row == nrows - 1:
            ax.set_xlabel('Eavesdropping Duration(s)')

    # 删除多余的空子图
    for j in range(num_plots, nrows * ncols):
        fig.delaxes(axs[j // ncols][j % ncols])

    # 调整子图间的间距
    plt.tight_layout()

    # 保存图形
    plt.savefig(r'data/multi_comp_group_grid.pdf', bbox_inches='tight')
    plt.show()




############################绘图参数##################################
# x 轴的时间数据
times = [20, 40, 60, 80, 100, 120, 140, 160, 180]
# 准确率数据
accuracies = [
    [0.02, 0.06, 0.13, 0.14, 0.15, 0.16, 0.163, 0.166, 0.17],  # wu
    [0.31, 0.79, 0.87, 0.88, 0.89, 0.90, 0.91, 0.91, 0.92],  # wu+fs
    [0.02, 0.04, 0.07, 0.078, 0.085, 0.09, 0.094, 0.097, 0.10],  # zhang
    [0.17, 0.47, 0.68, 0.72, 0.78, 0.82, 0.83, 0.84, 0.86],  # zhang+fs
    [0.11, 0.34, 0.50, 0.64, 0.78, 0.87, 0.92, 0.93, 0.94],  # bae
    [0.38, 0.91, 0.97, 0.973, 0.974, 0.975, 0.978, 0.98, 0.985],  # our
]
# 自定义颜色和图例
colors = ['#9467bd', '#9467bd', 'g', 'g', 'orange', '#d62728']
markers = ['s', 's', '^', '^', 'D', 'o']
labels = ['Zhao', 'fs+Zhao', 'RoVIA', 'fs+RoVIA', 'Bae', 'Anya']

# 子图配置，一个配置一张图
scenario_configs = [
    {
        'times': times,
        'accuracies': accuracies,
        'colors': colors,
        'markers': markers,
        'labels': labels,
        'scenario': 'Ideal',
        'show_legend': True
    },
    {
        'times': times,
        'accuracies': accuracies,
        'colors': colors,
        'markers': markers,
        'labels': labels,
        'scenario': 'Weak',
        'show_legend': False
    },
]
############################绘制多个子图##################################
plot_multiple_accuracies(scenario_configs)
plot_grid_accuracies(scenario_configs)