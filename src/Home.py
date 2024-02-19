import streamlit as st

st.set_page_config(
        page_title="A/B Testing Platforme",
        page_icon="👨‍🔬",
        layout="wide"
    )


def main():
    st.title("👨‍🔬A/B Testing Platform")

    with st.expander("💡About Platform", True):
        st.write("A/B testing is a method of marketing research " +
                 "in which two versions of a strategy (A and B) are " +
                 "compared to determine which one is more effective. " +
                 "In business, A/B testing is used to optimize web pages, " +
                 "advertising campaigns, email newsletters, and other " +
                 "elements of marketing strategy. It helps make informed " +
                 "decisions based on data, increasing conversion rates, " +
                 "improving user experience, and ultimately enhancing the " +
                 "efficiency of business processes.")

        _, col_center, _ = st.columns(3)
        with col_center:
            st.image('images/ab_picture.jfif',
                     caption='A/B Testing Picture')

    with st.expander("🧮Sample Size Calculator"):
        st.write("On this page, you'll find a sample size calculator. " +
                 "Here, you can determine the required sample size for " +
                 "your A/B test, considering the significance level, " +
                 "test power, and expected conversions.")

    with st.expander("🔍Minimum Detectable Effect"):
        st.write("This page provides information on the minimum " +
                 "detectable effect. Here, you can specify the effect " +
                 "size you aim to detect with your A/B test to make " +
                 "statistically significant conclusions.")

    with st.expander("📈Estimate Errors"):
        st.write("On this page, you can estimate potential errors when " +
                 "conducting A/B testing. Various aspects are " +
                 "considered, such as Type I error, Type II error, " +
                 "and other statistical parameters.")

    with st.expander("🅱Bootstrap"):
        st.write("Bootstrap is a resampling method used to assess " +
                 "the distribution of statistics based on available " +
                 "data. On this page, you can apply the bootstrap " +
                 "method to estimate confidence intervals " +
                 "and other statistical parameters.")

    with st.expander("📊Metrics Calculator"):
        st.write("Here, a metrics calculator is provided, " +
                 "allowing you to input A/B test results and " +
                 "obtain various key performance indicators, " +
                 "such as Revenue, Linerization for Ratio " +
                 "and more. Additionally, methods for reducing " +
                 "variance, such as CUPED (Controlled-experiment " +
                 "Using Pre-Existing Data), and metric " +
                 "transformation like linearization, are available.")

    with st.expander("🧪Experiment"):
        st.write("This page serves as the central hub for " +
                 "conducting the A/B test. Here, you can " +
                 "configure test parameters, make changes to the " +
                 "page, define control and experimental groups, " +
                 "and then analyze the test results.")


if __name__ == "__main__":
    main()
