from __future__ import annotations

from pathlib import Path

import streamlit as st

from ground_station_ui.queue_reader import read_payloads, read_telemetry, summarize_telemetry


st.set_page_config(page_title="KilnWatch Ground Station", layout="wide")


def main() -> None:
    st.title("KilnWatch Ground Station")
    st.caption("Displays only payloads downlinked from the satellite edge node")

    queue_dir = Path(st.sidebar.text_input("Transmission queue", "transmission_queue"))
    payloads = read_payloads(queue_dir)
    telemetry = read_telemetry(queue_dir)
    summary = summarize_telemetry(telemetry)

    cols = st.columns(5)
    cols[0].metric("Tiles processed", summary["processed_tiles"])
    cols[1].metric("Alerts received", summary["alerts"])
    cols[2].metric("Raw bytes avoided", summary["bandwidth_saved_bytes"])
    cols[3].metric("Downlinked bytes", summary["transmitted_payload_bytes"])
    ratio = summary["compression_ratio"]
    cols[4].metric("Compression ratio", "inf" if ratio == float("inf") else f"{ratio:.2f}x")

    st.subheader("Received Alerts")
    alerts = [payload for payload in payloads if payload.get("event") == "alert"]
    if alerts:
        st.dataframe(alerts, width="stretch")
    else:
        st.info("No alert payloads received yet.")

    st.subheader("Telemetry")
    if telemetry:
        st.dataframe(telemetry, width="stretch")
    else:
        st.warning("No telemetry.jsonl found in the transmission queue.")

    st.subheader("All Downlinked Payloads")
    st.json(payloads, expanded=False)


if __name__ == "__main__":
    main()
