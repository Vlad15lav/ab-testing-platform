import pandas as pd

from datetime import datetime


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


class MetricsService:
    def __init__(self, data_service):
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

    def calculate_metric(self,
                         metric_name,
                         begin_date,
                         end_date,
                         user_ids=None):
        """Считает значения для вычисления метрик.

        :param metric_name (str): название метрики
        :param begin_date (datetime): дата начала периода (включая границу)
        :param end_date (datetime): дата окончания периода (не включая границу)
        :param user_ids (list[str], None): список пользователей.
            Если None, то вычисляет значения для всех пользователей.
        :return df: columns=['user_id', 'metric']
        """
        if metric_name == 'response time':
            return self._calculate_response_time(begin_date,
                                                 end_date,
                                                 user_ids)
        elif metric_name == 'revenue (web)':
            return self._calculate_revenue_web(begin_date, end_date, user_ids)
        elif metric_name == 'revenue (all)':
            return self._calculate_revenue_all(begin_date, end_date, user_ids)
        else:
            raise ValueError('Wrong metric name')


def _chech_df(df, df_ideal, sort_by, reindex=False, set_dtypes=False):
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
    assert df_ideal.equals(df), \
        'Итоговый датафрейм не совпадает с верным результатом.'


if __name__ == '__main__':
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
