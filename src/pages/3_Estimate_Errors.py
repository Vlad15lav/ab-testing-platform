import pandas as pd
import streamlit as st

from scipy import stats
from src.experiments import Design, ExperimentsService
from src.visualization import plot_pvalue_ecdf


st.set_page_config(
        page_title="A/B Testing Platforme | Estimate Errors",
        page_icon="📈",
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

st.title('📈Estimate Errors')

# Параметры дизайна эксперимента
col1, col2 = st.columns(2)
with col1:
    alp_level = st.slider('Alpha level', 0.01, 0.99, 0.05, key='m1')
    sample_size = st.text_input('Sample size', key='m2')
    add_option = st.selectbox('Effect add type?',
                              ('Plus', 'Multiply'), key='m3')
with col2:
    power_level = st.slider('Power level', 0.01, 0.99, 0.8, key='m4')
    effect = st.text_input('Relative Effect', key='m5')
    n_iters = st.text_input('Iterations', 1000, key='m6')

# Загрузка своего CSV файла
uploaded_file = st.file_uploader("Upload CSV File", key='m7')
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    select_user_col = st.selectbox("Choose Users Column", df.columns)
    select_metric_col = st.selectbox("Choose Metric Column", df.columns)
    df_stats = df[[select_user_col, select_metric_col]].copy()
    df_stats.rename(columns=({select_user_col: 'user_id',
                              select_metric_col: 'metric'}), inplace=True)

# Кнопка для оценки ошибок
if st.button('Estimate Errors', key='m8') and uploaded_file:
    if not (sample_size or effect or n_iters):
        st.markdown("<p class='error'>Enter design parameters!</p>",
                    unsafe_allow_html=True)

    df_stats = df_stats.groupby('user_id')[['metric']].mean().reset_index()

    try:
        alpha, beta = float(alp_level), 1-float(power_level)
        effect, sample_size = float(effect), int(sample_size)
        n_iters = int(n_iters)
        if add_option == 'Plus':
            effect_add_type = 'all_const'
        elif add_option == 'Multiply':
            effect_add_type = 'all_percent'
        else:
            raise 'Incorrect effect add type!'

        design = Design(effect=effect,
                        alpha=alpha,
                        beta=beta,
                        sample_size=sample_size)
        experiments_service = ExperimentsService()

        pvalues_aa, pvalues_ab, first_type_error, second_type_error = \
            experiments_service.estimate_errors(df_stats,
                                                design,
                                                effect_add_type,
                                                n_iters)

        # Визуализация результатов
        pvalue_ks = stats.kstest(pvalues_aa, 'uniform').pvalue
        ks_correct = 'error' if pvalue_ks < alpha else 'result'
        alpha_correct = first_type_error < alpha + 0.015
        beta_correct = second_type_error < beta + 0.015

        if alpha_correct and beta_correct:
            result_type = 'result'
            is_correct = 'Correct'
        else:
            result_type = 'error'
            is_correct = 'Incorrect'

        st.markdown(f"<p class='{result_type}'>" +
                    f"Design Experiment is {is_correct}" +
                    "</p>",
                    unsafe_allow_html=True)

        # Графики для проверки равномерности pvalue в A/A тесте
        st.title('A/A Test')
        st.markdown(f"<p class='{ks_correct}'>\
                    Kolmogorov Smirnov Test (pvalue = {round(pvalue_ks, 3)})\
                    </p>",
                    unsafe_allow_html=True)
        fig1 = plot_pvalue_ecdf(pvalues_aa, 'p-value ECD Function. ' +
                                'Null Hypothesis')
        st.pyplot(fig1)

        # Графики для проверки обнаржуения эффекта в A/B тесте
        st.title('A/B Test')
        fig2 = plot_pvalue_ecdf(pvalues_ab, 'p-value ECD Function. ' +
                                'Alternative Hypothesis')
        st.pyplot(fig2)

        # Графики для проверки обнаржуения эффекта в A/B тесте
        st.title('Error Rate')
        st.markdown(f"<p class='{'result' if alpha_correct else 'error'}'>\
                    Alpha Error Rate: {round(first_type_error, 5)}\
                    </p>",
                    unsafe_allow_html=True)

        st.markdown(f"<p class='{'result' if beta_correct else 'error'}'>\
                    Beta Error Rate: {round(second_type_error, 5)}\
                    </p>",
                    unsafe_allow_html=True)

    except Exception as e:
        print(e)
        st.markdown("<p class='error'>Enter correct design parameters!</p>",
                    unsafe_allow_html=True)
