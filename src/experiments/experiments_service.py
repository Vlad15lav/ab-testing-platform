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
    sample_size - размер групп
    """
    statistical_test: str = 'ttest'
    effect: float
    alpha: float = 0.05
    beta: float = 0.1
    sample_size: int


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

    def _create_group_generator(self, metrics, sample_size, n_iter):
        """Генератор случайных групп.

        :param metrics (pd.DataFame): таблица с метриками,
            columns=['user_id', 'metric'].
        :param sample_size (int): размер групп
            (количество пользователей в группе).
        :param n_iter (int): количество итераций генерирования случайных групп.
        :return (np.array, np.array): два массива со значениями
            метрик в группах.
        """
        user_ids = metrics['user_id'].unique()
        for _ in range(n_iter):
            a_user_ids, b_user_ids = np.random.choice(user_ids,
                                                      (2, sample_size),
                                                      False)
            a_metric_values = metrics.loc[metrics['user_id'].isin(a_user_ids),
                                          'metric'].values
            b_metric_values = metrics.loc[metrics['user_id'].isin(b_user_ids),
                                          'metric'].values
            yield a_metric_values, b_metric_values

    def _estimate_errors(self, group_generator, design, effect_add_type):
        """Оцениваем вероятности ошибок I и II рода.

        :param group_generator: генератор значений метрик для двух групп.
        :param design (Design): объект с данными, описывающий
            параметры эксперимента.
        :param effect_add_type (str): способ добавления эффекта для группы B.
            - 'all_const' - увеличить всем значениям в группе B на константу
                (b_metric_values.mean() * effect / 100).
            - 'all_percent' - увеличить всем значениям в группе B
                в (1 + effect / 100) раз.
        :return pvalues_aa (list[float]), pvalues_ab (list[float]),
            first_type_error (float), second_type_error (float):
            - pvalues_aa, pvalues_ab - списки со значениями pvalue
            - first_type_error, second_type_error - оценки вероятностей
                ошибок I и II рода.
        """
        pvalues_aa, pvalues_ab = [], []
        effect = design.effect
        alpha = design.alpha

        for a_matric, b_metric in group_generator:
            b_metric_mean = b_metric.mean()
            pvalue_aa = self.get_pvalue(a_matric, b_metric, design)

            if effect_add_type == 'all_const':
                b_metric += b_metric_mean * effect / 100
            elif effect_add_type == 'all_percent':
                b_metric *= (1 + effect / 100)
            else:
                raise ValueError('Неверный effect_add_type')

            pvalue_ab = self.get_pvalue(a_matric, b_metric, design)

            pvalues_aa.append(pvalue_aa)
            pvalues_ab.append(pvalue_ab)

        first_type_error = np.mean(np.array(pvalues_aa) < alpha)
        second_type_error = np.mean(np.array(pvalues_ab) >= alpha)

        return pvalues_aa, pvalues_ab, first_type_error, second_type_error

    def estimate_errors(self, metrics, design, effect_add_type, n_iter):
        """Оцениваем вероятности ошибок I и II рода.

        :param metrics (pd.DataFame): таблица с метриками,
            columns=['user_id', 'metric'].
        :param design (Design): объект с данными, описывающий
            параметры эксперимента.
        :param effect_add_type (str): способ добавления эффекта для группы B.
            - 'all_const' - увеличить всем значениям в группе B на константу
                (b_metric_values.mean() * effect / 100).
            - 'all_percent' - увеличить всем значениям в группе B
                в (1 + effect / 100) раз.
        :param n_iter (int): количество итераций генерирования случайных групп.
        :return pvalues_aa (list[float]), pvalues_ab (list[float]),
            first_type_error (float), second_type_error (float):
            - pvalues_aa, pvalues_ab - списки со значениями pvalue
            - first_type_error, second_type_error - оценки вероятностей
                ошибок I и II рода.
        """
        group_generator = self._create_group_generator(metrics,
                                                       design.sample_size,
                                                       n_iter)
        return self._estimate_errors(group_generator, design, effect_add_type)


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
    # metrics = pd.DataFrame({
    #     'user_id': [str(i) for i in range(10)],
    #     'metric': [i for i in range(10)]
    # })
    # design = Design(
    #     statistical_test='ttest',
    #     alpha=0.05,
    #     beta=0.1,
    #     effect=3.
    # )
    # ideal_sample_size = 9513

    # experiments_service = ExperimentsService()
    # sample_size = experiments_service.estimate_sample_size(metrics, design)
    # print(sample_size)
    # assert sample_size == ideal_sample_size, 'Неверно'
    # print('simple test passed')

    # Test for estimate alpha and beta error
    _a = np.array([1., 2, 3, 4, 5])
    _b = np.array([1., 2, 3, 4, 10])
    group_generator = ([a, b] for a, b in ((_a, _b),))
    design = Design(effect=50., sample_size=5)
    effect_add_type = 'all_percent'

    ideal_pvalues_aa = [0.579584]
    ideal_pvalues_ab = [0.260024]
    ideal_first_type_error = 0.
    ideal_second_type_error = 1.

    experiments_service = ExperimentsService()
    pvalues_aa, pvalues_ab, first_type_error, second_type_error = \
        experiments_service._estimate_errors(group_generator,
                                             design, effect_add_type)
    np.testing.assert_almost_equal(ideal_pvalues_aa, pvalues_aa, decimal=4)
    np.testing.assert_almost_equal(ideal_pvalues_ab, pvalues_ab, decimal=4)
    assert ideal_first_type_error == first_type_error
    assert ideal_second_type_error == second_type_error
    print('simple test passed')
