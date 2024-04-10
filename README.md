# Платформа A/B тестирования

Этот проект представляет собой платформу, которая позволяет использовать A/B тестирование для проведения различных экспериментов. С помощью данной платформы у вас есть возможность легко и удобно загрузить свои данные, настроить параметры проведения теста и анализировать результаты.

Воспользоваться сервисом можно сейчас на [Streamlit Cloud](https://ab-test.streamlit.app/).

## Функционал платформы
На платформе пользователь можешь выполнить следующее:
- Оценить размер выборки для эксперимента.
- Оценить Minimal Detectable Effect.
- Запустить A/A и синтетический A/B тест для поверки корректности эксперимента.
- Построить доверительный интервал Bootstrap.
- Вычислить метрику Revenue, Linearization, CUPED.
- Поддержка метода Post-Stratification.
- Проверить результаты эксперимента с указанием его дизайна.

![Web приложение платформы](/reports/figures/app_preview.png)

## Запуск приложения

Установите Python 3.11 зависимости для проекта:
```bash
pip install -r requirements.txt
```

Запустите Web сервис Streamlit с помощью команды:
```bash
streamlit run src/Home.py
```

Перейдите по ссылке сервиса [localhost:8501](http://localhost:8501).

## Запуск сервиса Docker

Создайте образ Docker:
```bash
docker build -t ab_service .
```

Запустите контейнер с сервисом:
```bash
docker run -p 8501:8501 ab_service
```

## Полезные ссылки

Ноутбуки с материалами:
- [Основы статистики](/references/1_statistical_terms.ipynb)
- [Тестирование гипотез](/references/2_hypothesis_testing.ipynb)
- [MDE](/references/3_mde.ipynb)
- [Дизайн эксперимента](/references/4_design.ipynb)
- [Доверительный интервал и Bootstrap](/references/5_bootstrap.ipynb)
- [Повышение чувствительности](/references/6_variance_reduction.ipynb)
- [Стратификация](/references/7_stratification.ipynb)
- [CUPED](/references/8_cuped.ipynb)
- [Множественное тестирование](/references/9_multiple_testing_problem.ipynb)
- [Split система](/references/10_split_testing.ipynb)
- [Линеаризация](/references/11_linearization.ipynb)
- [Последовательное тестирование](/references/12_sequential_testing.ipynb)

Другие источники:
- [5 лайфхаков для ускорения А/B-тестирования от аналитиков MyTracker](https://tracker.my.com/blog/204/5-lajfhakov-dlya-uskoreniya-a-b-testirovaniya-ot-analitikov-mytracker?lang=ru)
- [Switchback-эксперименты в Ситимобил](https://habr.com/ru/companies/citymobil/articles/560426/)
- [Reliable ML AB Testing & Causal Inference Meetup](https://ods.ai/tracks/reliable_ml_ab_testing-causal_inference_meetup)