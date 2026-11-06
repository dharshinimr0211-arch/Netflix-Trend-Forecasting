import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from statsmodels.tsa.arima.model import ARIMA


st.set_page_config(
    page_title="Netflix Analytics",
    page_icon="🎬",
    layout="wide"
)

# Colours
BLACK = "#000000"
BLUE = "#242f9b"
LAVENDER = "#d1d5f6"
WHITE = "#ffffff"

# Styling
st.markdown("""
<style>
[data-testid="stMainBlockContainer"] {
    padding-top: 1.0rem;
}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stSidebar"],
[data-testid="stHeader"] {
    background-color: #000000;
    color: #ffffff;
}

[data-testid="stSidebar"] {
    border-right: 1px solid #242f9b;
}

h1, h2, h3, p, label {
    color: #ffffff;
}

div[data-testid="stMetric"] {
    background-color: #000000;
    border: 1px solid #242f9b;
    padding: 16px;
    border-radius: 8px;
}

div[data-testid="stMetricValue"] {
    color: #ffffff;
}

hr {
    border-color: #242f9b;
}
</style>
""", unsafe_allow_html=True)

# Load dataset
BASE_DIR = Path(__file__).parent

@st.cache_data
def load_data():
    df = pd.read_csv(BASE_DIR / "Dataset.csv")
    df.columns = df.columns.str.strip()

    df["date_added"] = pd.to_datetime(
        df["date_added"].astype("string").str.strip(),
        errors="coerce"
    )

    return df

df = load_data()

@st.cache_data
def prepare_monthly_data(data):
    monthly_data = (
        data.dropna(subset=["date_added"])
        .set_index("date_added")
        .resample("MS")
        .size()
        .asfreq("MS", fill_value=0)
    )

    monthly_data.name = "titles_added"

    return monthly_data

monthly_data = prepare_monthly_data(df)


MONTH_NAMES = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December"
]

MODEL_EVALUATION = pd.DataFrame({
    "Model": [
        "ARIMA (0,1,1)",
        "SARIMA",
        "Holt's Linear Trend",
        "Naive"
    ],
    "MAE": [28.100105, 53.735994, 87.149360, 35.212121],
    "RMSE": [36.091664, 64.156065, 101.015445, 41.661697]
})


ROLLING_EVALUATION = pd.DataFrame({
    "Model": ["ARIMA (0,1,1)", "Naive"],
    "MAE": [35.860291, 34.312500],
    "RMSE": [43.544361, 43.034143]
})

def get_type_counts(data):
    return data["type"].value_counts()


def get_yearly_additions(data):
    valid_dates = data.dropna(subset=["date_added"])

    return (
        valid_dates.groupby(valid_dates["date_added"].dt.year)
        .size()
        .rename_axis("Year")
        .reset_index(name="Titles Added")
    )

@st.cache_data
def generate_forecast(data, horizon):
    model = ARIMA(data, order=(0, 1, 1))
    fitted_model = model.fit()

    result = fitted_model.get_forecast(steps=horizon)

    forecast = result.predicted_mean
    confidence_interval = result.conf_int(alpha=0.05)

    lower_bound = confidence_interval.iloc[:, 0]
    upper_bound = confidence_interval.iloc[:, 1]

    return forecast, lower_bound, upper_bound

def style_chart(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BLACK,
        plot_bgcolor=BLACK,
        font=dict(color=WHITE, size=12),
        margin=dict(l=20, r=20, t=55, b=20),
        hovermode="x unified"
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#333333",
        zeroline=False
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#333333",
        zeroline=False
    )

    return fig

# Sidebar
st.sidebar.title("🎬 Netflix Analytics")

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Content Analysis",
        "Forecasting",
        "Model Evaluation",
        "Insights"
    ]
)

# Overview
if page == "Overview":

    st.title("Netflix Content Trend Analysis")

    st.write(
        "Explore Netflix content distribution, "
        "historical additions and forecasting trends."
    )

    st.markdown("---")

    total_titles = len(df)
    total_movies = (df["type"] == "Movie").sum()
    total_shows = (df["type"] == "TV Show").sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Titles", f"{total_titles:,}")
    col2.metric("Movies", f"{total_movies:,}")
    col3.metric("TV Shows", f"{total_shows:,}")

    st.markdown("---")
    st.subheader("Content Type Distribution")

    type_counts = (
        get_type_counts(df)
        .rename_axis("Content Type")
        .reset_index(name="Count")
    )

    fig = px.pie(
        type_counts,
        names="Content Type",
        values="Count",
        hole=0.5,
        color="Content Type",
        color_discrete_map={
            "Movie": BLUE,
            "TV Show": LAVENDER
        }
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )

    style_chart(fig)
    st.plotly_chart(fig, use_container_width=True)

# Content Analysis
elif page == "Content Analysis":

    st.title("Content Analysis")

    st.write(
        "Explore the distribution and historical "
        "addition patterns of Netflix content."
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Movies vs TV Shows")

        type_counts = (
            get_type_counts(df)
            .rename_axis("Type")
            .reset_index(name="Count")
        )

        fig = px.pie(
            type_counts,
            names="Type",
            values="Count",
            hole=0.5,
            color="Type",
            color_discrete_map={
                "Movie": BLUE,
                "TV Show": LAVENDER
            }
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label"
        )

        style_chart(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col2:

        st.subheader("Content Ratings")

        rating_counts = (
            df["rating"]
            .fillna("Not Rated")
            .value_counts()
            .head(10)
            .rename_axis("Rating")
            .reset_index(name="Count")
        )

        fig = px.bar(
            rating_counts,
            x="Rating",
            y="Count",
            color_discrete_sequence=[LAVENDER]
        )

        style_chart(fig)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Yearly Content Additions")

    yearly_data = get_yearly_additions(df)

    fig = px.bar(
        yearly_data,
        x="Year",
        y="Titles Added",
        color_discrete_sequence=[BLUE]
    )

    style_chart(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Monthly Content Additions")

    monthly_plot = monthly_data.reset_index()
    monthly_plot.columns = ["Date", "Titles Added"]

    fig = px.line(
        monthly_plot,
        x="Date",
        y="Titles Added",
        markers=True
    )

    fig.update_traces(
        line=dict(color=LAVENDER, width=2),
        marker=dict(size=4, color=BLUE)
    )

    style_chart(fig)
    st.plotly_chart(fig, use_container_width=True)

# Forecasting
elif page == "Forecasting":

    st.title("Netflix Content Forecasting")

    st.write(
        "Forecast future monthly content additions "
        "using the selected ARIMA model."
    )

    st.markdown("---")

    horizon = st.slider(
        "Select forecast horizon (months)",
        min_value=3,
        max_value=24,
        value=12
    )

    with st.spinner("Generating forecast..."):

        forecast, lower_bound, upper_bound = generate_forecast(
            monthly_data, horizon
        )

    st.subheader("Historical Data vs Future Forecast")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=monthly_data.index,
            y=monthly_data.values,
            mode="lines",
            name="Historical Data",
            line=dict(color=BLUE, width=2)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast.index,
            y=lower_bound,
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast.index,
            y=upper_bound,
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(209,213,246,0.16)",
            name="95% Confidence Interval",
            hoverinfo="skip"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast.index,
            y=forecast.values,
            mode="lines+markers",
            name="ARIMA Forecast",
            line=dict(color=LAVENDER, width=2),
            marker=dict(size=6, color=WHITE)
        )
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Titles Added",
        legend=dict(
            orientation="h",
            y=1.12
        )
    )

    style_chart(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "The shaded area represents the 95% confidence interval. "
        "It shows the uncertainty around the predicted values."
    )

    col1, col2 = st.columns(2)
    col1.metric(
        "Average Forecast",
        f"{forecast.mean():.1f} titles/month"
    )

    col2.metric(
        "Forecast Horizon",
        f"{horizon} months"
    )

    st.markdown("---")
    st.subheader("Forecasted Values")

    forecast_table = pd.DataFrame({
        "Predicted Titles": forecast.round(0).astype(int),
        "Lower Bound": lower_bound.round(1),
        "Upper Bound": upper_bound.round(1)
    })

    forecast_table.index.name = "Month"

    st.dataframe(
        forecast_table,
        use_container_width=True
    )

    csv = forecast_table.to_csv().encode("utf-8")

    st.download_button(
        "Download Forecast CSV",
        data=csv,
        file_name="netflix_forecast.csv",
        mime="text/csv"
    )

    st.markdown("---")
    st.caption(
        "Note: These forecasts are based on historical data. "
        "The dataset ends in 2021 and does not represent "
        "Netflix's actual current content additions."
    )

# Model Evaluation
elif page == "Model Evaluation":

    st.title("Model Evaluation")

    st.write("Compare forecasting models using MAE and RMSE.")

    st.markdown("---")

    evaluation_data = MODEL_EVALUATION.copy()

    st.subheader("Holdout Test Performance")

    col1, col2 = st.columns(2)

    col1.metric("Best MAE", "28.10", "ARIMA (0,1,1)")
    col2.metric("Best RMSE", "36.09", "ARIMA (0,1,1)")

    st.subheader("Model Performance Table")

    styled_data = evaluation_data.style.highlight_min(
        subset=["MAE", "RMSE"],
        color=BLUE
    )

    st.dataframe(
        styled_data,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Results obtained from forecasting experiments conducted in the Jupyter Notebook."
    )

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            evaluation_data,
            x="Model",
            y="MAE",
            color_discrete_sequence=[BLUE],
            title="Mean Absolute Error"
        )

        style_chart(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            evaluation_data,
            x="Model",
            y="RMSE",
            color_discrete_sequence=[LAVENDER],
            title="Root Mean Squared Error"
        )

        style_chart(fig)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Rolling-Origin Validation")

    rolling_data = ROLLING_EVALUATION.copy()

    st.dataframe(
        rolling_data,
        use_container_width=True,
        hide_index=True
    )

    st.info(
        "ARIMA performed better on the original holdout test, "
        "but the Naive baseline performed slightly better "
        "during rolling-origin validation."
    )

    st.caption(
        "Model selection should consider both evaluation methods. "
        "ARIMA is retained as the forecasting model for this project, "
        "but it is not superior in every validation setting."
    )

# Insights
elif page == "Insights":

    st.title("Netflix Content Insights")

    st.write(
        "Key findings derived from historical Netflix content data."
    )

    st.markdown("---")

    valid_dates = df.dropna(subset=["date_added"])

    yearly = valid_dates.groupby(
        valid_dates["date_added"].dt.year
    ).size()

    monthly_counts = valid_dates.groupby(
        valid_dates["date_added"].dt.month
    ).size()

    type_counts = get_type_counts(df)

    peak_year = yearly.idxmax()
    peak_additions = yearly.max()
    peak_month = monthly_counts.idxmax()

    col1, col2, col3 = st.columns(3)

    col1.metric("Peak Addition Year", int(peak_year))

    col2.metric(
        "Titles Added in Peak Year",
        int(peak_additions)
    )

    col3.metric(
        "Highest Addition Month",
        MONTH_NAMES[peak_month - 1]
    )

    st.markdown("---")
    st.subheader("Key Findings")

    movie_percentage = (
        type_counts.get("Movie", 0) / len(df)
    ) * 100

    show_percentage = (
        type_counts.get("TV Show", 0) / len(df)
    ) * 100

    st.markdown("**1. Content Distribution**")

    st.write(
        f"Movies account for approximately {movie_percentage:.1f}% "
        f"of the dataset, while TV Shows account for "
        f"{show_percentage:.1f}%."
    )

    st.markdown("**2. Historical Content Growth**")

    st.write(
        f"Netflix content additions reached their highest "
        f"recorded level in {peak_year}, with "
        f"{peak_additions} titles added."
    )

    st.markdown("**3. Monthly Trends**")

    st.write(
        f"{MONTH_NAMES[peak_month - 1]} has the highest "
        f"number of additions when grouped across all years."
    )

    st.markdown("**4. Forecasting Findings**")

    st.write(
        "ARIMA (0,1,1) achieved the lowest MAE and RMSE "
        "among the tested models on the original holdout dataset."
    )

    st.write(
        "However, rolling-origin validation showed that "
        "the Naive baseline performed slightly better."
    )

    st.markdown("---")
    st.subheader("Project Limitations")

    st.write("""
    - The dataset ends in 2021 and does not represent Netflix's current catalogue.
    - Forecasts are based on historical patterns.
    - Sudden changes in content additions are difficult to predict.
    - Forecasts should not be interpreted as actual Netflix business projections.
    """)

    st.markdown("---")

    st.write(
        "This project demonstrates exploratory data analysis, "
        "time-series forecasting, model evaluation and "
        "interactive data visualization."
    )