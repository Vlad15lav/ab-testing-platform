import matplotlib.pyplot as plt
import seaborn as sns


def plot_pvalue_ecdf(pvalues, title=None):
    """Визуализация распределение pvalue экспериментов
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    if title:
        plt.suptitle(title)

    sns.histplot(pvalues, ax=ax1, bins=20, stat='density')
    ax1.plot([0, 1], [1, 1], 'k--')
    ax1.set(xlabel='p-value', ylabel='Density')

    sns.ecdfplot(pvalues, ax=ax2)
    ax2.plot([0, 1], [0, 1], 'k--')
    ax2.set(xlabel='p-value', ylabel='Probability')
    ax2.grid()

    return fig


def plot_error_rate(first_type_error,
                    second_type_error,
                    alpha,
                    beta):
    """Визуализация ошибки 1-го и 2-го рода для каждого эксперимента
    """
    count_pilots = len(first_type_error)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    axes[0].set_tittle('Alpha Error Rate')
    axes[1].set_tittle('Beta Error Rate')

    axes[0].hlines(alpha, 0, count_pilots, 'k', linestyles='--',
                   label=f'alpha={alpha}')
    axes[1].hlines(beta, 0, count_pilots, 'k', linestyles='--',
                   label=f'beta={beta}')

    axes[0].plot(first_type_error, '-o', alpha=0.7)
    axes[1].plot(second_type_error, '-o', alpha=0.7)

    return fig
