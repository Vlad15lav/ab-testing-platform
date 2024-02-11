import hashlib

from pydantic import BaseModel


class Experiment(BaseModel):
    """
    id_exp - идентификатор эксперимента.
    salt - соль эксперимента (для случайного распределения пользователей
    на контрольную/пилотную группы)
    buckets_count - необходимое количество бакетов.
    conflicts - список идентификаторов экспериментов, которые нельзя проводить
        одновременно на одних и тех же пользователях.
    """
    id_exp: int

    salt: str = ''
    buckets_count: int = 0
    conflicts: list[int] = []


class SplittingService:
    def __init__(self,
                 buckets_count,
                 bucket_salt='',
                 buckets=None,
                 id2experiment=None):
        """Класс для распределения экспериментов и пользователей по бакетам.

        :param buckets_count (int): количество бакетов.
        :param bucket_salt (str): соль для разбиения пользователей по бакетам.
            При одной соли каждый пользователь должен всегда попадать
            в один и тот же бакет.
            Если изменить соль, то распределение людей по бакетам
            должно измениться.
        :param buckets (list[list[int]]) - список бакетов, в каждом бакете
        перечислены идентификаторы
            эксперименты, которые в нём проводятся.
        :param id2experiment (dict[int, Experiment]) - словарь пар:
        идентификатор эксперимента - эксперимент.
        """
        self.buckets_count = buckets_count
        self.bucket_salt = bucket_salt
        if buckets:
            self.buckets = buckets
        else:
            self.buckets = [[] for _ in range(buckets_count)]

        if id2experiment:
            self.id2experiment = id2experiment
        else:
            self.id2experiment = {}

    def add_experiment(self, experiment):
        """Проверяет можно ли добавить эксперимент, добавляет если можно.

        :param experiment (Experiment): параметры эксперимента,
            который нужно запустить
        :return success, buckets:
            success (boolean) - можно ли добавить эксперимент,
                True - можно, иначе - False
            buckets (list[list[int]]]) - список бакетов, в каждом бакете
            перечислены идентификаторы экспериментов,
            которые в нём проводятся.
        """
        id_exp = experiment.id_exp
        buckets_count = experiment.buckets_count
        conflicts = experiment.conflicts

        # Проверяем какие бакеты доступны для эксперимента
        correct_buckets = []
        for id_bucket, bucket in enumerate(self.buckets):
            if set(conflicts) & set(bucket):
                continue

            correct_buckets.append((id_bucket, len(bucket)))

        if len(correct_buckets) < buckets_count:
            return False, self.buckets

        # Добавляем эксперимент в сервис
        sort_correct_buckets = sorted(correct_buckets,
                                      key=lambda x: x[1],
                                      reverse=True)
        for i in range(buckets_count):
            id_bucket, _ = sort_correct_buckets[i]
            self.buckets[id_bucket].append(id_exp)

        return True, self.buckets

    def _get_hash_id(self, user_id: str, salt: str, n_buckets: int):
        """Вычисляем остаток от деления: (hash(value) + salt) % modulo.

        :param user_id (str): текст идентификатора пользователя
        :param salt (str): соль
        :param n_backets (str): количество бактов/групп

        :return number (int): индекс бакета/группы
        """

        input_string = (user_id + salt).encode()
        hash_value = hashlib.md5(input_string).hexdigest()

        return int(hash_value, 16) % n_buckets

    def process_user(self, user_id):
        """Определяет в какие эксперименты попадает пользователь.

        Сначала нужно определить бакет пользователя.
        Затем для каждого эксперимента в этом бакете выбрать пилотную или
        контрольную группу.

        :param user_id (str): идентификатор пользователя
        :return bucket_id, experiment_groups:
            - bucket_id (int) - номер бакета (индекс элемента в self.buckets)
            - experiment_groups (list[tuple]) - список пар: id эксперимента,
            группа.
                Группы: 'A', 'B'.
            Пример: (8, [(194, 'A'), (73, 'B')])
        """
        # Узнаем бакет для пользовател
        bucket_id = self._get_hash_id(user_id,
                                      self.bucket_salt,
                                      self.buckets_count)

        user_groups = []
        # Выбираем группу для каждого эксперимента из бакета
        for id_exp in self.buckets[bucket_id]:
            experiment = self.id2experiment[id_exp]
            group_id = self._get_hash_id(user_id, experiment.salt, 2)
            group = 'A' if group_id == 0 else 'B'
            user_groups.append((id_exp, group))

        return bucket_id, user_groups


def check_correct_buckets(buckets, experiments):
    for experiment in experiments:
        buckets_with_exp = [b for b in buckets if experiment.id_exp in b]
        assert experiment.buckets_count == len(buckets_with_exp), \
            'Неверное количество бакетов с экспериментом'
        parallel_experiments = set(sum(buckets_with_exp, []))
        err_msg = 'Несовместные эксперименты в одном бакете'
        assert len(set(experiment.conflicts) & parallel_experiments) == 0, \
            err_msg


if __name__ == '__main__':
    # Test splitting experiments per backet
    experiments = [
        Experiment(id_exp=1, buckets_count=4, conflicts=[4]),
        Experiment(id_exp=2, buckets_count=2, conflicts=[3]),
        Experiment(id_exp=3, buckets_count=2, conflicts=[2]),
        Experiment(id_exp=4, buckets_count=1, conflicts=[1]),
    ]
    ideal_answers = [True, True, True, False]

    splitting_service = SplittingService(buckets_count=4)
    added_experiments = []
    for index, (experiment, ideal_answer) in enumerate(zip(experiments,
                                                           ideal_answers)):
        success, buckets = splitting_service.add_experiment(experiment)
        assert success == ideal_answer, \
            'Сплит-система работает неоптимально или некорректно.'
        if success:
            added_experiments.append(experiment)
        check_correct_buckets(buckets, added_experiments)
    print('simple test passed')

    # Test splitting users per backet
    id2experiment = {
        0: Experiment(id_exp=0, salt='0'),
        1: Experiment(id_exp=1, salt='1')
    }
    buckets = [[0, 1], [1], [], []]
    buckets_count = len(buckets)
    bucket_salt = 'a2N4'

    splitting_service = SplittingService(buckets_count, bucket_salt,
                                         buckets, id2experiment)
    user_ids = [str(x) for x in range(1000)]
    for user_id in user_ids:
        bucket_id, experiment_groups = splitting_service.process_user(user_id)
        assert bucket_id in [0, 1, 2, 3], 'Неверный bucket_id'
        assert len(experiment_groups) == len(buckets[bucket_id]), \
            'Неверное количество экспериментов в бакете'
        for exp_id, group in experiment_groups:
            assert exp_id in id2experiment, 'Неверный experiment_id'
            assert group in ['A', 'B'], 'Неверная group'
    print('simple test passed')
