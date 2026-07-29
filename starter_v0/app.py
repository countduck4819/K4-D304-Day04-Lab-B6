from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version
from chat import run_model_tool_loop, write_transcript, now_iso, safe_slug


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
RUNS_DIR = ROOT / "runs"
TRANSCRIPTS_DIR = ROOT / "transcripts"
VERSIONS_DIR = ROOT / "versions"
load_lab_env(ROOT)


def available_snapshots() -> list[str]:
    if not VERSIONS_DIR.exists():
        return []
    return sorted([p.name for p in VERSIONS_DIR.iterdir() if p.is_dir() and (p / "system_prompt.md").exists() and (p / "tools.yaml").exists()])


st.set_page_config(page_title="Research Agent — Day 04", layout="wide")


THEME_CSS = """
<style>
:root {
  --bg-body: #f6f8fb;
  --bg-card: #ffffff;
  --border-soft: #e4e9f0;
  --text-main: #2c3e50;
  --text-muted: #6b7c93;
  --mint-500: #3fd6b0;
  --mint-600: #2fbf9a;
  --hero-from: #c73866;
  --hero-to: #2b8e8a;
}

/* Body background: clean off-white */
[data-testid="stAppViewContainer"] {
  background-color: var(--bg-body);
}

/* Hero gradient bar across the top of the main content */
[data-testid="stAppViewContainer"] > .main::before {
  content: "";
  display: block;
  height: 140px;
  margin: -1rem -1rem 1.5rem -1rem;
  background: linear-gradient(90deg, var(--hero-from) 0%, #7a3a8f 45%, var(--hero-to) 100%);
  border-radius: 0 0 18px 18px;
  box-shadow: 0 4px 18px rgba(44, 62, 80, 0.08);
}

/* Sidebar clean white with subtle right border */
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
  background-color: #ffffff !important;
  border-right: 1px solid var(--border-soft) !important;
}

/* Cards: white with soft shadow (like "Trade" feature cards) */
[data-testid="stChatMessage"], .stExpander, [data-testid="stExpander"] {
  background-color: var(--bg-card) !important;
  border-radius: 12px !important;
  border: 1px solid var(--border-soft) !important;
  box-shadow: 0 4px 16px rgba(44, 62, 80, 0.06);
}

/* Chat input */
[data-testid="stChatInput"] textarea, [data-testid="stChatInput"] {
  background-color: #ffffff !important;
  border-radius: 24px !important;
  border-color: var(--border-soft) !important;
}

/* Primary buttons: mint pill (like the "Schedule a Free Consultation" CTA) */
.stButton > button {
  background-color: var(--mint-500) !important;
  color: white !important;
  border: none !important;
  border-radius: 999px !important;
  padding: 0.5rem 1.4rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.2px;
  box-shadow: 0 3px 12px rgba(63, 214, 176, 0.28);
  transition: transform 0.15s ease, background-color 0.15s ease;
}
.stButton > button:hover {
  background-color: var(--mint-600) !important;
  transform: translateY(-1px);
}

/* Tabs: quiet, mint underline for active */
.stTabs [data-baseweb="tab-list"] {
  gap: 4px;
  border-bottom: 1px solid var(--border-soft);
}
.stTabs [data-baseweb="tab"] {
  background-color: transparent !important;
  border-radius: 8px 8px 0 0 !important;
  padding: 0.6rem 1.2rem !important;
  color: var(--text-muted) !important;
  font-weight: 500;
}
.stTabs [aria-selected="true"] {
  color: var(--mint-600) !important;
  border-bottom: 3px solid var(--mint-500) !important;
}

/* Headings: professional dark navy */
h1, h2, h3, h4 {
  color: var(--text-main) !important;
  font-weight: 700 !important;
  letter-spacing: -0.2px;
}
h2 {
  border-bottom: 1px solid var(--border-soft);
  padding-bottom: 0.4rem;
}

/* Small mint accent on section titles */
h3 {
  color: var(--mint-600) !important;
}

/* Code blocks */
pre, code, .stCode {
  background-color: #f0f4f8 !important;
  border-radius: 8px !important;
  color: #2c3e50 !important;
}

/* Dataframes */
[data-testid="stDataFrame"] {
  border-radius: 10px !important;
  border: 1px solid var(--border-soft) !important;
  overflow: hidden;
  background-color: var(--bg-card);
}

/* Inputs */
input, textarea, select {
  border-radius: 8px !important;
}

/* Links: mint */
a {
  color: var(--mint-600) !important;
}
</style>
"""
st.markdown(THEME_CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def read_artifacts() -> tuple[str, list[dict[str, Any]], str]:
    prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    decls = load_tool_declarations(tools_path)
    version_label = st.session_state.get("version_label", "v3")
    return system_prompt, decls, version_label


def artifact_version_string(version_label: str) -> str:
    return build_artifact_version(
        version_label,
        ARTIFACTS_DIR / "system_prompt.md",
        ARTIFACTS_DIR / "tools.yaml",
    ).artifact_version


def load_run_files() -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    if not RUNS_DIR.exists():
        return runs
    for path in sorted(RUNS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        summary = data.get("summary") or {}
        runs.append({
            "file": path.name,
            "version": data.get("version") or data.get("artifact_version_label") or "?",
            "artifact_version": data.get("artifact_version", ""),
            "suite": data.get("suite", ""),
            "provider": data.get("provider", ""),
            "total_cases": summary.get("total_cases"),
            "measured_cases": summary.get("measured_cases"),
            "passed_cases": summary.get("passed_cases"),
            "case_accuracy": summary.get("case_accuracy"),
            "tool_routing_accuracy": summary.get("tool_routing_accuracy"),
            "argument_accuracy": summary.get("argument_accuracy"),
            "multiturn_accuracy": summary.get("multiturn_accuracy"),
            "provider_error_cases": summary.get("provider_error_cases"),
            "failure_counts": summary.get("failure_counts") or {},
            "results": data.get("results", []),
            "path": str(path),
        })
    return runs


def render_tool_trace(rounds: list[dict[str, Any]]) -> None:
    if not rounds:
        st.info("No tool calls in this turn.")
        return
    for round_data in rounds:
        st.markdown(f"**Round {round_data.get('round', '?')}**")
        calls = round_data.get("tool_calls", [])
        results = round_data.get("tool_results", [])
        if not calls:
            st.caption("No tool call this round — direct answer.")
            continue
        for i, call in enumerate(calls):
            tool_name = call.get("name", "?")
            args = call.get("args", {})
            result = results[i].get("result") if i < len(results) else {}
            error = None
            if isinstance(result, dict):
                error = result.get("error")
            status_label = "ERROR" if error else "OK"
            with st.expander(f"[{status_label}] `{tool_name}` — args: `{json.dumps(args, ensure_ascii=False)}`", expanded=False):
                if error:
                    st.error(f"{error}: {result.get('message') if isinstance(result, dict) else ''}")
                st.code(json.dumps(result, ensure_ascii=False, indent=2, default=str)[:6000], language="json")


def chat_tab() -> None:
    st.header("Chat with the agent")

    system_prompt, decls, version_label = read_artifacts()
    artifact_version = artifact_version_string(version_label)
    openai_tools = to_openai_tools(decls)

    left, right = st.columns([3, 1])
    with right:
        st.markdown("**Session config**")
        provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0)
        st.text_input("Version label", key="version_label", value=version_label)
        st.markdown(f"**Artifact version**\n\n`{artifact_version}`")
        st.markdown(f"**Declared tools:** {len(decls)}")
        with st.expander("List of tools", expanded=False):
            for t in decls:
                st.markdown(f"- `{t['name']}`")
        if st.button("Clear conversation"):
            st.session_state.pop("chat_history", None)
            st.session_state.pop("chat_turns", None)
            st.session_state.pop("transcript_path", None)
            st.rerun()

    with left:
        history: list[dict[str, str]] = st.session_state.get("chat_history", [])
        turns: list[dict[str, Any]] = st.session_state.get("chat_turns", [])

        for turn in turns:
            with st.chat_message("user"):
                st.markdown(turn.get("user", ""))
            with st.chat_message("assistant"):
                st.markdown(turn.get("assistant_text") or "*(no text)*")
                render_tool_trace(turn.get("rounds", []))

        user_input = st.chat_input("Ask the research agent…")
        if user_input:
            with st.chat_message("user"):
                st.markdown(user_input)

            provider = make_provider(provider_name)
            selected_model = getattr(provider, "default_model", None)

            messages = [
                {"role": "system", "content": system_prompt},
                *history[-10:],
                {"role": "user", "content": user_input},
            ]

            with st.chat_message("assistant"):
                with st.spinner("Agent is thinking…"):
                    try:
                        result = run_model_tool_loop(
                            provider=provider,
                            messages=messages,
                            tools=openai_tools,
                            model=None,
                            max_tool_rounds=4,
                        )
                        assistant_text = result.get("assistant_text") or ""
                        st.markdown(assistant_text or "*(no text)*")
                        render_tool_trace(result.get("rounds", []))

                        history.append({"role": "user", "content": user_input})
                        history.append({"role": "assistant", "content": assistant_text})
                        turn_record = {
                            "turn_index": len(turns) + 1,
                            "started_at": now_iso(),
                            "user": user_input,
                            "status": result.get("status"),
                            "assistant_text": assistant_text,
                            "rounds": result.get("rounds", []),
                            "tool_events": result.get("tool_events", []),
                            "ended_at": now_iso(),
                        }
                        turns.append(turn_record)
                        st.session_state["chat_history"] = history
                        st.session_state["chat_turns"] = turns

                        transcript_path = st.session_state.get("transcript_path")
                        if transcript_path is None:
                            ts = datetime.now().strftime("%Y%m%dT%H%M%S%f")
                            transcript_path = TRANSCRIPTS_DIR / f"ui_{safe_slug(version_label)}_{safe_slug(provider_name)}_{ts}.transcript.json"
                            st.session_state["transcript_path"] = str(transcript_path)
                        transcript_path = Path(st.session_state["transcript_path"])
                        transcript = {
                            "transcript_id": transcript_path.stem,
                            "artifact_version": artifact_version,
                            "version": version_label,
                            "provider": provider_name,
                            "model": selected_model,
                            "created_at": turns[0]["started_at"] if turns else now_iso(),
                            "updated_at": now_iso(),
                            "turns": turns,
                        }
                        write_transcript(transcript_path, transcript)
                        st.caption(f"Transcript: `{transcript_path.name}`")
                    except Exception as exc:
                        st.error(f"{type(exc).__name__}: {exc}")


def compare_tab() -> None:
    st.header("Version comparison")
    runs = load_run_files()
    if not runs:
        st.warning("No runs yet — run `python run_eval.py …` first.")
        return

    base_runs = [r for r in runs if r["suite"] == "base"]
    group_runs = [r for r in runs if r["suite"] == "group"]

    st.subheader("Base suite metrics per version")
    if base_runs:
        rows = [{
            "version": r["version"],
            "case_acc": r["case_accuracy"],
            "routing_acc": r["tool_routing_accuracy"],
            "arg_acc": r["argument_accuracy"],
            "multiturn_acc": r["multiturn_accuracy"],
            "passed": r["passed_cases"],
            "measured": r["measured_cases"],
            "provider_err": r["provider_error_cases"],
            "provider": r["provider"],
            "file": r["file"],
        } for r in base_runs]
        st.dataframe(rows, use_container_width=True, hide_index=True)

        latest_by_version: dict[str, dict[str, Any]] = {}
        for r in base_runs:
            latest_by_version[r["version"]] = r
        chart_data = {v: (r["case_accuracy"] or 0.0) for v, r in latest_by_version.items()}
        if chart_data:
            st.bar_chart(chart_data, y_label="case_accuracy")
    else:
        st.info("No base-suite runs found.")

    st.subheader("Group (team) suite metrics")
    if group_runs:
        rows = [{
            "version": r["version"],
            "case_acc": r["case_accuracy"],
            "routing_acc": r["tool_routing_accuracy"],
            "arg_acc": r["argument_accuracy"],
            "multiturn_acc": r["multiturn_accuracy"],
            "passed": r["passed_cases"],
            "measured": r["measured_cases"],
            "file": r["file"],
        } for r in group_runs]
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No group-suite runs found.")

    st.subheader("Failure counts per version (base suite)")
    if base_runs:
        all_types = sorted({t for r in base_runs for t in (r["failure_counts"] or {}).keys()})
        rows = []
        for r in base_runs:
            row = {"version": r["version"], "file": r["file"]}
            for t in all_types:
                row[t] = (r["failure_counts"] or {}).get(t, 0)
            rows.append(row)
        st.dataframe(rows, use_container_width=True, hide_index=True)

    st.subheader("Drill-down: what improved between two versions")
    versions_available = sorted({r["version"] for r in base_runs})
    if len(versions_available) >= 2:
        cols = st.columns(2)
        with cols[0]:
            v_a = st.selectbox("From version", versions_available, index=0)
        with cols[1]:
            v_b = st.selectbox("To version", versions_available, index=len(versions_available) - 1)
        run_a = next((r for r in base_runs if r["version"] == v_a), None)
        run_b = next((r for r in base_runs if r["version"] == v_b), None)
        if run_a and run_b:
            def status_map(run: dict[str, Any]) -> dict[str, str]:
                out: dict[str, str] = {}
                for case in run.get("results", []):
                    cid = case.get("id") or case.get("case_id") or ""
                    passed = ((case.get("result") or {}).get("passed"))
                    ft = ((case.get("result") or {}).get("failure_type")) or "-"
                    out[cid] = "PASS" if passed else f"FAIL({ft})"
                return out

            a_status = status_map(run_a)
            b_status = status_map(run_b)
            all_ids = sorted(set(a_status.keys()) | set(b_status.keys()))
            rows = []
            for cid in all_ids:
                a = a_status.get(cid, "-")
                b = b_status.get(cid, "-")
                if a == b:
                    delta = "same"
                elif a.startswith("FAIL") and b == "PASS":
                    delta = "fixed"
                elif a == "PASS" and b.startswith("FAIL"):
                    delta = "regressed"
                else:
                    delta = "changed"
                rows.append({"case_id": cid, v_a: a, v_b: b, "delta": delta})
            st.dataframe(rows, use_container_width=True, hide_index=True)


def about_tab() -> None:
    st.header("About this agent")
    _, decls, version_label = read_artifacts()
    artifact_version = artifact_version_string(version_label)
    st.markdown(f"**Artifact version:** `{artifact_version}`")
    st.markdown(f"**Declared tools:** {len(decls)}")

    st.subheader("Tools")
    for t in decls:
        with st.expander(f"`{t['name']}`", expanded=False):
            st.markdown(t.get("description", ""))
            st.code(json.dumps(t.get("parameters", {}), ensure_ascii=False, indent=2), language="json")

    st.subheader("Sample questions to try")
    st.markdown("""
- **Normal research:** *"Tin AI hôm nay có gì nổi bật?"* → routes to `lookup`.
- **Twitter timeline:** *"Xem các tweet gần đây của Sam Altman"* → routes to `timeline`.
- **Missing info:** *"Tóm tắt bài viết này giùm mình"* (no URL) → should call `clarify`.
- **Sensitive action:** *"Gửi lên Telegram: 'chào nhóm'"* → should call `clarify(yes_no)` first.
- **New tools:** *"Alan Turing là ai?"* (→ `wiki`), *"Top HN stories about LLM"* (→ `hackernews`), *"Thời tiết Hanoi"* (→ `weather`), *"100 USD sang VND"* (→ `currency`).
""")


def llm_vs_agent_tab() -> None:
    st.header("LLM alone vs Agent with tools")
    st.caption("Same question, two runs side by side: a plain LLM with no tools, and the current agent with all declared tools.")

    system_prompt, decls, version_label = read_artifacts()
    openai_tools = to_openai_tools(decls)
    artifact_version = artifact_version_string(version_label)

    left, right = st.columns([3, 1])
    with right:
        st.markdown("**Config**")
        provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0, key="vs_provider")
        st.markdown(f"**Agent artifact**\n\n`{artifact_version}`")
        st.markdown(f"**Declared tools:** {len(decls)}")

    with left:
        query = st.text_area(
            "Your question",
            height=90,
            key="vs_query",
            placeholder="Ví dụ: Thời tiết Hà Nội bây giờ / 100 USD sang VND / Tin AI hôm nay",
        )
        run = st.button("Run both side by side", key="vs_run")

    if not run:
        st.info("Try questions where a plain LLM struggles: current weather, live currency rates, today's news, latest tweets, or specific URLs. The agent should visibly outperform.")
        return
    if not query.strip():
        st.warning("Enter a question first.")
        return

    provider = make_provider(provider_name)

    col_llm, col_agent = st.columns(2)

    with col_llm:
        st.markdown("### LLM alone (no tools)")
        st.caption("Plain assistant, cutoff-bound knowledge, no external calls.")
        with st.spinner("LLM answering…"):
            try:
                messages_plain = [
                    {"role": "system", "content": "You are a helpful assistant. Answer the user directly from your own knowledge. You do not have access to any tools, the internet, or real-time data."},
                    {"role": "user", "content": query},
                ]
                response = provider.complete(messages_plain, [], model=None, temperature=0.0)
                st.markdown("**Answer**")
                st.markdown(response.text or "*(no text)*")
                st.markdown("**Tool trace**")
                st.caption("No tools available — the LLM must guess or refuse.")
            except Exception as exc:
                st.error(f"{type(exc).__name__}: {exc}")

    with col_agent:
        st.markdown("### Agent (with tools)")
        st.caption(f"System prompt + {len(decls)} declared tools including your team-written tools.")
        with st.spinner("Agent thinking…"):
            try:
                result = run_model_tool_loop(
                    provider=provider,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query},
                    ],
                    tools=openai_tools,
                    model=None,
                    max_tool_rounds=4,
                )
                st.markdown("**Answer**")
                st.markdown(result.get("assistant_text") or "*(no text)*")
                st.markdown("**Tool trace**")
                render_tool_trace(result.get("rounds", []))
            except Exception as exc:
                st.error(f"{type(exc).__name__}: {exc}")

    st.divider()
    st.markdown("**Suggested questions that highlight the gap:**")
    st.markdown("""
- `Thời tiết Hà Nội hôm nay` — plain LLM has no real-time weather.
- `100 USD sang VND` — plain LLM gives a stale/guessed rate.
- `Tin AI hôm nay có gì` — plain LLM cannot know today's news.
- `Tweet mới nhất của Sam Altman` — plain LLM cannot access Twitter.
- `Top HN stories về LLM` — plain LLM cannot query Hacker News.
- `Alan Turing là ai?` — both may answer, but the agent cites Wikipedia.
""")


def compare_live_tab() -> None:
    st.header("Ask the same question across versions")
    st.caption("Runs your prompt on multiple prompt/tool snapshots and shows tool calls + final answer side by side.")

    snapshots = available_snapshots()
    if not snapshots:
        st.warning("No snapshots in `versions/`. Create `versions/vN/system_prompt.md` + `tools.yaml` first.")
        return

    left, right = st.columns([3, 1])
    with right:
        st.markdown("**Config**")
        provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0, key="cmp_provider")
        selected = st.multiselect("Versions to compare", snapshots, default=snapshots, key="cmp_versions")
        st.caption(f"Estimated cost: {len(selected)}× a single-question call.")

    with left:
        query = st.text_area("Your question", height=90, key="cmp_query", placeholder="Ví dụ: Tin AI hôm nay có gì nổi bật?")
        run = st.button("Run across selected versions", key="cmp_run")

    if not run:
        return
    if not query.strip():
        st.warning("Enter a question first.")
        return
    if not selected:
        st.warning("Pick at least one version.")
        return

    provider = make_provider(provider_name)
    cols = st.columns(len(selected))
    for col, version_name in zip(cols, selected):
        with col:
            st.markdown(f"### {version_name}")
            snap_dir = VERSIONS_DIR / version_name
            system_prompt = (snap_dir / "system_prompt.md").read_text(encoding="utf-8")
            decls = load_tool_declarations(snap_dir / "tools.yaml")
            openai_tools = to_openai_tools(decls)
            artifact_version = build_artifact_version(version_name, snap_dir / "system_prompt.md", snap_dir / "tools.yaml").artifact_version
            st.caption(f"`{artifact_version}`")
            st.caption(f"Declared tools: {len(decls)}")
            with st.spinner(f"Running on {version_name}…"):
                try:
                    result = run_model_tool_loop(
                        provider=provider,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": query},
                        ],
                        tools=openai_tools,
                        model=None,
                        max_tool_rounds=4,
                    )
                    st.markdown("**Final answer**")
                    st.markdown(result.get("assistant_text") or "*(no text)*")
                    st.markdown("**Tool trace**")
                    render_tool_trace(result.get("rounds", []))
                except Exception as exc:
                    st.error(f"{type(exc).__name__}: {exc}")


tab_chat, tab_vs_llm, tab_live_cmp, tab_compare, tab_about = st.tabs([
    "Chat",
    "LLM vs Agent",
    "Compare across versions",
    "Version metrics",
    "About",
])
with tab_chat:
    chat_tab()
with tab_vs_llm:
    llm_vs_agent_tab()
with tab_live_cmp:
    compare_live_tab()
with tab_compare:
    compare_tab()
with tab_about:
    about_tab()
