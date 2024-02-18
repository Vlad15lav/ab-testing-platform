import numpy as np
import pandas as pd
import streamlit as st

from src.experiments import Design, ExperimentsService
from src.visualization import plot_interval

st.set_page_config(
        page_title="A/B Testing Platforme | Variance Reduction",
        page_icon="📉",
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

st.title('📉Variance Reduction')

# Параметры дизайна эксперимента
col1, col2 = st.columns(2)
with col1:
    alp_level = st.slider('Alpha level', 0.01, 0.99, 0.05, key='m1')
    effect = st.text_input('Effect', key='m2')

with col2:
    power_level = st.slider('Power level', 0.01, 0.99, 0.8, key='m3')

# Загрузка своего CSV файла
uploaded_metric_file = st.file_uploader("Upload Metric CSV File", key='m5')
uploaded_pilot_file = st.file_uploader("Upload Pilot Users CSV File", key='m6')
if uploaded_metric_file and uploaded_pilot_file:
    df_metric = pd.read_csv(uploaded_metric_file)
    df_pilot = pd.read_csv(uploaded_pilot_file)

    select_user_col = st.selectbox("Choose Users Column", df_metric.columns)
    select_metric_col = st.selectbox("Choose Metric Column", df_metric.columns)
    select_pilot_col = st.selectbox("Choose Pilot Column", df_pilot.columns)

    try:
        df_metric = df_metric[[select_user_col,
                               select_metric_col,
                               'date']].copy()
        df_pilot = df_pilot[[select_user_col, select_pilot_col]].copy()
        df_metric['date'] = pd.to_datetime(df_metric['date'], errors='coerce')

        df_metric.rename(columns=({select_user_col: 'user_id',
                                   select_metric_col: 'metric'}), inplace=True)
        df_pilot.rename(columns=({select_user_col: 'user_id',
                                  select_pilot_col: 'pilot'}), inplace=True)

        min_date, max_date = df_metric['date'].min(), df_metric['date'].max()
        period_experement = st.date_input("Select your period experiment\
                                          [start_date, end_date)",
                                          value=(min_date, max_date),
                                          min_value=min_date,
                                          max_value=max_date,
                                          format="YYYY.MM.DD")
    except Exception:
        pass


# Кнопка для вычисления доверительного интервала
if st.button('Bootstrap Interval', key='m8') and \
        uploaded_metric_file and uploaded_pilot_file:
    try:
        begin_date = np.datetime64(period_experement[0])
        end_date = np.datetime64(period_experement[1])
        df_metric = df_metric[(df_metric['date'] >= begin_date) &
                              (df_metric['date'] < end_date)]
        df_metric = df_metric.groupby('user_id')[['metric']]\
            .sum().reset_index()

        design = Design(alpha=float(alp_level))
        experiments_service = ExperimentsService()

        df_stats = df_pilot.merge(right=df_metric,
                                  how='left',
                                  on='user_id').fillna(0)

        a_metric = df_stats[df_stats['pilot'] == 0]['metric']
        b_metric = df_stats[df_stats['pilot'] == 1]['metric']

    except Exception:
        st.markdown("<p class='error'>Enter correct design parameters!</p>",
                    unsafe_allow_html=True)
