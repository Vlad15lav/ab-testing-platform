import pandas as pd
import streamlit as st

from src.experiments import get_mde


st.set_page_config(
        page_title="A/B Testing Platforme | Minimum Detectable Effect",
        page_icon="🔍",
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

st.title('🔍Minimum Detectable Effect')
st.write('Determine the minimum effect you can detect. \
         Use your values or upload historical data.')

with st.expander("Minimum detectable effect for Estimating a Population Mean",
                 True):
    col1, col2 = st.columns(2)
    with col1:
        alp_level = st.slider('Alpha level', 0.01, 0.99, 0.05, key='m1')
        power_level = st.slider('Power level', 0.01, 0.99, 0.8, key='m2')

    with col2:
        std_placeholder = st.empty()
        std_value = std_placeholder.text_input('Standard deviation', key='m3')
        sample_size = st.text_input('Sample size', key='m4')

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
    if st.button('Minimum Detectable Effect', key='m6'):
        if not sample_size:
            st.markdown("<p class='error'>Enter sample size!</p>",
                        unsafe_allow_html=True)

        try:
            sample_size = int(sample_size)

            # Вычисляем дисперсию метрики и узнаем размер выборки
            if uploaded_file:
                std_data = df_stats['metric'].std()
                std_value = std_placeholder.text_input('Standard deviation',
                                                       value=std_data)
            elif std_value:
                std_data = float(std_value)
            else:
                st.markdown("<p class='error'>\
                            Enter standard deviation or upload csv file!\
                            </p>",
                            unsafe_allow_html=True)

            if uploaded_file or std_value:
                effect = get_mde(std_data, sample_size,
                                 alp_level, 1 - power_level)
                st.markdown(f"<p class='result'>MDE: {effect}</p>",
                            unsafe_allow_html=True)
        except Exception:
            pass

with st.expander("Minimum detectable effect to Estimate Proportion", True):
    col1, col2 = st.columns(2)
    with col1:
        alp_level = st.slider('Alpha level', 0.01, 0.99, 0.05, key='p1')
        power_level = st.slider('Power level', 0.01, 0.99, 0.8, key='p2')

    with col2:
        prop_level = st.slider('Proportion', 0.00, 1.00, 0.2,
                               step=0.01, key='p3')
        sample_size = st.text_input('Sample size', key='p4')

    # Вычисление размера выборке на основе своего CSV файла
    uploaded_file = st.file_uploader("Upload CSV File", key='p5')
    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        select_metric_col = st.selectbox("Choose Binary Metric Column",
                                         df.columns)
        df_stats = df[[select_metric_col]].copy()

    # Кнопка для вычисления размера выборки
    if st.button('Minimum Detectable Effect', key="p6"):
        if not sample_size:
            st.markdown("<p class='error'>Enter sample size!</p>",
                        unsafe_allow_html=True)

        try:
            sample_size = int(sample_size)

            # Вычисляем дисперсию метрики и узнаем MDE
            if uploaded_file:
                prop_level = df_stats[select_metric_col].mean()
            elif prop_level:
                prop_level = float(prop_level)
            else:
                st.markdown("<p class='error'>\
                            Enter proportion or upload csv file!\
                            </p>",
                            unsafe_allow_html=True)

            if uploaded_file or prop_level:
                std_value = (prop_level * (1 - prop_level)) ** 0.5
                effect = get_mde(std_value, sample_size,
                                 alp_level, 1 - power_level)
                st.markdown(f"<p class='result'>MDE: {effect}</p>",
                            unsafe_allow_html=True)
        except Exception:
            pass
