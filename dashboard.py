from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import yaml


LOG_PATH = Path("data/logs.jsonl")
CONFIG_PATH = Path("config/dashboard.yaml")


def load_contract() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)["dashboard"]


CONTRACT = load_contract()
TIME_RANGE_MINUTES = int(CONTRACT["time_range_minutes"])
REFRESH_SECONDS = int(CONTRACT["refresh_seconds"])
PANELS = {panel["id"]: panel for panel in CONTRACT["panels"]}


st.set_page_config(
    page_title="Monitoring & LLMOps Dashboard",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(ttl=REFRESH_SECONDS)
def load_logs(path: str, modified_at: float) -> pd.DataFrame:
    del modified_at

    rows: list[dict] = []

    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not rows:
        return pd.DataFrame()

    frame = pd.DataFrame(rows)

    required_columns = [
        "ts",
        "event",
        "latency_ms",
        "ttft_ms",
        "cost_usd",
        "tokens_in",
        "tokens_out",
        "quality_score",
        "error_type",
        "tool_name",
        "tool_success",
    ]

    for column in required_columns:
        if column not in frame.columns:
            frame[column] = pd.NA

    frame["ts"] = pd.to_datetime(frame["ts"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["ts"])

    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(
        minutes=TIME_RANGE_MINUTES
    )

    return frame[frame["ts"] >= cutoff].sort_values("ts")


def numeric_values(
    frame: pd.DataFrame,
    event: str,
    field: str,
) -> pd.Series:
    selected = frame.loc[frame["event"] == event, field]
    return pd.to_numeric(selected, errors="coerce").dropna()


def threshold_text(panel_id: str) -> str:
    threshold = PANELS[panel_id]["threshold"]
    symbol = "≤" if threshold["operator"] == "lte" else "≥"
    return f"{symbol} {threshold['value']} {PANELS[panel_id]['unit']}"


def show_threshold(
    panel_id: str,
    value: float,
) -> None:
    threshold = PANELS[panel_id]["threshold"]
    target = float(threshold["value"])

    passed = (
        value <= target
        if threshold["operator"] == "lte"
        else value >= target
    )

    message = f"Threshold: {threshold_text(panel_id)}"

    if passed:
        st.success(message)
    else:
        st.error(message)


def render_dashboard() -> None:
    if not LOG_PATH.exists():
        st.error("Không tìm thấy data/logs.jsonl.")
        st.code("python scripts/load_test.py --concurrency 5")
        return

    frame = load_logs(
        str(LOG_PATH),
        LOG_PATH.stat().st_mtime,
    )

    if frame.empty:
        st.warning(
            f"Không có dữ liệu trong {TIME_RANGE_MINUTES} phút gần nhất. "
            "Hãy chạy lại load test."
        )
        st.code("python scripts/load_test.py --concurrency 5")
        return

    responses = frame[frame["event"] == "response_sent"].copy()
    requests = frame[frame["event"] == "request_received"].copy()
    failures = frame[frame["event"] == "request_failed"].copy()

    left, right = st.columns(2)

    # 1. Latency
    with left:
        with st.container(border=True):
            st.subheader(PANELS["latency"]["title"])
            st.caption(
                f"Unit: {PANELS['latency']['unit']} · "
                f"Threshold: {threshold_text('latency')}"
            )

            latency = numeric_values(
                frame,
                "response_sent",
                "latency_ms",
            )
            ttft = numeric_values(
                frame,
                "response_sent",
                "ttft_ms",
            )

            p50 = float(latency.quantile(0.50)) if not latency.empty else 0
            p95 = float(latency.quantile(0.95)) if not latency.empty else 0
            p99 = float(latency.quantile(0.99)) if not latency.empty else 0
            ttft_p95 = float(ttft.quantile(0.95)) if not ttft.empty else 0

            metric_columns = st.columns(4)
            metric_columns[0].metric("P50", f"{p50:,.0f} ms")
            metric_columns[1].metric("P95", f"{p95:,.0f} ms")
            metric_columns[2].metric("P99", f"{p99:,.0f} ms")
            metric_columns[3].metric("TTFT P95", f"{ttft_p95:,.0f} ms")

            latency_chart = responses[["ts", "latency_ms"]].copy()
            latency_chart["latency_ms"] = pd.to_numeric(
                latency_chart["latency_ms"],
                errors="coerce",
            )
            latency_chart = latency_chart.dropna()

            if not latency_chart.empty:
                figure = px.line(
                    latency_chart,
                    x="ts",
                    y="latency_ms",
                    markers=True,
                    labels={
                        "ts": "Time",
                        "latency_ms": "Latency (ms)",
                    },
                )
                figure.add_hline(
                    y=3000,
                    line_dash="dash",
                    line_color="red",
                )
                st.plotly_chart(figure, use_container_width=True)

            show_threshold("latency", p95)

    # 2. Traffic
    with right:
        with st.container(border=True):
            st.subheader(PANELS["traffic"]["title"])
            st.caption(
                f"Unit: {PANELS['traffic']['unit']} · "
                f"Threshold: {threshold_text('traffic')}"
            )

            traffic_count = len(requests)

            if traffic_count > 1:
                elapsed_minutes = max(
                    1.0,
                    (
                        requests["ts"].max() - requests["ts"].min()
                    ).total_seconds()
                    / 60,
                )
            else:
                elapsed_minutes = 1.0

            rate_per_minute = traffic_count / elapsed_minutes

            metric_columns = st.columns(2)
            metric_columns[0].metric("Requests", traffic_count)
            metric_columns[1].metric(
                "Rate/minute",
                f"{rate_per_minute:.2f}",
            )

            traffic_chart = requests[["ts"]].copy()
            traffic_chart["minute"] = traffic_chart["ts"].dt.floor("min")
            traffic_chart = (
                traffic_chart.groupby("minute")
                .size()
                .reset_index(name="requests")
            )

            if not traffic_chart.empty:
                figure = px.bar(
                    traffic_chart,
                    x="minute",
                    y="requests",
                    labels={
                        "minute": "Time",
                        "requests": "Requests/minute",
                    },
                )
                figure.add_hline(
                    y=1,
                    line_dash="dash",
                    line_color="red",
                )
                st.plotly_chart(figure, use_container_width=True)

            show_threshold("traffic", rate_per_minute)

    left, right = st.columns(2)

    # 3. Errors
    with left:
        with st.container(border=True):
            st.subheader(PANELS["errors"]["title"])
            st.caption(
                f"Unit: {PANELS['errors']['unit']} · "
                f"Error threshold: {threshold_text('errors')}"
            )

            request_count = len(requests)
            failure_count = len(failures)

            error_rate = (
                failure_count / request_count * 100
                if request_count
                else 0.0
            )

            retrieval = frame[
                (frame["tool_name"] == "retrieval")
                & frame["tool_success"].notna()
            ]

            retrieval_success = (
                retrieval["tool_success"]
                .astype(str)
                .str.lower()
                .eq("true")
                .mean()
                * 100
                if not retrieval.empty
                else 0.0
            )

            metric_columns = st.columns(3)
            metric_columns[0].metric(
                "Error rate",
                f"{error_rate:.2f}%",
            )
            metric_columns[1].metric(
                "Failed requests",
                failure_count,
            )
            metric_columns[2].metric(
                "Retrieval success",
                f"{retrieval_success:.2f}%",
            )

            error_breakdown = (
                failures["error_type"]
                .fillna("unknown")
                .value_counts()
                .rename_axis("error_type")
                .reset_index(name="count")
            )

            if not error_breakdown.empty:
                figure = px.bar(
                    error_breakdown,
                    x="error_type",
                    y="count",
                    labels={
                        "error_type": "Error type",
                        "count": "Count",
                    },
                )
                st.plotly_chart(figure, use_container_width=True)
            else:
                st.info("Không có request_failed trong time range.")

            show_threshold("errors", error_rate)

    # 4. Cost
    with right:
        with st.container(border=True):
            st.subheader(PANELS["cost"]["title"])
            st.caption(
                f"Unit: {PANELS['cost']['unit']} · "
                f"Threshold: {threshold_text('cost')}"
            )

            cost_chart = responses[["ts", "cost_usd"]].copy()
            cost_chart["cost_usd"] = pd.to_numeric(
                cost_chart["cost_usd"],
                errors="coerce",
            )
            cost_chart = cost_chart.dropna()

            total_cost = float(cost_chart["cost_usd"].sum())

            st.metric("Total cost", f"${total_cost:.6f}")

            if not cost_chart.empty:
                cost_chart["minute"] = cost_chart["ts"].dt.floor("min")
                cost_by_minute = (
                    cost_chart.groupby("minute", as_index=False)["cost_usd"]
                    .sum()
                )

                figure = px.line(
                    cost_by_minute,
                    x="minute",
                    y="cost_usd",
                    markers=True,
                    labels={
                        "minute": "Time",
                        "cost_usd": "Cost (USD)",
                    },
                )
                st.plotly_chart(figure, use_container_width=True)

            show_threshold("cost", total_cost)

    left, right = st.columns(2)

    # 5. Tokens
    with left:
        with st.container(border=True):
            st.subheader(PANELS["tokens"]["title"])
            st.caption(
                f"Unit: {PANELS['tokens']['unit']} · "
                f"Threshold: {threshold_text('tokens')}"
            )

            tokens_in = numeric_values(
                frame,
                "response_sent",
                "tokens_in",
            )
            tokens_out = numeric_values(
                frame,
                "response_sent",
                "tokens_out",
            )

            total_in = int(tokens_in.sum())
            total_out = int(tokens_out.sum())
            total_tokens = total_in + total_out

            metric_columns = st.columns(3)
            metric_columns[0].metric("Input tokens", f"{total_in:,}")
            metric_columns[1].metric("Output tokens", f"{total_out:,}")
            metric_columns[2].metric("Total", f"{total_tokens:,}")

            token_chart = pd.DataFrame(
                {
                    "type": ["Input", "Output"],
                    "tokens": [total_in, total_out],
                }
            )

            figure = px.bar(
                token_chart,
                x="type",
                y="tokens",
                color="type",
                labels={
                    "type": "Token type",
                    "tokens": "Tokens",
                },
            )
            st.plotly_chart(figure, use_container_width=True)

            show_threshold("tokens", max(total_in, total_out))

    # 6. Quality
    with right:
        with st.container(border=True):
            st.subheader(PANELS["quality"]["title"])
            st.caption(
                f"Unit: {PANELS['quality']['unit']} · "
                f"Threshold: {threshold_text('quality')}"
            )

            quality_chart = responses[["ts", "quality_score"]].copy()
            quality_chart["quality_score"] = pd.to_numeric(
                quality_chart["quality_score"],
                errors="coerce",
            )
            quality_chart = quality_chart.dropna()

            quality_mean = (
                float(quality_chart["quality_score"].mean())
                if not quality_chart.empty
                else 0.0
            )

            st.metric("Mean quality score", f"{quality_mean:.3f}")

            if not quality_chart.empty:
                figure = px.line(
                    quality_chart,
                    x="ts",
                    y="quality_score",
                    markers=True,
                    labels={
                        "ts": "Time",
                        "quality_score": "Quality score",
                    },
                )
                figure.add_hline(
                    y=0.75,
                    line_dash="dash",
                    line_color="red",
                )
                figure.update_yaxes(range=[0, 1])
                st.plotly_chart(figure, use_container_width=True)

            show_threshold("quality", quality_mean)


st.title("📊 K4-L3B Monitoring & LLMOps")
st.caption(
    f"Source: {LOG_PATH} · "
    f"Time range: {TIME_RANGE_MINUTES} minutes · "
    f"Refresh: {REFRESH_SECONDS} seconds"
)

if st.button("Refresh now"):
    st.cache_data.clear()
    st.rerun()


@st.fragment(run_every=REFRESH_SECONDS)
def auto_refresh_dashboard() -> None:
    render_dashboard()


auto_refresh_dashboard()