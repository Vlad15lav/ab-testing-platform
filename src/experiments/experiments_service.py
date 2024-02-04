import numpy as np
import pandas as pd

from pydantic import BaseModel
from scipy import stats


class Design(BaseModel):
    """Дата-класс с описание параметров эксперимента.

    statistical_test - тип статтеста. ['ttest']
    effect - размер эффекта в процентах
    alpha - уровень значимости
    beta - допустимая вероятность ошибки II рода
    """
    statistical_test: str
    effect: float
    alpha: float
    beta: float


class ExperimentsService:
    def get_pvalue(self, metrics_a_group, metrics_b_group, design):
        """Применяет статтест, возвращает pvalue.

        :param metrics_a_group (np.array): массив значений метрик группы A
        :param metrics_a_group (np.array): массив значений метрик группы B
        :param design (Design): объект с данными,
        описывающий параметры эксперимента
        :return (float): значение p-value
        """
        if design.statistical_test == 'ttest':
            pvalue = stats.ttest_ind(metrics_a_group, metrics_b_group).pvalue

            return round(pvalue, 4)
        else:
            raise ValueError('Неверный design.statistical_test')

    def estimate_sample_size(self, metrics, design):
        """Оцениваем необходимый размер выборки для проверки
        гипотезы о равенстве средних.

        Для метрик, у которых для одного пользователя одно значение просто
        вычислите размер групп по формуле.
        Для метрик, у которых для одного пользователя несколько значений
        (например, response_time),
        вычислите необходимый объём данных и разделите его на среднее
        количество значений на одного пользователя.
        Пример, если в таблице metrics 1000 наблюдений и 100 уникальных
        пользователей, и для эксперимента нужно
        302 наблюдения, то размер групп будет 31, тк в среднем на одного
        пользователя 10 наблюдений, то получится
        порядка 310 наблюдений в группе.

        :param metrics (pd.DataFrame): датафрейм со значениями
            метрик из MetricsService.
            columns=['user_id', 'metric']
        :param design (Design): объект с данными, описывающий
            параметры эксперимента
        :return (int): минимально необходимый размер групп
            (количество пользователей)
        """
        ration = metrics['user_id'].nunique() / len(metrics)

        alp_ppf = stats.norm.ppf(1 - design.alpha / 2)
        beta_ppf = stats.norm.ppf(1 - design.beta)
        z_score = (alp_ppf + beta_ppf) ** 2

        metric_mean = metrics['metric'].mean()
        metric_var = metrics['metric'].var(ddof=0)

        epsilon = metric_mean * (design.effect / 100)
        sample_size = ration * z_score * 2 * metric_var / (epsilon ** 2)

        return int(np.ceil(sample_size))


if __name__ == '__main__':
    # Test for get_pvalue method
    # metrics_a_group = np.array([964, 1123, 962, 1213, 914, 906,
    #                             951, 1033, 987, 1082])
    # metrics_b_group = np.array([952, 1064, 1091, 1079, 1158, 921,
    #                             1161, 1064, 819, 1065])
    # design = Design(statistical_test='ttest')
    # ideal_pvalue = 0.612219

    # experiments_service = ExperimentsService()
    # pvalue = experiments_service.get_pvalue(metrics_a_group,
    #                                         metrics_b_group,
    #                                         design)
    # np.testing.assert_almost_equal(ideal_pvalue, pvalue, decimal=4)
    # print('simple test passed')

    # Test for estimate_sample_size method
    metrics = pd.DataFrame({
        'user_id': [str(i) for i in range(10)],
        'metric': [i for i in range(10)]
    })
    design = Design(
        statistical_test='ttest',
        alpha=0.05,
        beta=0.1,
        effect=3.
    )
    ideal_sample_size = 9513

    experiments_service = ExperimentsService()
    sample_size = experiments_service.estimate_sample_size(metrics, design)
    print(sample_size)
    assert sample_size == ideal_sample_size, 'Неверно'
    print('simple test passed')
