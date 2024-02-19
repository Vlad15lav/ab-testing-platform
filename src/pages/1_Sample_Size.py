import pandas as pd
import streamlit as st

from experiments import get_sample_size
from experiments import Design, ExperimentsService


st.set_page_config(
        page_title="A/B Testing Platforme | Sample Size",
        page_icon="🧮",
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

st.title('🧮Sample Size Calculator')

with st.expander("Minimum Sample Size for Estimating a Population Mean", True):
    col1, col2 = st.columns(2)
    with col1:
        alp_level = st.slider('Alpha level', 0.01, 0.99, 0.05, key='m1')
        power_level = st.slider('Power level', 0.01, 0.99, 0.8, key='m2')

    with col2:
        std_placeholder = st.empty()
        std_value = std_placeholder.text_input('Standard deviation', key='m3')
        effect = st.text_input('Effect', key='m4')

    # Вычисление размера выборке на основе своего CSV файла
    uploaded_file = st.file_uploader("Upload CSV File", key='m5')
    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        select_user_col = st.selectbox("Choose Users Column", df.columns)
        select_metric_col = st.selectbox("Choose Metric Column", df.columns)
        df_stats = df[[select_user_col, select_metric_col]].copy()
        df_stats.rename(columns=({select_user_col: 'user_id',
                                  select_metric_col: 'metric'}), inplace=True)

    # Кнопка для вычисления размера выборки
    if st.button('Sample Size', key='m6'):
        if not effect:
            st.markdown("<p class='error'>Enter expected effect!</p>",
                        unsafe_allow_html=True)

        try:
            # Вычисляем дисперсию метрики и узнаем размер выборки
            if uploaded_file and not std_value:
                experiments_service = ExperimentsService()
                desgin = Design(effect=effect,
                                alpha=alp_level,
                                beta=1-power_level)

                size = experiments_service.estimate_sample_size(df_stats,
                                                                design=desgin)
                std_value = df_stats['metric'].std()
                std_value = std_placeholder.text_input('Standard deviation',
                                                       value=std_value)
                st.markdown(f"<p class='result'>Sample Size: {size}</p>",
                            unsafe_allow_html=True)
            elif std_value:
                # Вычисление размера выборке на основе параметров
                size = get_sample_size(float(std_value), float(effect),
                                       alp_level, power_level)
                st.markdown(f"<p class='result'>Sample Size: {size}</p>",
                            unsafe_allow_html=True)
            else:
                st.markdown("<p class='error'>\
                            Enter standard deviation or upload csv file!\
                            </p>",
                            unsafe_allow_html=True)
        except Exception:
            st.markdown("<p class='error'>\
                        Enter correct design parameters!</p>",
                        unsafe_allow_html=True)

with st.expander("Minimum Sample Size to Estimate Proportion", True):
    col1, col2 = st.columns(2)
    with col1:
        alp_level = st.slider('Alpha level', 0.01, 0.99, 0.05, key='p1')
        power_level = st.slider('Power level', 0.01, 0.99, 0.8, key='p2')

    with col2:
        prop_level = st.slider('Proportion', 0.00, 1.00, 0.2,
                               step=0.01, key='p3')
        effect = st.slider('Effect', 0.000, 1.000 - prop_level, 0.01,
                           step=0.001, format="%f", key='p4')

    # Вычисление размера выборке на основе своего CSV файла
    uploaded_file = st.file_uploader("Upload CSV File", key='p5')
    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        select_metric_col = st.selectbox("Choose Binary Metric Column",
                                         df.columns)
        df_stats = df[[select_metric_col]].copy()

    # Кнопка для вычисления размера выборки
    if st.button('Sample Size', key="p6"):
        try:
            if uploaded_file:
                prop_level = df_stats[select_metric_col].mean()
            else:
                prop_level = float(prop_level)

            std_value = (prop_level * (1 - prop_level)) ** 0.5
            size = get_sample_size(std_value, float(effect),
                                   alp_level, power_level)
            st.markdown(f"<p class='result'>Sample Size: {size}</p>",
                        unsafe_allow_html=True)
        except Exception:
            st.markdown("<p class='error'>\
                        Enter correct design parameters!</p>",
                        unsafe_allow_html=True)
