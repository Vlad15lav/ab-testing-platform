import numpy as np
from pydantic import BaseModel
from scipy import stats


class Design(BaseModel):
    """Дата-класс с описание параметров эксперимента."""
    statistical_test: str


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


if __name__ == '__main__':
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
