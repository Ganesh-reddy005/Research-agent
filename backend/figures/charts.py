"""Figures and tables drawn from the lab notebook: measured numbers only, never written by a model.
Charts are rendered with matplotlib (object API, no pyplot, so it's safe in worker threads) to SVG
with real text, in IEEE column width and print-friendly greys."""
import io
from matplotlib import rc_context
from matplotlib.figure import Figure
from experiments import notebook as nb
from experiments.lab import latest_results

COLUMN_INCHES = (3.5, 2.2)  # one IEEE column
GREY, DARK, ACCENT = "#9a9a9a", "#333333", "#ff511c"
MAX_BARS = 12
MAX_CHARTS = 2  # from-scratch results: one chart per metric, at most this many
STYLE = {"svg.fonttype": "none", "font.family": "serif", "font.size": 7.5, "axes.spines.top": False,
         "axes.spines.right": False, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6}


def bar_chart(labels: list[str], means: list[float], spreads: list[float], ylabel: str,
              reference: float | None = None, highlight: int | None = None) -> str:
    """SVG of one bar per label with ± spread error bars; reference draws the baseline as a dashed line."""
    with rc_context(STYLE):
        fig = Figure(figsize=COLUMN_INCHES)
        ax = fig.add_subplot()
        colours = [ACCENT if i == highlight else GREY for i in range(len(labels))]
        ax.bar(range(len(labels)), means, yerr=spreads, color=colours, edgecolor=DARK, linewidth=0.5,
               error_kw={"elinewidth": 0.6, "capsize": 2, "ecolor": DARK})
        if reference is not None:
            ax.axhline(reference, color=DARK, linewidth=0.6, linestyle="--")
        ax.set_xticks(range(len(labels)), labels, rotation=30 if len(labels) > 5 else 0,
                      ha="right" if len(labels) > 5 else "center")
        ax.set_ylabel(ylabel)
        fig.tight_layout(pad=0.9)  # room for the browser's serif, which can be wider than matplotlib's
        out = io.StringIO()
        fig.savefig(out, format="svg")
    return out.getvalue()


def _short(text: str, words: int = 9) -> str:
    parts = str(text or "").split()
    return " ".join(parts[:words]) + ("…" if len(parts) > words else "")


def _value(mean, spread) -> str:
    return "—" if mean is None else f"{mean:.4g} ± {spread or 0:.2g}"


def improve_figures(notebook: list[dict], brief: dict, repeats: int) -> list[dict]:
    """Improving existing code: every attempt against the baseline, as a chart and as a table."""
    goal, metric = brief["metric"]["goal"], brief["metric"]["name"]
    baseline = notebook[0].get("metric") if notebook else None
    if baseline is None:
        return []
    better = "higher" if goal == "maximize" else "lower"
    ran = [a for a in notebook if a.get("metric") is not None and all(a.get("checks", {}).values())][:MAX_BARS]
    kept = [a for a in ran if a.get("verdict") == nb.IMPROVED]  # what Lume kept: a gain beyond the noise
    labels = ["Baseline" if a["n"] == 1 else f"#{a['n']}" for a in ran]
    chart = bar_chart(labels, [a["metric"] for a in ran], [a.get("spread") or 0 for a in ran], _short(metric, 4),
                      reference=baseline, highlight=next((i for i, a in enumerate(ran) if kept and a["n"] == kept[-1]["n"]), None))
    rows = []
    for a in notebook:
        change = "—" if a["n"] == 1 or a.get("metric") is None or not baseline else f"{(a['metric'] - baseline) / baseline * 100:+.1f}%"
        rows.append([str(a["n"]), "Unmodified code" if a["n"] == 1 else _short(a.get("hypothesis")),
                     _value(a.get("metric"), a.get("spread")), change, a.get("verdict", "")])
    note = f"mean ± standard deviation over {repeats} runs; {better} is better"
    return [
        {"id": "fig-attempts", "kind": "chart", "origin": "measured", "svg": chart,
         "caption": f"{metric} of the unmodified code (dashed line) and of each attempt that passed its checks; "
                    f"{'the highlighted bar is the change kept' if kept else 'no change beat the baseline beyond the noise'} ({note}).",
         "summary": "; ".join(f"{label}: {a['metric']:.4g}" for label, a in zip(labels, ran))},
        {"id": "tab-attempts", "kind": "table", "origin": "measured",
         "caption": f"Every attempt, including those that failed ({note}).",
         "table": {"columns": ["#", "Change", metric, "vs. baseline", "Outcome"], "rows": rows}},
    ]


def build_figures(notebook: list[dict], repeats: int) -> list[dict]:
    """Code written from scratch: the final results table (variant × metric), and a chart per metric."""
    results = latest_results(notebook)
    if not results:
        return []
    by_metric: dict[str, dict[str, dict]] = {}
    for name, value in results.items():
        variant, _, metric = name.rpartition(".")
        by_metric.setdefault(metric or name, {})[variant or name] = value
    variants = sorted({v for table in by_metric.values() for v in table})
    note = f"mean ± standard deviation over {repeats} runs"
    figures = [{"id": "tab-results", "kind": "table", "origin": "measured", "caption": f"Results of every variant ({note}).",
                "table": {"columns": ["Variant", *by_metric], "rows": [[v, *(_value(t[v]["mean"], t[v]["spread"]) if v in t else "—"
                                                                             for t in by_metric.values())] for v in variants]}}]
    for i, (metric, table) in enumerate(list(by_metric.items())[:MAX_CHARTS], start=1):
        names = list(table)[:MAX_BARS]
        figures.append({"id": f"fig-results-{i}", "kind": "chart", "origin": "measured",
                        "svg": bar_chart(names, [table[n]["mean"] for n in names], [table[n]["spread"] for n in names], metric),
                        "caption": f"{metric} of each variant ({note}).",
                        "summary": "; ".join(f"{n}: {table[n]['mean']:.4g}" for n in names)})
    return figures


def experiment_figures(state) -> list[dict]:
    notebook, lab = state.get("notebook") or [], state.get("lab") or {}
    if not notebook or not state.get("experiment_brief"):
        return []
    repeats = (lab.get("spec") or {}).get("repeats", 5)
    if lab.get("mode") == "build":
        return build_figures(notebook, repeats)
    return improve_figures(notebook, state["experiment_brief"], repeats)
