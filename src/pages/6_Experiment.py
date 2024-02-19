import numpy as np
import pandas as pd
import streamlit as st

from src.experiments import Design, ExperimentsService
from src.visualization import plot_experiment


st.set_page_config(
        page_title="A/B Testing Platforme | Experiment",
        page_icon="🧪",
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

st.title('🧪Experiment')

# Параметры дизайна эксперимента
col1, col2 = st.columns(2)
with col1:
    alp_level = st.slider('Alpha level', 0.01, 0.99, 0.05, key='m1')
    strat_option = st.radio("Post-Stratification",
                            ["off", "on"], key="m2")

with col2:
    test_option = st.selectbox('Statistical test',
                               ('T-test', 'U-test'), key='m3')
    agg_option = st.selectbox('Aggregation metric',
                              ('off', 'mean', 'sum'), key='m4')

# Загрузка своего CSV файла
uploaded_metric_file = st.file_uploader("Upload Metric CSV File", key='m5')
uploaded_pilot_file = st.file_uploader("Upload Pilot Users CSV File", key='m6')

if uploaded_metric_file and uploaded_pilot_file:
    df_metric = pd.read_csv(uploaded_metric_file)
    df_pilot = pd.read_csv(uploaded_pilot_file)

    select_user_col = st.selectbox("Choose Users Column", df_metric.columns)
    select_metric_col = st.selectbox("Choose Metric Column", df_metric.columns)
    select_pilot_col = st.selectbox("Choose Pilot Column", df_pilot.columns)
    if strat_option == 'on':
        select_strat_col = st.selectbox("Choose Stratification Column",
                                        df_metric.columns)

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

        if strat_option == 'on':
            df_metric.rename(columns=({select_strat_col: 'strat'}),
                             inplace=True)

        min_date, max_date = df_metric['date'].min(), df_metric['date'].max()
        period_experement = st.date_input("Select your period experiment\
                                          [start_date, end_date]",
                                          value=(min_date, max_date),
                                          min_value=min_date,
                                          max_value=max_date,
                                          format="YYYY.MM.DD")
    except Exception:
        pass


# Кнопка для вычисления доверительного интервала
if st.button('Get Result', key='m8') and \
        uploaded_metric_file and uploaded_pilot_file:
    try:
        begin_date = np.datetime64(period_experement[0])
        end_date = np.datetime64(period_experement[1])
        end_date += np.timedelta64(1, 'D')

        df_metric = df_metric[(df_metric['date'] >= begin_date) &
                              (df_metric['date'] < end_date)]

        if strat_option == 'off' and agg_option != 'off':
            df_metric = df_metric.groupby('user_id')\
                .agg({'metric': agg_option}).reset_index()

        test_option = 'ttest' if test_option == 'T-test' else 'utest'

        design = Design(alpha=float(alp_level),
                        statistical_test=test_option,
                        stratification=strat_option)
        experiments_service = ExperimentsService()
        df_stats = df_pilot.merge(right=df_metric,
                                  how='left',
                                  on='user_id').fillna(0)

        a_metric = df_stats[df_stats['pilot'] == 0]['metric']
        b_metric = df_stats[df_stats['pilot'] == 1]['metric']

        if strat_option == 'on':
            a_metric = df_stats[df_stats['pilot'] == 0][['metric',
                                                         'strat']].values
            b_metric = df_stats[df_stats['pilot'] == 1][['metric',
                                                         'strat']].values

        pvalue = experiments_service.get_pvalue(a_metric, b_metric, design)
        result_cls = 'error' if pvalue >= design.alpha else 'result'
        result_type = 'Failed' if pvalue >= design.alpha else 'Succesed'
        st.markdown(f"<p class='{result_cls}'>" +
                    f"Experiment {result_type}" +
                    "</p>",
                    unsafe_allow_html=True)

        fig = plot_experiment(a_metric, b_metric,
                              title='A/B Test Result | ' +
                              f'pvalue={round(pvalue, 3)}')
        st.pyplot(fig)

    except Exception:
        st.markdown("<p class='error'>Enter correct design parameters!</p>",
                    unsafe_allow_html=True)
