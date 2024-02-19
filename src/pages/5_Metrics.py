import pandas as pd
import streamlit as st

from metrics import DataService, Design, MetricsService
# from src.visualization import plot_remove_outliers


@st.cache_data
def load_data(data):
    return pd.read_csv(data)


@st.cache_data
def convert_df(df):
    return df.to_csv().encode('utf-8')


st.set_page_config(
        page_title="A/B Testing Platforme | Metrics Calculator",
        page_icon="📊",
        layout="wide",
    )

st.markdown(
    """
    <style>
    .result {
    font-size:24px;
    color: green
    }
    .error {
    font-size:24px;
    color: red
    }
    </style>""", unsafe_allow_html=True)

st.title('📊Metrics Calculator')

# Параметры дизайна эксперимента
col11, col12, col13 = st.columns(3)
with col11:
    metric_option = st.radio("Select Metric",
                             ["Revenue (Web)",
                              "Revenue (All)",
                              "Linearization (Ratio)"], key="m1")
with col12:
    if metric_option == 'Revenue (Web)':
        cuped_option = st.radio("CUPED",
                                ["off", "on"], key="m2")
    else:
        cuped_option = 'off'
# with col13:
#     outliers_option = st.radio("Process Outliers",
#                                ["off", "drop", "clip"], key="m3")

col1, col2 = st.columns(2)
with col1:
    if cuped_option == 'on':
        cuped_days = st.slider('Previous Days', 1, 28, 7, key='m5')

# Загрузка своего CSV файла
data_service = None
uploaded_metric_file = st.file_uploader("Upload Users Metric CSV File",
                                        key='m7')
if metric_option == 'Linearization (Ratio)':
    uploaded_pilot_file = st.file_uploader("Upload Pilot Users CSV File",
                                           key='m8')
    uploaded_logs_file = True
else:
    uploaded_logs_file = st.file_uploader("Upload Web-Logs CSV File",
                                          key='m6')
    uploaded_pilot_file = True


if uploaded_metric_file and uploaded_pilot_file and uploaded_logs_file:
    # Чтения csv файлов и выбор столбцов
    df_metric = load_data(uploaded_metric_file)
    select_user_col = st.selectbox("Choose Users Column", df_metric.columns)
    select_metric_col = st.selectbox("Choose Metric Column", df_metric.columns)

    if metric_option == 'Linearization (Ratio)':
        df_pilot = load_data(uploaded_pilot_file)
        select_pilot_col = st.selectbox("Choose Pilot Column",
                                        df_pilot.columns)
    else:
        df_logs = load_data(uploaded_logs_file)

    try:
        # Изменение название столбцов для функций
        df_metric.rename(columns=({select_user_col: 'user_id',
                                   select_metric_col: 'price'}),
                         inplace=True)

        if metric_option == 'Linearization (Ratio)':
            df_metric.rename(columns=({'price': 'metric'}),
                             inplace=True)
            df_pilot.rename(columns=({select_user_col: 'user_id',
                                      select_pilot_col: 'pilot'}),
                            inplace=True)
        else:
            df_logs.rename(columns=({select_user_col: 'user_id'}),
                           inplace=True)

        # Обработка временных столбцов
        if uploaded_logs_file:
            df_logs['date'] = pd.to_datetime(df_logs['date'],
                                             format="%Y-%m-%d %H:%M:%S")

        if 'date' in df_metric:
            df_metric['date'] = pd.to_datetime(df_metric['date'],
                                               format="%Y-%m-%d %H:%M:%S")
            # Виджет для выбора интервала метрики
            min_date = df_metric['date'].min()
            max_date = df_metric['date'].max()
            period_experement = st.date_input("Select time period \
                                              [start_date, end_date)",
                                              value=(min_date, max_date),
                                              min_value=min_date,
                                              max_value=max_date,
                                              format="YYYY.MM.DD")

        # Создание Data сервиса
        if metric_option != 'Linearization (Ratio)':
            data_service = DataService({'sales': df_metric,
                                       'web-logs': df_logs})
        else:
            data_service = DataService({'sales': df_metric})

    except Exception:
        pass


# Кнопка для вычисления доверительного интервала
if st.button('Calculate', key='m9') and data_service:
    try:
        design = Design(metric_name=metric_option.lower())
        metrics_service = MetricsService(data_service=data_service)

        # Предобработка интервала времени
        if 'date' in df_metric:
            begin_date = pd.to_datetime(period_experement[0],
                                        errors='coerce')
            end_date = pd.to_datetime(period_experement[1],
                                      errors='coerce')

        # Вычисляем метрику
        if metric_option != 'Linearization (Ratio)':
            df_result = metrics_service.\
                calculate_metric(metric_name=design.metric_name,
                                 begin_date=begin_date,
                                 end_date=end_date,
                                 cuped=cuped_option,
                                 cuped_days=int(cuped_days))
        else:
            df_stats = df_pilot.merge(right=df_metric,
                                      how='left',
                                      on='user_id').fillna(0)

            a_metric = df_stats[df_stats['pilot'] == 0]
            b_metric = df_stats[df_stats['pilot'] == 1]
            df_a_linear, df_b_linear = metrics_service.\
                calculate_linearized_metrics(control_metrics=a_metric,
                                             pilot_metrics=b_metric)
            df_a_linear['pilot'] = 0
            df_b_linear['pilot'] = 1
            df_result = pd.concat((df_a_linear, df_b_linear), axis=0)

        # Сохраняет результат расчета
        st.title('✅Result DataFrame')
        st.dataframe(df_result)

        file_name = f'{metric_option}.csv'
        if 'date' in df_metric:
            file_name = f'{begin_date}_{end_date}_{file_name}'

        csv_file = convert_df(df_result)
        st.download_button(
            label="Download data as CSV",
            data=csv_file,
            file_name=file_name,
            mime='text/csv',
        )

    except Exception:
        st.markdown("<p class='error'>Enter correct parameters!\
                    </p>",
                    unsafe_allow_html=True)


# # Удаляем выбросы при необходимости
# if outliers_option != 'off':
#     min_metric, max_metric = df_result['metric'].min(), \
#         df_result['metric'].max()
#     left, right = st.slider('Select a range of values',
#                             min_metric, max_metric,
#                             (min_metric, max_metric))

#     design.metric_outlier_process_type = outliers_option
#     design.metric_outlier_lower_bound = left
#     design.metric_outlier_upper_bound = right

#     fig = plot_remove_outliers(df_result['metric'],
#                                 left,
#                                 right,
#                                 title='Metric Density')
#     st.pyplot(fig)
