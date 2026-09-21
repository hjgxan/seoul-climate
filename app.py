import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 데이터 로드 및 전처리 ---
@st.cache_data
def load_data(filepath: str = "seoul_temperature.csv") -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip()
    df["날짜"] = df["날짜"].str.strip()
    df["날짜"] = pd.to_datetime(df["날짜"])
    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["일교차"] = df["최고기온(℃)"] - df["최저기온(℃)"]
    return df

df = load_data()

# --- 연도별 집계 ---
yearly_stats = df.groupby("연도").agg(
    평균기온=("평균기온(℃)", "mean"),
    최저기온=("최저기온(℃)", "mean"),
    최고기온=("최고기온(℃)", "mean"),
    평균일교차=("일교차", "mean")
).reset_index()

yearly_stats["5년이동평균"] = yearly_stats["평균기온"].rolling(window=5, min_periods=1).mean()

# 히트맵용 피벗 테이블
heatmap_data = df.pivot_table(index="연도", columns="월", values="평균기온(℃)", aggfunc="mean")

# --- 사이드바: 연도 범위 슬라이더 ---
min_year = int(yearly_stats["연도"].min())
max_year = int(yearly_stats["연도"].max())

start_year, end_year = st.sidebar.slider(
    "연도 범위 선택",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
)

# --- 선택 구간 필터링 ---
filtered_yearly = yearly_stats[(yearly_stats["연도"] >= start_year) & (yearly_stats["연도"] <= end_year)].copy()
filtered_heatmap = heatmap_data.loc[start_year:end_year]

# --- 1. 연도별 평균기온 꺾은선 그래프 + 5년 이동평균 ---
fig_line = go.Figure()

fig_line.add_trace(go.Scatter(
    x=filtered_yearly["연도"],
    y=filtered_yearly["평균기온"],
    mode="lines+markers",
    name="연도별 평균기온",
    line=dict(color="#1f77b4", width=2),
    marker=dict(size=6)
))

fig_line.add_trace(go.Scatter(
    x=filtered_yearly["연도"],
    y=filtered_yearly["5년이동평균"],
    mode="lines",
    name="5년 이동평균",
    line=dict(color="#d62728", width=3, dash="dot")
))

fig_line.update_layout(
    title=f"연도별 평균기온 ({start_year}–{end_year})",
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    height=400,
    hovermode="x unified"
)
st.plotly_chart(fig_line, use_container_width=True)

# --- 2. 월별 히트맵 (이미지 색상 사용) ---
# 이미지에서 추출한 색상 팔레트: #001c04 → #192780 → #760000 → #620000
fig_heatmap = go.Figure(data=go.Heatmap(
    z=filtered_heatmap.values,
    x=filtered_heatmap.columns,
    y=filtered_heatmap.index,
    colorscale=[
        [0.0, "#001c04"],
        [0.25, "#192780"],
        [0.5, "#4a4a4a"],
        [0.75, "#760000"],
        [1.0, "#620000"]
    ],
    colorbar=dict(title="평균기온 (℃)"),
    hoverongaps=False
))
fig_heatmap.update_layout(
    title="월별 평균기온 히트맵",
    xaxis_title="월",
    yaxis_title="연도",
    height=500
)
st.plotly_chart(fig_heatmap, use_container_width=True)

# --- 3. 최고기온 상위 10일 & 최저기온 하위 10일 표 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("최고기온 상위 10일")
    top10_hot = df.sort_values(by="최고기온(℃)", ascending=False).head(10)
    hot_display = top10_hot[["날짜", "최고기온(℃)"]].copy()
    hot_display["날짜"] = hot_display["날짜"].dt.strftime("%Y-%m-%d")
    hot_display["최고기온(℃)"] = hot_display["최고기온(℃)"].round(1)
    st.dataframe(hot_display, use_container_width=True, hide_index=True)

with col2:
    st.subheader("최저기온 하위 10일")
    top10_cold = df.sort_values(by="최저기온(℃)", ascending=True).head(10)
    cold_display = top10_cold[["날짜", "최저기온(℃)"]].copy()
    cold_display["날짜"] = cold_display["날짜"].dt.strftime("%Y-%m-%d")
    cold_display["최저기온(℃)"] = cold_display["최저기온(℃)"].round(1)
    st.dataframe(cold_display, use_container_width=True, hide_index=True)

# --- 4. 연도별 평균 일교차 그래프 ---
fig_diurnal = go.Figure()
fig_diurnal.add_trace(go.Scatter(
    x=filtered_yearly["연도"],
    y=filtered_yearly["평균일교차"],
    mode="lines+markers",
    name="평균 일교차",
    line=dict(color="#9467bd", width=2),
    marker=dict(size=5)
))
fig_diurnal.update_layout(
    title="연도별 평균 일교차",
    xaxis_title="연도",
    yaxis_title="일교차 (℃)",
    height=400
)
st.plotly_chart(fig_diurnal, use_container_width=True)
