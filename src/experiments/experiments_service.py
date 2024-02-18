import numpy as np
import pandas as pd

from pydantic import BaseModel
from scipy import stats
from stqdm import stqdm


class Design(BaseModel):
    """Дата-класс с описание параметров эксперимента.

    statistical_test - тип статтеста. ['ttest', 'utest', 'bootstrap']
    effect - размер эффекта в процентах
    alpha - уровень значимости
    beta - допустимая вероятность ошибки II рода
    bootstrap_iter - количество итераций бутстрепа
    bootstrap_ci_type - способ построения доверительного интервала.
        ['normal', 'percentile', 'pivotal']
    bootstrap_agg_func - метрика эксперимента. ['mean', 'quantile 95']
    stratification - постстратификация. 'on' - использовать постстратификация,
        'off - не использовать.
    """
    statistical_test: str = 'ttest'
    effect: float = 5
    alpha: float = 0.05
    beta: float = 0.1
    sample_size: int = 1000
    bootstrap_iter: int = 1000
    bootstrap_ci_type: str = 'normal'
    bootstrap_agg_func: str = 'mean'
    stratification: str = 'off'


class ExperimentsService:
    def get_pvalue(self, metrics_strat_a_group, metrics_strat_b_group, design):
        """Применяет статтест, возвращает pvalue.

        :param metrics_strat_a_group (np.ndarray): значения метрик истрат
            группы A.
            shape = (n, 2), первый столбец - метрики, второй столбец - страты.
        :param metrics_strat_b_group (np.ndarray): значения метрик и страт
            группы B.
            shape = (n, 2), первый столбец - метрики, второй столбец - страты.
        :param design (Design): объект с данными, описывающий параметры
            эксперимента
        :return (float): значение p-value
        """
        if design.statistical_test == 'ttest':
            if design.stratification == 'off':
                _, pvalue = stats.ttest_ind(metrics_strat_a_group,
                                            metrics_strat_b_group)
                return pvalue
            elif design.stratification == 'on':
                return self._ttest_strat(metrics_strat_a_group,
                                         metrics_strat_b_group)
            else:
                raise ValueError('Неверный design.stratification')
        elif design.statistical_test == 'utest':
            _, pvalue = stats.mannwhitneyu(metrics_strat_a_group,
                                           metrics_strat_b_group)
            return pvalue
        elif design.statistical_test == 'bootstrap':
            bootstrap_metrics, pe_metric = self._generate_bootstrap_metrics(
                metrics_strat_a_group,
                metrics_strat_b_group,
                design)
            _, pvalue = self._run_bootstrap(bootstrap_metrics,
                                            pe_metric,
                                            design)
            return pvalue
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
        for _ in stqdm(range(n_iter)):
            a_user_ids, b_user_ids = np.random.choice(user_ids,
                                                      (2, sample_size),
                                                      False)
            a_metric_values = metrics.loc[metrics['user_id'].isin(a_user_ids),
                                          'metric'].values.astype('float64')
            b_metric_values = metrics.loc[metrics['user_id'].isin(b_user_ids),
                                          'metric'].values.astype('float64')
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

    def _generate_bootstrap_metrics(self, data_one, data_two, design):
        """Генерирует значения метрики, полученные с помощью бутстрепа.

        :param data_one, data_two (np.array): значения метрик в группах.
        :param design (Design): объект с данными, описывающий
            параметры эксперимента
        :return bootstrap_metrics, pe_metric:
            bootstrap_metrics (np.array) - значения статистики теста
                псчитанное по бутстрепным подвыборкам
            pe_metric (float) - значение статистики теста посчитанное
                по исходным данным
        """
        bootstrap_data_one = np.random.choice(data_one,
                                              (len(data_one),
                                               design.bootstrap_iter))
        bootstrap_data_two = np.random.choice(data_two,
                                              (len(data_two),
                                               design.bootstrap_iter))
        if design.bootstrap_agg_func == 'mean':
            bootstrap_metrics = bootstrap_data_two.mean(axis=0) - \
                bootstrap_data_one.mean(axis=0)
            pe_metric = data_two.mean() - data_one.mean()
            return bootstrap_metrics, pe_metric
        elif design.bootstrap_agg_func == 'quantile 95':
            bootstrap_metrics = (
                np.quantile(bootstrap_data_two, 0.95, axis=0)
                - np.quantile(bootstrap_data_one, 0.95, axis=0)
            )
            pe_metric = np.quantile(data_two, 0.95) - np.quantile(data_one,
                                                                  0.95)
            return bootstrap_metrics, pe_metric
        else:
            raise ValueError('Неверное значение design.bootstrap_agg_func')

    @staticmethod
    def get_ci_bootstrap_normal(boot_metrics: np.array,
                                pe_metric: float,
                                alpha: float = 0.05):
        """Строит нормальный доверительный интервал.

        boot_metrics - значения метрики, полученные с помощью бутстрепа
        pe_metric - точечная оценка метрики
        alpha - уровень значимости

        return: (left, right) - границы доверительного интервала.
        """
        c = stats.norm.ppf(1 - alpha / 2)
        se = np.std(boot_metrics)
        left, right = pe_metric - c * se, pe_metric + c * se
        return left, right

    @staticmethod
    def get_ci_bootstrap_percentile(boot_metrics: np.array,
                                    pe_metric: float,
                                    alpha: float = 0.05):
        """Строит доверительный интервал на процентилях.

        boot_metrics - значения метрики, полученные с помощью бутстрепа
        pe_metric - точечная оценка метрики
        alpha - уровень значимости

        return: (left, right) - границы доверительного интервала.
        """
        left, right = np.quantile(boot_metrics, [alpha / 2, 1 - alpha / 2])
        return left, right

    @staticmethod
    def get_ci_bootstrap_pivotal(boot_metrics: np.array,
                                 pe_metric: float,
                                 alpha: float = 0.05):
        """Строит центральный доверительный интервал.

        boot_metrics - значения метрики, полученные с помощью бутстрепа
        pe_metric - точечная оценка метрики
        alpha - уровень значимости

        return: (left, right) - границы доверительного интервала.
        """
        right, left = 2 * pe_metric - np.quantile(boot_metrics,
                                                  [alpha / 2, 1 - alpha / 2])
        return left, right

    def _run_bootstrap(self, bootstrap_metrics, pe_metric, design):
        """Строит доверительный интервал и проверяет
        значимость отличий с помощью бутстрепа.

        :param bootstrap_metrics (np.array): статистика теста,
            посчитанная на бутстрепных выборках.
        :param pe_metric (float): значение статистики теста посчитанное
            по исходным данным.
        :return ci, pvalue:
            ci [float, float] - границы доверительного интервала
            pvalue (float) - 0 если есть статистически значимые отличия,
                иначе 1.
                Настоящее pvalue для произвольного способа построения
                доверительного интервала с помощью бутстрепа вычислить
                не тривиально.
                Поэтому мы будем использовать краевые значения 0 и 1.
        """
        if design.bootstrap_ci_type == 'normal':
            left, right = self.get_ci_bootstrap_normal(bootstrap_metrics,
                                                       pe_metric,
                                                       design.alpha)
        elif design.bootstrap_ci_type == 'percentile':
            left, right = self.get_ci_bootstrap_percentile(bootstrap_metrics,
                                                           pe_metric,
                                                           design.alpha)
        elif design.bootstrap_ci_type == 'pivotal':
            left, right = self.get_ci_bootstrap_pivotal(bootstrap_metrics,
                                                        pe_metric,
                                                        design.alpha)
        else:
            raise 'Wrong bootstrap_ci_type'

        ci = (left, right)
        pvalue = float(left < 0 < right)
        return ci, pvalue

    @staticmethod
    def _calc_strat_mean(df: pd.DataFrame, weights: pd.Series) -> float:
        """Считает стратифицированное среднее.

        :param df: датафрейм с целевой метрикой и данными для стратификации
        :param weights: маппинг {название страты: вес страты в популяции}
        """
        strat_mean = df.groupby('strat')['metric'].mean()
        return (strat_mean * weights).sum()

    @staticmethod
    def _calc_strat_var(df: pd.DataFrame, weights: pd.Series) -> float:
        """Считает стратифицированную дисперсию.

        :param df: датафрейм с целевой метрикой и данными для стратификации
        :param weights: маппинг {название страты: вес страты в популяции}
        """
        strat_var = df.groupby('strat')['metric'].var()
        return (strat_var * weights).sum()

    def _ttest_strat(self, metrics_strat_a_group, metrics_strat_b_group):
        """Применяет постстратификацию, возвращает pvalue.

        Веса страт считаем по данным обеих групп.
        Предполагаем, что эксперимент проводится на всей популяции.
        Веса страт нужно считать по данным всей популяции.

        :param metrics_strat_a_group (np.ndarray): значения метрик и
            страт группы A.
            shape = (n, 2), первый столбец - метрики, второй столбец - страты.
        :param metrics_strat_b_group (np.ndarray): значения метрик и
            страт группы B.
            shape = (n, 2), первый столбец - метрики, второй столбец - страты.
        :param design (Design): объект с данными, описывающий
            параметры эксперимента
        :return (float): значение p-value
        """
        weights = pd.Series(np.hstack((
            metrics_strat_a_group[:, 1],
            metrics_strat_b_group[:, 1])
            )).value_counts(normalize=True)
        a = pd.DataFrame(metrics_strat_a_group, columns=['metric', 'strat'])
        b = pd.DataFrame(metrics_strat_b_group, columns=['metric', 'strat'])

        a_strat_mean = self._calc_strat_mean(a, weights)
        b_strat_mean = self._calc_strat_mean(b, weights)

        a_strat_var = self._calc_strat_var(a, weights)
        b_strat_var = self._calc_strat_var(b, weights)

        delta = b_strat_mean - a_strat_mean
        std = (a_strat_var / len(a) + b_strat_var / len(b)) ** 0.5
        pvalue = 2 * (1 - stats.norm.cdf(np.abs(delta / std)))

        return pvalue


if __name__ == '__main__':
    # Test for get_pvalue method
    metrics_a_group = np.array([964, 1123, 962, 1213, 914, 906,
                                951, 1033, 987, 1082])
    metrics_b_group = np.array([952, 1064, 1091, 1079, 1158, 921,
                                1161, 1064, 819, 1065])
    design = Design(statistical_test='ttest')
    ideal_pvalue = 0.612219

    experiments_service = ExperimentsService()
    pvalue = experiments_service.get_pvalue(metrics_a_group,
                                            metrics_b_group,
                                            design)
    np.testing.assert_almost_equal(ideal_pvalue, pvalue, decimal=4)
    print('simple test passed')

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

    # Test for bootstrap
    bootstrap_metrics = np.arange(-490, 510)
    pe_metric = 5.
    design = Design(
        statistical_test='bootstrap',
        effect=5,
        bootstrap_ci_type='normal',
        bootstrap_agg_func='mean'
    )
    ideal_ci = (-560.79258, 570.79258)
    ideal_pvalue = 1.

    experiments_service = ExperimentsService()
    ci, pvalue = experiments_service._run_bootstrap(bootstrap_metrics,
                                                    pe_metric,
                                                    design)
    np.testing.assert_almost_equal(ideal_ci, ci, decimal=4,
                                   err_msg='Неверный доверительный интервал')
    assert ideal_pvalue == pvalue, 'Неверный pvalue'
    print('simple test passed')

    # Test for stratification
    metrics_strat_a_group = np.zeros((10, 2,))
    metrics_strat_a_group[:, 0] = np.arange(10)
    metrics_strat_a_group[:, 1] = (np.arange(10) < 4).astype(float)
    metrics_strat_b_group = np.zeros((10, 2,))
    metrics_strat_b_group[:, 0] = np.arange(1, 11)
    metrics_strat_b_group[:, 1] = (np.arange(10) < 5).astype(float)
    design = Design(stratification='on')
    ideal_pvalue = 0.037056

    experiments_service = ExperimentsService()
    pvalue = experiments_service.get_pvalue(metrics_strat_a_group,
                                            metrics_strat_b_group, design)

    np.testing.assert_almost_equal(ideal_pvalue, pvalue, decimal=4,
                                   err_msg='Неверное значение pvalue')
    print('simple test passed')
