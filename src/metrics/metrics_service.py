import numpy as np
import pandas as pd

from pydantic import BaseModel
from datetime import datetime
from datetime import timedelta


class DataService:
    def __init__(self, table_name_2_table):
        """Класс, предоставляющий доступ к сырым данным.

        :param table_name_2_table (dict[str, pd.DataFrame]):
            словарь таблиц с данными.
            Пример, {
                'sales': pd.DataFrame({'sale_id': ['123', ...], ...}),
                ...
            }
        """
        self.table_name_2_table = table_name_2_table

    def get_data_subset(
        self, table_name, begin_date, end_date, user_ids=None, columns=None
    ):
        """Возвращает подмножество данных.

        :param table_name (str): название таблицы с данными.
        :param begin_date (datetime.datetime): дата начала интервала с данными.
            Пример, df[df['date'] >= begin_date].
            Если None, то фильтровать не нужно.
        :param end_date (None, datetime.datetime): дата окончания интервала
            с данными.
            Пример, df[df['date'] < end_date].
            Если None, то фильтровать не нужно.
        :param user_ids (None, list[str]): список user_id, по которым нужно
            предоставить данные.
            Пример, df[df['user_id'].isin(user_ids)].
            Если None, то фильтровать по user_id не нужно.
        :param columns (None, list[str]): список названий столбцов, по которым
            нужно предоставить данные.
            Пример, df[columns].
            Если None, то фильтровать по columns не нужно.

        :return df (pd.DataFrame): датафрейм с подмножеством данных.
        """
        df = self.table_name_2_table[table_name]

        if begin_date:
            df = df[df['date'] >= begin_date]

        if end_date:
            df = df[df['date'] < end_date]

        if user_ids:
            df = df[df['user_id'].isin(user_ids)]

        if columns:
            df = df[columns]

        return df


class Design(BaseModel):
    """Дата-класс с описание параметров эксперимента.

    statistical_test - тип статтеста. ['ttest', 'bootstrap']
    effect - размер эффекта в процентах
    alpha - уровень значимости
    beta - допустимая вероятность ошибки II рода
    bootstrap_iter - количество итераций бутстрепа
    bootstrap_ci_type - способ построения доверительного интервала.
        ['normal', 'percentile', 'pivotal']
    bootstrap_agg_func - метрика эксперимента. ['mean', 'quantile 95']
    metric_name - название целевой метрики эксперимента
    metric_outlier_lower_bound - нижняя допустимая граница метрики,
        всё что ниже считаем выбросами
    metric_outlier_upper_bound - верхняя допустимая граница метрики,
        всё что выше считаем выбросами
    metric_outlier_process_type - способ обработки выбросов. ['drop', 'clip'].
        'drop' - удаляем измерение, 'clip' - заменяем выброс на значение
            ближайшей границы (lower_bound, upper_bound).
    """
    statistical_test: str = 'ttest'
    effect: float = 3.
    alpha: float = 0.05
    beta: float = 0.1
    bootstrap_iter: int = 1000
    bootstrap_ci_type: str = 'normal'
    bootstrap_agg_func: str = 'mean'
    metric_name: str
    metric_outlier_lower_bound: float
    metric_outlier_upper_bound: float
    metric_outlier_process_type: str


class MetricsService:
    def __init__(self, data_service=None):
        """Класс для вычисления метрик.

        :param data_service (DataService): объект класса,
        предоставляющий доступ к данным.
        """
        self.data_service = data_service

    def _get_data_subset(
        self,
        table_name,
        begin_date,
        end_date,
        user_ids=None,
        columns=None
    ):
        """Возвращает часть таблицы с данными."""
        return self.data_service.get_data_subset(table_name,
                                                 begin_date,
                                                 end_date,
                                                 user_ids,
                                                 columns)

    def _calculate_response_time(self, begin_date, end_date, user_ids):
        """Вычисляет значения времени обработки запроса сервером.

        :param begin_date, end_date (datetime): период времени, за который
        нужно считать значения.
        :param user_id (None, list[str]): id пользователей, по которым
        нужно отфильтровать полученные значения.

        :return (pd.DataFrame): датафрейм с двумя
        столбцами ['user_id', 'metric']
        """
        data_filter = self._get_data_subset(table_name='web-logs',
                                            begin_date=begin_date,
                                            end_date=end_date,
                                            user_ids=user_ids,
                                            columns=['user_id', 'load_time'])
        data_filter.rename(columns={'load_time': 'metric'}, inplace=True)
        return data_filter

    def _calculate_revenue_web(self, begin_date, end_date, user_ids):
        """Вычисляет значения выручки с пользователя за указанный период
        для заходивших на сайт в указанный период.

        Эти данные нужны для экспериментов на сайте, когда в эксперимент
        попадают только те, кто заходил на сайт.

        :param begin_date, end_date (datetime): период времени, за который
        нужно считать значения.
        Также за этот период времени нужно выбирать пользователей, которые
        заходили на сайт.
        :param user_id (None, list[str]): id пользователей, по которым нужно
        отфильтровать полученные значения.

        :return (pd.DataFrame): датафрейм с двумя
        столбцами ['user_id', 'metric']
        """
        web_logs_filter = self._get_data_subset(table_name='web-logs',
                                                begin_date=begin_date,
                                                end_date=end_date,
                                                user_ids=user_ids,
                                                columns=['user_id']
                                                ).drop_duplicates()

        sales_filte = self._get_data_subset(table_name='sales',
                                            begin_date=begin_date,
                                            end_date=end_date,
                                            user_ids=user_ids,
                                            columns=['user_id', 'price'])
        users_revenue = web_logs_filter.merge(right=sales_filte,
                                              on='user_id',
                                              how='left').fillna(0)

        users_revenue = users_revenue.groupby('user_id')['price'] \
            .sum().reset_index()
        return users_revenue.rename(columns={'price': 'metric'})

    def _calculate_revenue_all(self, begin_date, end_date, user_ids):
        """Вычисляет значения выручки с пользователя за указанный период
        для заходивших на сайт до end_date.

        Эти данные нужны, например, для экспериментов с рассылкой по email,
        когда в эксперимент попадают те, кто когда-либо оставил
        нам свои данные.

        :param begin_date, end_date (datetime): период времени, за который
        нужно считать значения.
        Нужно выбирать пользователей, которые хотя бы раз заходили на сайт
        до end_date.
        :param user_id (None, list[str]): id пользователей, по которым нужно
        отфильтровать полученные значения.

        :return (pd.DataFrame): датафрейм с двумя
        столбцами ['user_id', 'metric']
        """
        web_logs_filter = self._get_data_subset(table_name='web-logs',
                                                begin_date=None,
                                                end_date=end_date,
                                                user_ids=user_ids,
                                                columns=['user_id']
                                                ).drop_duplicates()

        sales_filte = self._get_data_subset(table_name='sales',
                                            begin_date=begin_date,
                                            end_date=end_date,
                                            user_ids=user_ids,
                                            columns=['user_id', 'price'])
        users_revenue = web_logs_filter.merge(right=sales_filte,
                                              on='user_id',
                                              how='left').fillna(0)

        users_revenue = users_revenue.groupby('user_id')['price'] \
            .sum().reset_index()

        return users_revenue.rename(columns={'price': 'metric'})

    @staticmethod
    def _calculate_theta_cuped(metric, metric_cov):
        """Считаем theta для CUPED

        :param metric (datetime): дата начала периода (включая границу)
        :param metric_cov (datetime): дата окончания периода
            (не включая границу)

        :return theta (float): theta значение CUPED
        """
        cov_matrix = np.cov((metric, metric_cov))[0][1]
        variance = metric_cov.var()
        return cov_matrix / variance

    def _calculate_revenue_cuped(self,
                                 begin_date,
                                 end_date,
                                 user_ids=None,
                                 days=7):
        """Считаем метрику CUPED

        :param begin_date (datetime): дата начала периода (включая границу)
        :param end_date (datetime): дата окончания периода (не включая границу)
        :param user_ids (list[str], None): список пользователей.
            Если None, то вычисляет метрику для всех пользователей.
        :param days (int): количество дней предэксперемента

        :return df: columns=['user_id', 'metric']
        """
        X_metric = self._calculate_revenue_web(
            begin_date=begin_date - timedelta(days=days),
            end_date=begin_date,
            user_ids=user_ids).rename(columns={'metric': 'cov'})
        Y_metric = self._calculate_revenue_web(
            begin_date=begin_date,
            end_date=end_date,
            user_ids=user_ids)
        if user_ids:
            df = pd.DataFrame({'user_id': user_ids})
        else:
            df = pd.concat((X_metric[['user_id']],
                            Y_metric[['user_id']])).drop_duplicates()

        df = df.merge(right=X_metric, how='left', on='user_id')
        df = df.merge(right=Y_metric, how='left', on='user_id').fillna(0)

        X_metric = df['cov'].values
        Y_metric = df['metric'].values

        theta = self._calculate_theta_cuped(Y_metric, X_metric)
        Y_cuped = Y_metric - theta * (X_metric - np.mean(X_metric))
        df['metric'] = Y_cuped

        return df[['user_id', 'metric']]

    def calculate_metric(self,
                         metric_name,
                         begin_date, end_date,
                         cuped='off',
                         user_ids=None):
        """Считает значения метрики.

        :param metric_name (str): название метрики
        :param begin_date (datetime): дата начала периода (включая границу)
        :param end_date (datetime): дата окончания периода (не включая границу)
        :param cuped (str): применение CUPED.
            ['off', 'on (previous week revenue)']
            'off' - не применять CUPED
            'on (previous week revenue)' - применяем CUPED,
                в качестве ковариаты используем выручку за прошлые 7 дней
        :param user_ids (list[str], None): список пользователей.
            Если None, то вычисляет метрику для всех пользователей.

        :return df: columns=['user_id', 'metric']
        """
        if metric_name == 'response time':
            return self._calculate_response_time(begin_date,
                                                 end_date,
                                                 user_ids)
        elif metric_name == 'revenue (web)':
            if cuped == 'off':
                return self._calculate_revenue_web(begin_date,
                                                   end_date,
                                                   user_ids)
            elif cuped == 'on (previous week revenue)':
                return self._calculate_revenue_cuped(begin_date,
                                                     end_date,
                                                     user_ids,
                                                     days=7)
            else:
                raise ValueError('Wrong cuped')
        elif metric_name == 'revenue (all)':
            return self._calculate_revenue_all(begin_date,
                                               end_date,
                                               user_ids)
        else:
            raise ValueError('Wrong metric name')

    def process_outliers(self, metrics, design):
        """Возвращает новый датафрейм с обработанными выбросами
        в измерениях метрики.

        :param metrics (pd.DataFrame): таблица со значениями метрики,
            columns=['user_id', 'metric'].
        :param design (Design): объект с данными, описывающий
            параметры эксперимента.
        :return df: columns=['user_id', 'metric']
        """
        process_type = design.metric_outlier_process_type
        lower_bound = design.metric_outlier_lower_bound
        upper_bound = design.metric_outlier_upper_bound
        metrics = metrics.copy()

        if process_type == 'drop':
            metrics = metrics[(metrics['metric'] >= lower_bound) &
                              (metrics['metric'] <= upper_bound)]
        elif process_type == 'clip':
            metrics[metrics['metric'] < lower_bound] = lower_bound
            metrics[metrics['metric'] > upper_bound] = upper_bound
        else:
            raise ValueError('Wrong metric outlier process type')

        return metrics


def _chech_df(df, df_ideal, sort_by, reindex=False,
              set_dtypes=False, decimal=None):
    assert isinstance(df, pd.DataFrame), 'Функция вернула не pd.DataFrame.'
    assert len(df) == len(df_ideal), 'Неверное количество строк.'
    assert len(df.T) == len(df_ideal.T), 'Неверное количество столбцов.'
    columns = df_ideal.columns
    assert df.columns.isin(columns).sum() == len(df.columns), \
        'Неверное название столбцов.'
    df = df[columns].sort_values(sort_by)
    df_ideal = df_ideal.sort_values(sort_by)
    if reindex:
        df_ideal.index = range(len(df_ideal))
        df.index = range(len(df))
    if set_dtypes:
        for column, dtype in df_ideal.dtypes.to_dict().items():
            df[column] = df[column].astype(dtype)
    if decimal:
        ideal_values = df_ideal.astype(float).values
        values = df.astype(float).values
        np.testing.assert_almost_equal(ideal_values, values, decimal=decimal)
    else:
        assert df_ideal.equals(df), \
            'Итоговый датафрейм не совпадает с верным результатом.'


if __name__ == '__main__':
    # Test for revenue metric
    df_sales = pd.DataFrame({
        'sale_id': [1, 2, 3],
        'date': [datetime(2022, 3, day, 11) for day in range(11, 14)],
        'price': [1100, 900, 1500],
        'user_id': ['1', '2', '1'],
    })
    df_web_logs = pd.DataFrame({
        'date': [datetime(2022, 3, day, 11) for day in range(10, 14)],
        'load_time': [80.8, 90.1, 15.8, 19.7],
        'user_id': ['3', '1', '2', '1'],
    })
    begin_date = datetime(2022, 3, 11, 9)
    end_date = datetime(2022, 4, 11, 9)

    ideal_response_time = pd.DataFrame({'user_id': ['1', '2', '1'],
                                        'metric': [90.1, 15.8, 19.7]})
    ideal_revenue_web = pd.DataFrame({'user_id': ['1', '2'],
                                      'metric': [2600., 900.]})
    ideal_revenue_all = pd.DataFrame({'user_id': ['1', '2', '3'],
                                      'metric': [2600., 900., 0.]})

    data_service = DataService({'sales': df_sales, 'web-logs': df_web_logs})
    metrics_service = MetricsService(data_service)

    df_response_time = metrics_service.calculate_metric('response time',
                                                        begin_date,
                                                        end_date)
    df_revenue_web = metrics_service.calculate_metric('revenue (web)',
                                                      begin_date,
                                                      end_date)
    df_revenue_all = metrics_service.calculate_metric('revenue (all)',
                                                      begin_date,
                                                      end_date)

    _chech_df(df_response_time, ideal_response_time, ['user_id', 'metric'],
              True, True)
    _chech_df(df_revenue_web, ideal_revenue_web, ['user_id', 'metric'],
              True, True)
    _chech_df(df_revenue_all, ideal_revenue_all, ['user_id', 'metric'],
              True, True)
    print('simple test passed')

    # Test for remove outlier
    metrics = pd.DataFrame({
        'user_id': ['1', '2', '3'],
        'metric': [1., 2, 3]
    })
    design = Design(
        metric_name='response_time',
        metric_outlier_lower_bound=0.1,
        metric_outlier_upper_bound=2.2,
        metric_outlier_process_type='drop',
    )
    ideal_processed_metrics = pd.DataFrame({
        'user_id': ['1', '2'],
        'metric': [1., 2]
    })

    metrics_service = MetricsService()
    processed_metrics = metrics_service.process_outliers(metrics, design)
    _chech_df(processed_metrics, ideal_processed_metrics,
              ['user_id', 'metric'], True, True)
    print('simple test passed')

    # Test for CUPED
    df_sales = pd.DataFrame({
        'sale_id': [1, 2, 3, 4, 5],
        'date': [datetime(2022, 3, day, 11) for day in range(10, 15)],
        'price': [1100, 1500, 2000, 2500, 3000],
        'user_id': ['1', '2', '1', '2', '3'],
    })
    df_web_logs = pd.DataFrame({
        'date': [datetime(2022, 3, day, 11) for day in range(10, 15)],
        'user_id': ['1', '2', '1', '2', '3'],
    })
    begin_date = datetime(2022, 3, 12, 0)
    end_date = datetime(2022, 3, 19, 0)

    ideal_metrics = pd.DataFrame({
        'user_id': ['1', '2', '3'],
        'metric': [2159.5303, 2933.0110, 2407.45856],
    })

    data_service = DataService({'sales': df_sales, 'web-logs': df_web_logs})
    metrics_service = MetricsService(data_service)
    metrics = metrics_service.calculate_metric(
        'revenue (web)', begin_date, end_date, 'on (previous week revenue)'
    )
    _chech_df(metrics, ideal_metrics, ['user_id', 'metric'], True,
              True, decimal=1)
    print('simple test passed')
