import math

from scipy import stats


def get_sample_size(
        sigma: float,
        effect: float,
        alp: float,
        power: float) -> int:
    """Вычисление размера выборки без DataFrame

    :param sigma (float): Стандартное отклонение исторических данных
    :param effect (float): Минимальный ожидаемый эффект
    :param alp (float): Уровень значимость для ошибки 1-го рода
    :param power (float): Пороговая мощность

    :return (int): Необходимый размер выборки для группы
    """

    z_score = stats.norm.ppf(1-alp/2) + stats.norm.ppf(power)
    total_sigma = 2 * (sigma ** 2)
    return math.ceil((z_score ** 2) * total_sigma / (effect ** 2))


def get_mde(
        sigma: float,
        sample_size: int,
        alp: float,
        power: float) -> int:
    """Вычисление MDE

    :param sigma (float): Стандартное отклонение исторических данных
    :param sample_size (int): Размер выборки
    :param alp (float): Уровень значимость для ошибки 1-го рода
    :param power (float): Пороговая мощность

    :return (float): Минимальный эффект, который можно определить
    """
    z_score = stats.norm.ppf(1-alp/2) + stats.norm.ppf(power)
    total_sigma = 2 * (sigma ** 2)
    return ((z_score ** 2) * total_sigma / sample_size) ** 0.5
