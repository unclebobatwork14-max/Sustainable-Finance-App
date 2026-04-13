import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="EcoVest", layout="wide")

# =========================================================
# Defaults
# =========================================================
DEFAULTS = {
    "page": "intro",
    "mu1_pct": 5.00,
    "mu2_pct": 12.00,
    "sigma1_pct": 9.00,
    "sigma2_pct": 20.00,
    "rf_pct": 2.00,
    "rho": -0.20,
    "esg1": 35.0,
    "esg2": 80.0,
    "lambda_esg": 0.30,
    "gamma": 3.0,
    "mix_points": 1001,
    "sample_points": 4000,
    "trading_days": 252,
    "investment_amount": 10000.0,
    "onboarding_complete": False,
    "onboarding_step": "investor_type",
    "investor_type": None,
    "has_existing_assets": None,
    "experienced_goal": None,
    "risk_profile": None,
    "esg_profile": None,
    "beginner_mode": False,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# =========================================================
# General helpers
# =========================================================
def go_to(page_name: str):
    st.session_state.page = page_name
    st.rerun()


def reset_onboarding():
    st.session_state.onboarding_complete = False
    st.session_state.onboarding_step = "investor_type"
    st.session_state.investor_type = None
    st.session_state.has_existing_assets = None
    st.session_state.experienced_goal = None
    st.session_state.risk_profile = None
    st.session_state.esg_profile = None
    st.session_state.beginner_mode = False
    st.session_state.page = "intro"
    st.rerun()


def format_gbp(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}£{abs(value):,.2f}"


# =========================================================
# Onboarding helpers
# =========================================================
RISK_MAP = {
    "Aggressive": 1.5,
    "Balanced": 4.0,
    "Conservative": 8.0,
}

ESG_MAP = {
    "Low ESG Impact": 0.10,
    "Medium ESG Impact": 0.45,
    "High ESG Impact": 0.85,
}

EXPERIENCED_OPTIONS = [
    "I already have 2 assets",
    "I would like to find an asset combination",
]


def is_experienced_existing_mode() -> bool:
    return (
        st.session_state.investor_type == "Experienced Investor"
        and st.session_state.experienced_goal == "existing_assets"
    )


def is_experienced_find_mode() -> bool:
    return (
        st.session_state.investor_type == "Experienced Investor"
        and st.session_state.experienced_goal == "find_assets"
    )


def apply_first_time_choices(
    risk_choice: str,
    esg_choice: str,
    custom_gamma: float,
    custom_lambda: float,
):
    gamma_value = float(custom_gamma) if risk_choice == "Custom" else RISK_MAP[risk_choice]
    lambda_value = float(custom_lambda) if esg_choice == "Custom" else ESG_MAP[esg_choice]

    st.session_state.gamma = gamma_value
    st.session_state.lambda_esg = lambda_value
    st.session_state.risk_profile = risk_choice
    st.session_state.esg_profile = esg_choice
    st.session_state.investor_type = "New to Investing/First Time User"
    st.session_state.beginner_mode = True
    st.session_state.onboarding_complete = True
    st.session_state.page = "results"
    st.rerun()


@st.dialog("EcoVest Questionnaire", width="medium", dismissible=False)
def onboarding_dialog():
    step = st.session_state.onboarding_step

    if step == "investor_type":
        st.write("**Are you an experienced investor or a first time user on the app?**")
        st.caption(
            "This helps EcoVest decide whether to use your own asset assumptions or guide you through a simpler path."
        )

        investment_amount = st.number_input(
            "How much money are you looking to invest (£)?",
            min_value=0.0,
            value=float(st.session_state.investment_amount),
            step=100.0,
            format="%.2f",
            key="dialog_investment_amount",
        )
        st.caption(
            "This amount does not change the optimal weights. It is used to convert recommendations into £ allocations."
        )

        investor_choice = st.radio(
            "Select one option",
            ["Experienced Investor", "New to Investing/First Time User"],
            key="dialog_investor_type",
            label_visibility="collapsed",
        )

        c1, c2 = st.columns(2)
        with c2:
            if st.button("Continue", use_container_width=True, key="continue_investor_type"):
                st.session_state.investor_type = investor_choice
                st.session_state.investment_amount = float(investment_amount)
                st.session_state.onboarding_step = (
                    "experienced_path"
                    if investor_choice == "Experienced Investor"
                    else "first_time_path"
                )
                st.rerun()

    elif step == "experienced_path":
        st.write("**Which best describes what you want to do?**")
        st.caption(
            "Choose whether you already have your own 2-asset assumptions or whether you want the app to help you find a stock combination from the workbook."
        )

        asset_choice = st.radio(
            "Select one option",
            EXPERIENCED_OPTIONS,
            key="dialog_existing_assets",
            label_visibility="collapsed",
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back", use_container_width=True, key="back_experienced"):
                st.session_state.onboarding_step = "investor_type"
                st.rerun()
        with c2:
            if st.button("Continue", use_container_width=True, key="continue_experienced"):
                st.session_state.beginner_mode = False
                st.session_state.onboarding_complete = True

                if asset_choice == "I already have 2 assets":
                    st.session_state.has_existing_assets = "Yes"
                    st.session_state.experienced_goal = "existing_assets"
                else:
                    st.session_state.has_existing_assets = "No"
                    st.session_state.experienced_goal = "find_assets"

                st.session_state.page = "inputs"
                st.rerun()

    elif step == "first_time_path":
        st.write("**Choose your risk aversion level**")
        st.caption(
            "Risk aversion means how uncomfortable you are with investment ups and downs. A higher level means you prefer steadier outcomes and usually take less risk."
        )

        risk_choice = st.radio(
            "Risk profile",
            ["Aggressive", "Balanced", "Conservative", "Custom"],
            key="dialog_risk_choice",
        )

        custom_gamma = 4.0
        if risk_choice == "Custom":
            custom_gamma = st.slider(
                "Select your custom risk aversion value",
                min_value=0.5,
                max_value=10.0,
                value=4.0,
                step=0.1,
                key="dialog_custom_gamma",
            )
            st.caption("Please enter a value between 0.5 and 10.0.")

        st.markdown("---")
        st.write("**Choose your ESG preference level**")
        st.caption(
            "This tells EcoVest how much you value holding greener assets. A higher value means the app will care more about ESG and less about pure risk-return efficiency."
        )

        esg_choice = st.radio(
            "ESG preference",
            ["Low ESG Impact", "Medium ESG Impact", "High ESG Impact", "Custom"],
            key="dialog_esg_choice",
        )

        custom_lambda = 0.45
        if esg_choice == "Custom":
            custom_lambda = st.slider(
                "Select your custom ESG intensity value",
                min_value=0.0,
                max_value=1.0,
                value=0.45,
                step=0.01,
                key="dialog_custom_lambda",
            )
            st.caption("Please enter a value between 0.0 and 1.0.")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back", use_container_width=True, key="back_first_time"):
                st.session_state.onboarding_step = "investor_type"
                st.rerun()
        with c2:
            if st.button("Continue", use_container_width=True, key="continue_first_time"):
                apply_first_time_choices(risk_choice, esg_choice, custom_gamma, custom_lambda)


# =========================================================
# Data helpers
# =========================================================
@st.cache_data
def load_fast_workbook() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    candidates = [
        Path("esg_crsp_2025_matched_workbook.xlsx"),
        Path("/mnt/data/esg_crsp_2025_matched_workbook.xlsx"),
    ]
    file_path = next((p for p in candidates if p.exists()), None)
    if file_path is None:
        raise FileNotFoundError(
            "Could not find 'esg_crsp_2025_matched_workbook.xlsx'. Put it in the same folder as app.py."
        )

    summary = pd.read_excel(file_path, sheet_name="Summary")
    cov = pd.read_excel(file_path, sheet_name="Covariance Matrix")
    corr = pd.read_excel(file_path, sheet_name="Correlation Matrix")

    required_cols = {
        "Ticker",
        "ESG Company Name (2025)",
        "ESGCombinedScore 2025",
        "ESG Rating 2025",
        "Latest Available Annual Return (2024)",
    }
    missing = required_cols - set(summary.columns)
    if missing:
        raise ValueError(f"Summary sheet is missing required columns: {sorted(missing)}")

    firms = summary[
        [
            "Ticker",
            "ESG Company Name (2025)",
            "ESG Rating 2025",
            "ESGCombinedScore 2025",
            "Latest Available Annual Return (2024)",
        ]
    ].copy()
    firms = firms.rename(
        columns={
            "ESG Company Name (2025)": "Company",
            "ESG Rating 2025": "ESG Rating",
            "ESGCombinedScore 2025": "ESG Score",
            "Latest Available Annual Return (2024)": "Expected Return",
        }
    )

    firms["Ticker"] = firms["Ticker"].astype(str)
    firms["ESG Score"] = pd.to_numeric(firms["ESG Score"], errors="coerce")
    firms["Expected Return"] = pd.to_numeric(firms["Expected Return"], errors="coerce")
    firms = firms.dropna(subset=["Ticker", "ESG Score", "Expected Return"]).copy()
    firms = firms.drop_duplicates(subset=["Ticker"]).sort_values("Ticker").reset_index(drop=True)

    cov = cov.rename(columns={cov.columns[0]: "Ticker"}).copy()
    cov["Ticker"] = cov["Ticker"].astype(str)
    cov = cov.set_index("Ticker")
    cov = cov.apply(pd.to_numeric, errors="coerce")

    corr = corr.rename(columns={corr.columns[0]: "Ticker"}).copy()
    corr["Ticker"] = corr["Ticker"].astype(str)
    corr = corr.set_index("Ticker")
    corr = corr.apply(pd.to_numeric, errors="coerce")

    common = sorted(set(firms["Ticker"]) & set(cov.index) & set(corr.index))
    firms = firms[firms["Ticker"].isin(common)].copy().sort_values("Ticker").reset_index(drop=True)
    tickers = firms["Ticker"].tolist()
    cov = cov.loc[tickers, tickers]
    corr = corr.loc[tickers, tickers]

    bad = set(cov.index[cov.isna().any(axis=1)])
    bad |= set(cov.columns[cov.isna().any(axis=0)])
    bad |= set(corr.index[corr.isna().any(axis=1)])
    bad |= set(corr.columns[corr.isna().any(axis=0)])

    if bad:
        firms = firms[~firms["Ticker"].isin(bad)].copy().sort_values("Ticker").reset_index(drop=True)
        tickers = firms["Ticker"].tolist()
        cov = cov.loc[tickers, tickers]
        corr = corr.loc[tickers, tickers]

    firms["ESG Score (%)"] = firms["ESG Score"] * 100
    firms["Expected Return (%)"] = firms["Expected Return"] * 100

    return firms, cov, corr


def annualise_covariance(daily_cov: pd.DataFrame, trading_days: int) -> pd.DataFrame:
    return daily_cov * float(trading_days)


# =========================================================
# Plot style helpers
# =========================================================
THEORETICAL_BLUE = "#1f77b4"
ESG_GREEN = "#2ca02c"
LIGHT_GREY = "#bfbfbf"
DARK_GREY = "#666666"


def style_axis(ax):
    ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(LIGHT_GREY)
    ax.spines["bottom"].set_color(LIGHT_GREY)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)
    ax.tick_params(axis="both", colors=DARK_GREY, length=3, width=1)
    ax.xaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))


# =========================================================
# Objective-function helpers
# =========================================================
def var_covar(sigmas: np.ndarray, rho: float) -> np.ndarray:
    return np.array(
        [
            [sigmas[0] ** 2, rho * sigmas[0] * sigmas[1]],
            [rho * sigmas[0] * sigmas[1], sigmas[1] ** 2],
        ]
    )


def objective_value(
    x: np.ndarray,
    mu: np.ndarray,
    cov: np.ndarray,
    gamma: float,
    lambda_esg: float,
    esg_scores: np.ndarray,
) -> float:
    risky_sum = float(np.sum(x))
    if risky_sum <= 1e-12:
        avg_esg = 0.0
    else:
        avg_esg = float(np.dot(x, esg_scores) / risky_sum)

    return float(
        np.dot(x, mu)
        - 0.5 * gamma * np.dot(x, np.dot(cov, x))
        + lambda_esg * avg_esg
    )


def portfolio_metrics(
    x: np.ndarray,
    mu: np.ndarray,
    cov: np.ndarray,
    rf: float,
    esg_scores: np.ndarray,
    gamma: float,
    lambda_esg: float,
) -> dict:
    x = np.asarray(x, dtype=float)
    risky_sum = float(np.sum(x))
    rf_weight = 1.0 - risky_sum
    risky_return = float(np.dot(x, mu))
    variance = float(np.dot(x, np.dot(cov, x)))
    std_dev = float(np.sqrt(max(variance, 0.0)))
    expected_total_return = float(rf_weight * rf + risky_return)
    sharpe = np.nan if std_dev <= 1e-12 else (expected_total_return - rf) / std_dev
    avg_esg = 0.0 if risky_sum <= 1e-12 else float(np.dot(x, esg_scores) / risky_sum)
    obj = objective_value(x, mu, cov, gamma, lambda_esg, esg_scores)

    return {
        "Expected Return": expected_total_return,
        "Variance": variance,
        "Std Dev": std_dev,
        "Risky Weight Sum": risky_sum,
        "Risk-free Weight": rf_weight,
        "Average ESG": avg_esg,
        "Objective": obj,
        "Sharpe Ratio": sharpe,
    }


def project_to_simplex(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    u = np.sort(v)[::-1]
    cssv = np.cumsum(u)
    rho = np.nonzero(u * np.arange(1, len(u) + 1) > (cssv - 1))[0][-1]
    theta = (cssv[rho] - 1) / (rho + 1)
    return np.maximum(v - theta, 0)


def direction_objective(
    p: np.ndarray,
    mu: np.ndarray,
    cov: np.ndarray,
    esg_scores: np.ndarray,
    gamma: float,
    lambda_esg: float,
) -> float:
    p = np.asarray(p, dtype=float)
    a = float(np.dot(p, mu))
    b = float(np.dot(p, np.dot(cov, p)))
    esg_term = float(np.dot(p, esg_scores))

    if gamma <= 1e-12 or b <= 1e-12 or a <= 1e-12:
        return 0.0

    return float((a * a) / (2.0 * gamma * b) + lambda_esg * esg_term)


def direction_gradient(
    p: np.ndarray,
    mu: np.ndarray,
    cov: np.ndarray,
    esg_scores: np.ndarray,
    gamma: float,
    lambda_esg: float,
) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    a = float(np.dot(p, mu))
    b = float(np.dot(p, np.dot(cov, p)))

    if gamma <= 1e-12 or b <= 1e-12 or a <= 1e-12:
        return lambda_esg * esg_scores.copy()

    sigma_p = np.dot(cov, p)
    return (a / (gamma * b)) * mu - (a * a / (gamma * b * b)) * sigma_p + lambda_esg * esg_scores


def solve_direction_simplex(
    mu: np.ndarray,
    cov: np.ndarray,
    esg_scores: np.ndarray,
    gamma: float,
    lambda_esg: float,
    n_random_starts: int = 20,
    max_iter: int = 300,
    step_size: float = 0.15,
    seed: int = 42,
) -> np.ndarray:
    n_assets = len(mu)
    rng = np.random.default_rng(seed)

    starts = [np.ones(n_assets) / n_assets]
    starts.append(project_to_simplex(mu - np.min(mu) + 1e-6))
    starts.append(project_to_simplex(esg_scores - np.min(esg_scores) + 1e-6))

    for i in range(n_assets):
        e = np.zeros(n_assets)
        e[i] = 1.0
        starts.append(e)

    for _ in range(n_random_starts):
        starts.append(rng.dirichlet(np.ones(n_assets)))

    best_p = starts[0].copy()
    best_obj = direction_objective(best_p, mu, cov, esg_scores, gamma, lambda_esg)

    for p0 in starts:
        p = p0.copy()
        current_obj = direction_objective(p, mu, cov, esg_scores, gamma, lambda_esg)

        for _ in range(max_iter):
            grad = direction_gradient(p, mu, cov, esg_scores, gamma, lambda_esg)
            local_step = step_size
            improved = False

            for _ in range(20):
                candidate = project_to_simplex(p + local_step * grad)
                cand_obj = direction_objective(candidate, mu, cov, esg_scores, gamma, lambda_esg)
                if cand_obj >= current_obj - 1e-12:
                    p = candidate
                    current_obj = cand_obj
                    improved = True
                    break
                local_step *= 0.5

            if not improved:
                break

        if current_obj > best_obj:
            best_obj = current_obj
            best_p = p.copy()

    return best_p


def optimal_scale_for_direction(p: np.ndarray, mu: np.ndarray, cov: np.ndarray, gamma: float) -> float:
    a = float(np.dot(p, mu))
    b = float(np.dot(p, np.dot(cov, p)))
    if gamma <= 1e-12 or b <= 1e-12:
        return 0.0
    return max(0.0, a / (gamma * b))


def solve_optimal_portfolio(
    mu: np.ndarray,
    cov: np.ndarray,
    esg_scores: np.ndarray,
    gamma: float,
    lambda_esg: float,
    rf: float,
    asset_names: list[str],
) -> tuple[pd.Series, pd.DataFrame]:
    p_star = solve_direction_simplex(mu, cov, esg_scores, gamma, lambda_esg)
    alpha_star = optimal_scale_for_direction(p_star, mu, cov, gamma)
    x_star = alpha_star * p_star
    metrics = portfolio_metrics(x_star, mu, cov, rf, esg_scores, gamma, lambda_esg)

    optimal_row = {
        **{f"Weight {asset_names[i]}": float(x_star[i]) for i in range(len(asset_names))},
        **metrics,
    }

    weight_table = pd.DataFrame(
        {
            "Asset": asset_names,
            "Risky Weight": x_star,
            "Direction Share (within risky assets)": p_star,
            "ESG Score": esg_scores,
            "Expected Return": mu,
        }
    ).sort_values("Risky Weight", ascending=False).reset_index(drop=True)

    return pd.Series(optimal_row), weight_table


def build_two_asset_risky_frontier(
    mu: np.ndarray,
    sigma: np.ndarray,
    rho: float,
    rf: float,
    esg_scores: np.ndarray,
    mix_points: int,
) -> pd.DataFrame:
    cov = var_covar(sigma, rho)
    rows = []

    for p1 in np.linspace(0.0, 1.0, mix_points):
        p = np.array([p1, 1.0 - p1], dtype=float)
        risky_return = float(np.dot(p, mu))
        variance = float(np.dot(p, np.dot(cov, p)))
        std_dev = float(np.sqrt(max(variance, 0.0)))
        avg_esg = float(np.dot(p, esg_scores))
        sharpe = np.nan if std_dev <= 1e-12 else (risky_return - rf) / std_dev
        rows.append(
            {
                "Mix Asset 1": p1,
                "Mix Asset 2": 1.0 - p1,
                "Risky Return": risky_return,
                "Std Dev": std_dev,
                "Average ESG": avg_esg,
                "Sharpe Ratio": sharpe,
            }
        )

    return pd.DataFrame(rows)


def esg_frontier_cutoff(frontier_df: pd.DataFrame, lambda_esg: float) -> float:
    s_min = float(frontier_df["Average ESG"].min())
    s_max = float(frontier_df["Average ESG"].max())
    return s_min + lambda_esg * (s_max - s_min)


def tangency_from_frontier(frontier_df: pd.DataFrame) -> pd.Series:
    valid = frontier_df[np.isfinite(frontier_df["Sharpe Ratio"])].copy()
    return valid.loc[valid["Sharpe Ratio"].idxmax()].copy()


def min_variance_from_frontier(frontier_df: pd.DataFrame) -> pd.Series:
    return frontier_df.loc[frontier_df["Std Dev"].idxmin()].copy()


def plot_frontier_cml(ax, frontier_df: pd.DataFrame, rf: float, color: str, tangency_label: str):
    x = frontier_df["Std Dev"] * 100
    y = frontier_df["Risky Return"] * 100
    tan = tangency_from_frontier(frontier_df)
    rf_plot = rf * 100

    ax.plot(x, y, color=color, linewidth=2.5)
    sigma_line = np.linspace(0.0, max(float(x.max()), float(tan["Std Dev"] * 100)) * 1.10, 200)
    cml = rf_plot + float(tan["Sharpe Ratio"]) * sigma_line
    ax.plot(sigma_line, cml, color=color, linewidth=1.8, linestyle=(0, (3, 3)))
    ax.scatter([0], [rf_plot], color=LIGHT_GREY, s=35, zorder=3)
    ax.scatter([tan["Std Dev"] * 100], [tan["Risky Return"] * 100], color=color, marker="*", s=110, zorder=4)
    ax.annotate(
        tangency_label,
        xy=(tan["Std Dev"] * 100, tan["Risky Return"] * 100),
        xytext=(16, -14),
        textcoords="offset points",
        color=color,
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color=color, lw=1.1),
    )
    return tan


def invert_covariance(cov: np.ndarray) -> np.ndarray:
    cov = np.asarray(cov, dtype=float)
    cov = (cov + cov.T) / 2.0
    cov = cov + np.eye(cov.shape[0]) * 1e-10
    return np.linalg.pinv(cov)


def frontier_constants(mu: np.ndarray, cov: np.ndarray):
    inv_cov = invert_covariance(cov)
    ones = np.ones(len(mu))
    A = float(ones @ inv_cov @ ones)
    B = float(ones @ inv_cov @ mu)
    C = float(mu @ inv_cov @ mu)
    D = max(A * C - B ** 2, 1e-12)
    return inv_cov, ones, A, B, C, D


def gmv_weights_frontier(mu: np.ndarray, cov: np.ndarray) -> np.ndarray:
    inv_cov, ones, A, _, _, _ = frontier_constants(mu, cov)
    return (inv_cov @ ones) / A


def target_return_weights_frontier(mu: np.ndarray, cov: np.ndarray, target_return: float) -> np.ndarray:
    inv_cov, ones, A, B, C, D = frontier_constants(mu, cov)
    alpha = (C - B * target_return) / D
    beta = (A * target_return - B) / D
    return inv_cov @ (alpha * ones + beta * mu)


def build_risky_frontier_visual(
    mu: np.ndarray,
    cov: np.ndarray,
    esg_scores: np.ndarray,
    rf: float,
    frontier_points: int = 80,
):
    mu = np.asarray(mu, dtype=float)
    cov = np.asarray(cov, dtype=float)
    esg_scores = np.asarray(esg_scores, dtype=float)

    w_gmv = gmv_weights_frontier(mu, cov)
    gmv_return = float(w_gmv @ mu)
    gmv_variance = float(w_gmv @ cov @ w_gmv)
    gmv_std = float(np.sqrt(max(gmv_variance, 0.0)))
    gmv_esg = float(w_gmv @ esg_scores)
    gmv_sharpe = np.nan if gmv_std <= 1e-12 else (gmv_return - rf) / gmv_std

    target_min = float(min(mu.min(), gmv_return))
    target_max = float(max(mu.max(), gmv_return))
    if np.isclose(target_min, target_max):
        target_max = target_min + 1e-6

    rows = []
    for target in np.linspace(target_min, target_max, frontier_points):
        w = target_return_weights_frontier(mu, cov, target)
        exp_return = float(w @ mu)
        variance = float(w @ cov @ w)
        std_dev = float(np.sqrt(max(variance, 0.0)))
        avg_esg = float(w @ esg_scores)
        sharpe = np.nan if std_dev <= 1e-12 else (exp_return - rf) / std_dev
        rows.append(
            {
                "Expected Return": exp_return,
                "Risky Return": exp_return,
                "Variance": variance,
                "Std Dev": std_dev,
                "Average ESG": avg_esg,
                "Sharpe Ratio": sharpe,
            }
        )

    frontier = pd.DataFrame(rows).sort_values("Std Dev").reset_index(drop=True)
    frontier["Efficient"] = frontier["Expected Return"] >= gmv_return - 1e-12
    gmv = {
        "Expected Return": gmv_return,
        "Risky Return": gmv_return,
        "Variance": gmv_variance,
        "Std Dev": gmv_std,
        "Average ESG": gmv_esg,
        "Sharpe Ratio": gmv_sharpe,
        "Weights": w_gmv,
    }
    return frontier, gmv


def min_esg_cutoff_from_scores(scores: np.ndarray, lambda_esg: float) -> float:
    scores = np.asarray(scores, dtype=float)
    return float(np.min(scores) + lambda_esg * (np.max(scores) - np.min(scores)))


def compact_optimal_summary(case_name: str, optimal_row: pd.Series, investment_amount: float) -> dict:
    return {
        "Case": case_name,
        "Expected Return": float(optimal_row["Expected Return"]),
        "Std Dev": float(optimal_row["Std Dev"]),
        "Risky Weight Sum": float(optimal_row["Risky Weight Sum"]),
        "Risk-free Weight": float(optimal_row["Risk-free Weight"]),
        "Average ESG": float(optimal_row["Average ESG"]),
        "Objective": float(optimal_row["Objective"]),
        "Amount in Risky Assets": float(optimal_row["Risky Weight Sum"]) * investment_amount,
        "Amount in Risk-free Asset": float(optimal_row["Risk-free Weight"]) * investment_amount,
    }


def audit_two_asset_solution(
    mu: np.ndarray,
    sigma: np.ndarray,
    rho: float,
    rf: float,
    esg_scores: np.ndarray,
    gamma: float,
    lambda_esg: float,
) -> dict:
    cov = var_covar(sigma, rho)

    opt_lambda0, _ = solve_optimal_portfolio(
        mu=mu,
        cov=cov,
        esg_scores=esg_scores,
        gamma=gamma,
        lambda_esg=0.0,
        rf=rf,
        asset_names=["Asset 1", "Asset 2"],
    )
    opt_lambda0_gamma2, _ = solve_optimal_portfolio(
        mu=mu,
        cov=cov,
        esg_scores=esg_scores,
        gamma=2.0 * gamma,
        lambda_esg=0.0,
        rf=rf,
        asset_names=["Asset 1", "Asset 2"],
    )
    opt_with_lambda, _ = solve_optimal_portfolio(
        mu=mu,
        cov=cov,
        esg_scores=esg_scores,
        gamma=gamma,
        lambda_esg=lambda_esg,
        rf=rf,
        asset_names=["Asset 1", "Asset 2"],
    )

    risky0 = float(opt_lambda0["Risky Weight Sum"])
    risky2 = float(opt_lambda0_gamma2["Risky Weight Sum"])
    ratio = np.nan if risky0 <= 1e-12 else risky2 / risky0

    greener_idx = int(np.argmax(esg_scores))
    greener_weight = float(opt_with_lambda[f"Weight Asset {greener_idx + 1}"])
    browner_idx = 1 - greener_idx
    browner_weight = float(opt_with_lambda[f"Weight Asset {browner_idx + 1}"])

    corner_solution = browner_weight <= 1e-8

    corner_x = np.zeros(2)
    corner_x[greener_idx] = optimal_scale_for_direction(np.eye(2)[greener_idx], mu, cov, gamma)
    corner_obj = objective_value(corner_x, mu, cov, gamma, lambda_esg, esg_scores)
    interior_x = np.array(
        [
            float(opt_with_lambda["Weight Asset 1"]),
            float(opt_with_lambda["Weight Asset 2"]),
        ]
    )
    interior_obj = objective_value(interior_x, mu, cov, gamma, lambda_esg, esg_scores)

    identical_mu = np.array([mu[0], mu[0]])
    identical_esg = np.array([esg_scores[0], esg_scores[0]])
    opt_symmetric, _ = solve_optimal_portfolio(
        mu=identical_mu,
        cov=cov,
        esg_scores=identical_esg,
        gamma=gamma,
        lambda_esg=0.0,
        rf=rf,
        asset_names=["Asset 1", "Asset 2"],
    )

    return {
        "Risky sum (lambda=0)": risky0,
        "Risky sum after doubling gamma (lambda=0)": risky2,
        "Gamma-doubling ratio": ratio,
        "Weight in greener asset": greener_weight,
        "Weight in browner asset": browner_weight,
        "Corner solution detected": corner_solution,
        "Corner objective": corner_obj,
        "Interior objective": interior_obj,
        "Symmetry check weight asset 1": float(opt_symmetric["Weight Asset 1"]),
        "Symmetry check weight asset 2": float(opt_symmetric["Weight Asset 2"]),
    }


@st.cache_data
def sample_simplex_cloud(n_assets: int, n_samples: int, seed: int = 123) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.dirichlet(np.ones(n_assets), size=n_samples)


def build_stock_objective_cloud(
    p_cloud: np.ndarray,
    mu: np.ndarray,
    cov: np.ndarray,
    rf: float,
    esg_scores: np.ndarray,
    gamma: float,
    lambda_esg: float,
) -> pd.DataFrame:
    rows = []
    for p in p_cloud:
        alpha = optimal_scale_for_direction(p, mu, cov, gamma)
        x = alpha * p
        metrics = portfolio_metrics(x, mu, cov, rf, esg_scores, gamma, lambda_esg)
        rows.append(metrics)
    return pd.DataFrame(rows)


# =========================================================
# Formatting helpers
# =========================================================
def add_currency_columns(optimal_row: pd.Series, investment_amount: float) -> pd.Series:
    out = optimal_row.copy()
    weight_cols = [c for c in out.index if c.startswith("Weight ")]
    for col in weight_cols:
        asset_name = col.replace("Weight ", "", 1)
        out[f"Amount {asset_name}"] = float(out[col]) * investment_amount
    out["Amount in Risky Assets"] = float(out["Risky Weight Sum"]) * investment_amount
    out["Amount in Risk-free Asset"] = float(out["Risk-free Weight"]) * investment_amount
    return out


def add_currency_to_weight_table(weight_table: pd.DataFrame, investment_amount: float) -> pd.DataFrame:
    out = weight_table.copy()
    out["Amount Invested"] = out["Risky Weight"] * investment_amount
    return out


def format_optimal_summary(df: pd.DataFrame):
    format_map = {col: "{:.3f}" for col in df.columns if col.startswith("Weight ")}
    format_map.update({col: "£{:,.2f}" for col in df.columns if col.startswith("Amount ")})
    format_map.update(
        {
            "Expected Return": "{:.2%}",
            "Variance": "{:.5f}",
            "Std Dev": "{:.2%}",
            "Risky Weight Sum": "{:.3f}",
            "Risk-free Weight": "{:.3f}",
            "Average ESG": "{:.2%}",
            "Objective": "{:.4f}",
            "Sharpe Ratio": "{:.3f}",
        }
    )
    return df.style.format(format_map)


def format_weight_table(df: pd.DataFrame):
    format_map = {
        "Risky Weight": "{:.3f}",
        "Direction Share (within risky assets)": "{:.2%}",
        "ESG Score": "{:.2%}",
        "Expected Return": "{:.2%}",
    }
    if "Amount Invested" in df.columns:
        format_map["Amount Invested"] = "£{:,.2f}"
    return df.style.format(format_map)


# =========================================================
# Rendering helpers
# =========================================================
def render_theoretical_tab(mu, sigma, rho, rf, esg_scores, gamma, lambda_esg, mix_points):
    investment_amount = float(st.session_state.investment_amount)
    cov = var_covar(sigma, rho)

    benchmark_opt, benchmark_weights = solve_optimal_portfolio(
        mu=mu,
        cov=cov,
        esg_scores=esg_scores,
        gamma=gamma,
        lambda_esg=0.0,
        rf=rf,
        asset_names=["Asset 1", "Asset 2"],
    )
    esg_opt, esg_weights = solve_optimal_portfolio(
        mu=mu,
        cov=cov,
        esg_scores=esg_scores,
        gamma=gamma,
        lambda_esg=lambda_esg,
        rf=rf,
        asset_names=["Asset 1", "Asset 2"],
    )

    audit = audit_two_asset_solution(mu, sigma, rho, rf, esg_scores, gamma, lambda_esg)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Risk aversion γ", f"{gamma:.2f}")
    m2.metric("ESG taste λ", f"{lambda_esg:.2f}")
    m3.metric("Benchmark risky sum", f"{benchmark_opt['Risky Weight Sum']:.3f}")
    m4.metric("ESG-optimal risky sum", f"{esg_opt['Risky Weight Sum']:.3f}")

    st.subheader("Objective-optimal portfolio: λ = 0 benchmark")
    st.dataframe(
        format_optimal_summary(pd.DataFrame([add_currency_columns(benchmark_opt, investment_amount)])),
        use_container_width=True,
    )

    st.subheader("Objective-optimal portfolio: chosen ESG taste")
    st.dataframe(
        format_optimal_summary(pd.DataFrame([add_currency_columns(esg_opt, investment_amount)])),
        use_container_width=True,
    )

    st.subheader("Audit checks")
    st.dataframe(
        pd.DataFrame([audit]).style.format(
            {
                "Risky sum (lambda=0)": "{:.3f}",
                "Risky sum after doubling gamma (lambda=0)": "{:.3f}",
                "Gamma-doubling ratio": "{:.3f}",
                "Weight in greener asset": "{:.3f}",
                "Weight in browner asset": "{:.3f}",
                "Corner objective": "{:.4f}",
                "Interior objective": "{:.4f}",
                "Symmetry check weight asset 1": "{:.3f}",
                "Symmetry check weight asset 2": "{:.3f}",
            }
        ),
        use_container_width=True,
    )

    if bool(audit["Corner solution detected"]):
        st.warning(
            "Corner solution detected. This is economically meaningful: at this ESG preference level, holding the brown asset is not optimal."
        )

    st.subheader("Risky-asset weights: λ = 0 benchmark")
    st.dataframe(
        format_weight_table(add_currency_to_weight_table(benchmark_weights, investment_amount)),
        use_container_width=True,
    )

    st.subheader("Risky-asset weights: chosen ESG taste")
    st.dataframe(
        format_weight_table(add_currency_to_weight_table(esg_weights, investment_amount)),
        use_container_width=True,
    )


def render_frontier_visual_tab(mu, sigma, rho, rf, esg_scores, gamma, lambda_esg, mix_points):
    investment_amount = float(st.session_state.investment_amount)

    # Stock-based visuals for first-time users and "find assets" users
    if st.session_state.beginner_mode or is_experienced_find_mode():
        try:
            firms, daily_cov, corr = load_fast_workbook()
            annual_cov = annualise_covariance(daily_cov, st.session_state.trading_days)

            mu_all = firms["Expected Return"].to_numpy(dtype=float)
            esg_all = firms["ESG Score"].to_numpy(dtype=float)
            cov_all = annual_cov.loc[firms["Ticker"], firms["Ticker"]].to_numpy(dtype=float)
            asset_names_all = firms["Ticker"].tolist()

            frontier_points = max(60, min(200, mix_points // 10))
            frontier_all, _ = build_risky_frontier_visual(mu_all, cov_all, esg_all, rf, frontier_points)

            cutoff = min_esg_cutoff_from_scores(esg_all, lambda_esg)
            firms_esg = firms[firms["ESG Score"] >= cutoff].copy().reset_index(drop=True)

            st.subheader("Frontier and CML visualisation")
            st.caption(
                "These graphs are built from all stocks in the workbook. The ESG frontier uses only the stocks that meet the minimum ESG criterion implied by your ESG preference."
            )
            st.write(f"Stocks available in workbook: **{len(firms)}**")
            st.write(f"Stocks meeting ESG cutoff: **{len(firms_esg)}**")

            if len(firms_esg) < 2:
                st.warning("Fewer than 2 stocks meet the ESG cutoff, so the ESG frontier cannot be plotted reliably.")
                return

            mu_esg = firms_esg["Expected Return"].to_numpy(dtype=float)
            esg_esg = firms_esg["ESG Score"].to_numpy(dtype=float)
            cov_esg = annual_cov.loc[firms_esg["Ticker"], firms_esg["Ticker"]].to_numpy(dtype=float)
            frontier_esg, _ = build_risky_frontier_visual(mu_esg, cov_esg, esg_esg, rf, frontier_points)

            tan_all = tangency_from_frontier(frontier_all)
            mvp_all = min_variance_from_frontier(frontier_all)
            tan_esg = tangency_from_frontier(frontier_esg)
            mvp_esg = min_variance_from_frontier(frontier_esg)

            # Graph 1: all stocks
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            plot_frontier_cml(ax1, frontier_all, rf, THEORETICAL_BLUE, "highest Sharpe portfolio")
            ax1.scatter(
                [mvp_all["Std Dev"] * 100],
                [mvp_all["Risky Return"] * 100],
                color=THEORETICAL_BLUE,
                marker="s",
                s=55,
                zorder=5,
            )
            ax1.annotate(
                "minimum variance portfolio",
                xy=(mvp_all["Std Dev"] * 100, mvp_all["Risky Return"] * 100),
                xytext=(15, -18),
                textcoords="offset points",
                color=THEORETICAL_BLUE,
                fontsize=9,
                arrowprops=dict(arrowstyle="->", color=THEORETICAL_BLUE, lw=1.1),
            )
            ax1.set_xlabel("Std")
            ax1.set_ylabel("Expected return")
            ax1.set_title("All-stock frontier without ESG consideration")
            style_axis(ax1)
            st.pyplot(fig1)

            # Graph 2: ESG-screened stocks
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            ax2.plot(
                frontier_all["Std Dev"] * 100,
                frontier_all["Risky Return"] * 100,
                color=THEORETICAL_BLUE,
                linewidth=2.1,
                alpha=0.7,
            )
            plot_frontier_cml(ax2, frontier_esg, rf, ESG_GREEN, "ESG highest Sharpe portfolio")
            ax2.scatter(
                [mvp_esg["Std Dev"] * 100],
                [mvp_esg["Risky Return"] * 100],
                color=ESG_GREEN,
                marker="s",
                s=55,
                zorder=5,
            )
            ax2.annotate(
                "ESG minimum variance portfolio",
                xy=(mvp_esg["Std Dev"] * 100, mvp_esg["Risky Return"] * 100),
                xytext=(-120, 12),
                textcoords="offset points",
                color=ESG_GREEN,
                fontsize=9,
                arrowprops=dict(arrowstyle="->", color=ESG_GREEN, lw=1.1),
            )
            ax2.set_xlabel("Std")
            ax2.set_ylabel("Expected return")
            ax2.set_title("ESG frontier from stocks meeting the minimum ESG criterion")
            style_axis(ax2)
            st.pyplot(fig2)

            # Graph 3: compare MVP and highest Sharpe
            fig3, ax3 = plt.subplots(figsize=(10, 6))
            ax3.plot(
                frontier_all["Std Dev"] * 100,
                frontier_all["Risky Return"] * 100,
                color=THEORETICAL_BLUE,
                linewidth=2.2,
            )
            ax3.plot(
                frontier_esg["Std Dev"] * 100,
                frontier_esg["Risky Return"] * 100,
                color=ESG_GREEN,
                linewidth=2.2,
            )
            ax3.scatter(
                [mvp_all["Std Dev"] * 100],
                [mvp_all["Risky Return"] * 100],
                color=THEORETICAL_BLUE,
                marker="s",
                s=60,
                zorder=5,
            )
            ax3.scatter(
                [tan_all["Std Dev"] * 100],
                [tan_all["Risky Return"] * 100],
                color=THEORETICAL_BLUE,
                marker="*",
                s=110,
                zorder=5,
            )
            ax3.scatter(
                [mvp_esg["Std Dev"] * 100],
                [mvp_esg["Risky Return"] * 100],
                color=ESG_GREEN,
                marker="s",
                s=60,
                zorder=5,
            )
            ax3.scatter(
                [tan_esg["Std Dev"] * 100],
                [tan_esg["Risky Return"] * 100],
                color=ESG_GREEN,
                marker="*",
                s=110,
                zorder=5,
            )
            ax3.annotate(
                "MVP without ESG",
                xy=(mvp_all["Std Dev"] * 100, mvp_all["Risky Return"] * 100),
                xytext=(14, -18),
                textcoords="offset points",
                color=THEORETICAL_BLUE,
                fontsize=9,
            )
            ax3.annotate(
                "Highest Sharpe without ESG",
                xy=(tan_all["Std Dev"] * 100, tan_all["Risky Return"] * 100),
                xytext=(-120, 10),
                textcoords="offset points",
                color=THEORETICAL_BLUE,
                fontsize=9,
            )
            ax3.annotate(
                "MVP with ESG",
                xy=(mvp_esg["Std Dev"] * 100, mvp_esg["Risky Return"] * 100),
                xytext=(14, 8),
                textcoords="offset points",
                color=ESG_GREEN,
                fontsize=9,
            )
            ax3.annotate(
                "Highest Sharpe with ESG",
                xy=(tan_esg["Std Dev"] * 100, tan_esg["Risky Return"] * 100),
                xytext=(16, -16),
                textcoords="offset points",
                color=ESG_GREEN,
                fontsize=9,
            )
            ax3.set_xlabel("Std")
            ax3.set_ylabel("Expected return")
            ax3.set_title("Minimum variance and highest Sharpe portfolios")
            style_axis(ax3)
            st.pyplot(fig3)

            benchmark_opt, _ = solve_optimal_portfolio(
                mu_all, cov_all, esg_all, gamma, 0.0, rf, asset_names_all
            )
            esg_opt, _ = solve_optimal_portfolio(
                mu_all, cov_all, esg_all, gamma, lambda_esg, rf, asset_names_all
            )

            compare_df = pd.DataFrame(
                [
                    compact_optimal_summary(
                        "Objective-optimal without ESG taste",
                        benchmark_opt,
                        investment_amount,
                    ),
                    compact_optimal_summary(
                        "Objective-optimal with ESG taste",
                        esg_opt,
                        investment_amount,
                    ),
                ]
            )

            st.subheader("Optimal portfolio details for comparison")
            st.dataframe(
                compare_df.style.format(
                    {
                        "Expected Return": "{:.2%}",
                        "Std Dev": "{:.2%}",
                        "Risky Weight Sum": "{:.3f}",
                        "Risk-free Weight": "{:.3f}",
                        "Average ESG": "{:.2%}",
                        "Objective": "{:.4f}",
                        "Amount in Risky Assets": "£{:,.2f}",
                        "Amount in Risk-free Asset": "£{:,.2f}",
                    }
                ),
                use_container_width=True,
            )
            return

        except Exception as e:
            st.error(f"Could not build the frontier visualisation from the workbook: {e}")
            return

    # Theoretical visuals for experienced users with their own 2-asset inputs
    cov = var_covar(sigma, rho)
    benchmark_opt, _ = solve_optimal_portfolio(mu, cov, esg_scores, gamma, 0.0, rf, ["Asset 1", "Asset 2"])
    esg_opt, _ = solve_optimal_portfolio(mu, cov, esg_scores, gamma, lambda_esg, rf, ["Asset 1", "Asset 2"])

    frontier_all = build_two_asset_risky_frontier(mu, sigma, rho, rf, esg_scores, mix_points)
    cutoff = esg_frontier_cutoff(frontier_all, lambda_esg)
    frontier_esg = frontier_all[frontier_all["Average ESG"] >= cutoff - 1e-12].copy()
    if frontier_esg.empty:
        frontier_esg = frontier_all.loc[[frontier_all["Average ESG"].idxmax()]].copy()

    tan_all = tangency_from_frontier(frontier_all)
    mvp_all = min_variance_from_frontier(frontier_all)
    tan_esg = tangency_from_frontier(frontier_esg)
    mvp_esg = min_variance_from_frontier(frontier_esg)

    st.subheader("Frontier and CML visualisation")
    st.caption("These graphs are theoretical and use your 2-asset inputs directly.")

    fig1, ax1 = plt.subplots(figsize=(10, 6))
    plot_frontier_cml(ax1, frontier_all, rf, THEORETICAL_BLUE, "highest Sharpe portfolio")
    ax1.scatter(
        [benchmark_opt["Std Dev"] * 100],
        [benchmark_opt["Expected Return"] * 100],
        color=THEORETICAL_BLUE,
        s=65,
        zorder=5,
    )
    ax1.scatter(
        [mvp_all["Std Dev"] * 100],
        [mvp_all["Risky Return"] * 100],
        color=THEORETICAL_BLUE,
        marker="s",
        s=55,
        zorder=5,
    )
    ax1.annotate(
        "objective-optimal portfolio",
        xy=(benchmark_opt["Std Dev"] * 100, benchmark_opt["Expected Return"] * 100),
        xytext=(-90, 12),
        textcoords="offset points",
        color=THEORETICAL_BLUE,
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color=THEORETICAL_BLUE, lw=1.2),
    )
    ax1.annotate(
        "minimum variance portfolio",
        xy=(mvp_all["Std Dev"] * 100, mvp_all["Risky Return"] * 100),
        xytext=(15, -18),
        textcoords="offset points",
        color=THEORETICAL_BLUE,
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color=THEORETICAL_BLUE, lw=1.1),
    )
    ax1.set_xlabel("Std")
    ax1.set_ylabel("Expected return")
    ax1.set_title("Without ESG consideration")
    style_axis(ax1)
    st.pyplot(fig1)

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    ax2.plot(
        frontier_all["Std Dev"] * 100,
        frontier_all["Risky Return"] * 100,
        color=THEORETICAL_BLUE,
        linewidth=2.1,
        alpha=0.7,
    )
    plot_frontier_cml(ax2, frontier_esg, rf, ESG_GREEN, "ESG highest Sharpe portfolio")
    ax2.scatter(
        [esg_opt["Std Dev"] * 100],
        [esg_opt["Expected Return"] * 100],
        color=ESG_GREEN,
        s=65,
        zorder=5,
    )
    ax2.scatter(
        [mvp_esg["Std Dev"] * 100],
        [mvp_esg["Risky Return"] * 100],
        color=ESG_GREEN,
        marker="s",
        s=55,
        zorder=5,
    )
    ax2.annotate(
        "objective-optimal portfolio",
        xy=(esg_opt["Std Dev"] * 100, esg_opt["Expected Return"] * 100),
        xytext=(18, -16),
        textcoords="offset points",
        color=ESG_GREEN,
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color=ESG_GREEN, lw=1.2),
    )
    ax2.annotate(
        "ESG minimum variance portfolio",
        xy=(mvp_esg["Std Dev"] * 100, mvp_esg["Risky Return"] * 100),
        xytext=(-120, 12),
        textcoords="offset points",
        color=ESG_GREEN,
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color=ESG_GREEN, lw=1.1),
    )
    ax2.set_xlabel("Std")
    ax2.set_ylabel("Expected return")
    ax2.set_title("With ESG consideration")
    style_axis(ax2)
    st.pyplot(fig2)

    fig3, ax3 = plt.subplots(figsize=(10, 6))
    ax3.plot(
        frontier_all["Std Dev"] * 100,
        frontier_all["Risky Return"] * 100,
        color=THEORETICAL_BLUE,
        linewidth=2.2,
    )
    ax3.plot(
        frontier_esg["Std Dev"] * 100,
        frontier_esg["Risky Return"] * 100,
        color=ESG_GREEN,
        linewidth=2.2,
    )
    ax3.scatter(
        [mvp_all["Std Dev"] * 100],
        [mvp_all["Risky Return"] * 100],
        color=THEORETICAL_BLUE,
        marker="s",
        s=60,
        zorder=5,
    )
    ax3.scatter(
        [tan_all["Std Dev"] * 100],
        [tan_all["Risky Return"] * 100],
        color=THEORETICAL_BLUE,
        marker="*",
        s=110,
        zorder=5,
    )
    ax3.scatter(
        [mvp_esg["Std Dev"] * 100],
        [mvp_esg["Risky Return"] * 100],
        color=ESG_GREEN,
        marker="s",
        s=60,
        zorder=5,
    )
    ax3.scatter(
        [tan_esg["Std Dev"] * 100],
        [tan_esg["Risky Return"] * 100],
        color=ESG_GREEN,
        marker="*",
        s=110,
        zorder=5,
    )
    ax3.annotate(
        "MVP without ESG",
        xy=(mvp_all["Std Dev"] * 100, mvp_all["Risky Return"] * 100),
        xytext=(14, -18),
        textcoords="offset points",
        color=THEORETICAL_BLUE,
        fontsize=9,
    )
    ax3.annotate(
        "Highest Sharpe without ESG",
        xy=(tan_all["Std Dev"] * 100, tan_all["Risky Return"] * 100),
        xytext=(-120, 10),
        textcoords="offset points",
        color=THEORETICAL_BLUE,
        fontsize=9,
    )
    ax3.annotate(
        "MVP with ESG",
        xy=(mvp_esg["Std Dev"] * 100, mvp_esg["Risky Return"] * 100),
        xytext=(14, 8),
        textcoords="offset points",
        color=ESG_GREEN,
        fontsize=9,
    )
    ax3.annotate(
        "Highest Sharpe with ESG",
        xy=(tan_esg["Std Dev"] * 100, tan_esg["Risky Return"] * 100),
        xytext=(16, -16),
        textcoords="offset points",
        color=ESG_GREEN,
        fontsize=9,
    )
    ax3.set_xlabel("Std")
    ax3.set_ylabel("Expected return")
    ax3.set_title("Minimum variance and highest Sharpe portfolios")
    style_axis(ax3)
    st.pyplot(fig3)


def render_stock_tab(lambda_esg: float, gamma: float, rf: float):
    investment_amount = float(st.session_state.investment_amount)

    st.subheader("Stock-universe objective optimisation")
    st.markdown(
        """
        This tab maximises the same objective function over the stock universe:

        max  x'μ  −  (γ/2) x'Σx  +  λ · s̄

        where the risky weights do not need to sum to one, and the remainder is implicitly held in the risk-free asset.
        """
    )

    try:
        firms, daily_cov, corr = load_fast_workbook()
        annual_cov = annualise_covariance(daily_cov, st.session_state.trading_days)

        mu = firms["Expected Return"].to_numpy(dtype=float)
        esg_scores = firms["ESG Score"].to_numpy(dtype=float)
        cov = annual_cov.loc[firms["Ticker"], firms["Ticker"]].to_numpy(dtype=float)
        names = firms["Ticker"].tolist()

        benchmark_opt, benchmark_weights = solve_optimal_portfolio(
            mu=mu,
            cov=cov,
            esg_scores=esg_scores,
            gamma=gamma,
            lambda_esg=0.0,
            rf=rf,
            asset_names=names,
        )
        esg_opt, esg_weights = solve_optimal_portfolio(
            mu=mu,
            cov=cov,
            esg_scores=esg_scores,
            gamma=gamma,
            lambda_esg=lambda_esg,
            rf=rf,
            asset_names=names,
        )

        p_cloud = sample_simplex_cloud(len(names), st.session_state.sample_points)
        cloud_benchmark = build_stock_objective_cloud(
            p_cloud, mu, cov, rf, esg_scores, gamma, 0.0
        )
        cloud_esg = build_stock_objective_cloud(
            p_cloud, mu, cov, rf, esg_scores, gamma, lambda_esg
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Stocks in universe", f"{len(firms)}")
        m2.metric("Risk aversion γ", f"{gamma:.2f}")
        m3.metric("Benchmark risky sum", f"{benchmark_opt['Risky Weight Sum']:.3f}")
        m4.metric("ESG-optimal risky sum", f"{esg_opt['Risky Weight Sum']:.3f}")

        st.subheader("Objective-optimal stock portfolio: λ = 0 benchmark")
        st.dataframe(
            format_optimal_summary(pd.DataFrame([add_currency_columns(benchmark_opt, investment_amount)])),
            use_container_width=True,
        )

        st.subheader("Objective-optimal stock portfolio: chosen ESG taste")
        st.dataframe(
            format_optimal_summary(pd.DataFrame([add_currency_columns(esg_opt, investment_amount)])),
            use_container_width=True,
        )

        st.subheader("Stock-universe objective plot")
        fig, ax = plt.subplots(figsize=(11, 6))
        ax.scatter(
            cloud_benchmark["Std Dev"] * 100,
            cloud_benchmark["Expected Return"] * 100,
            color=THEORETICAL_BLUE,
            alpha=0.08,
            s=12,
        )
        ax.scatter(
            cloud_esg["Std Dev"] * 100,
            cloud_esg["Expected Return"] * 100,
            color=ESG_GREEN,
            alpha=0.08,
            s=12,
        )
        ax.scatter(
            [benchmark_opt["Std Dev"] * 100],
            [benchmark_opt["Expected Return"] * 100],
            color=THEORETICAL_BLUE,
            s=70,
            zorder=5,
        )
        ax.scatter(
            [esg_opt["Std Dev"] * 100],
            [esg_opt["Expected Return"] * 100],
            color=ESG_GREEN,
            s=70,
            zorder=5,
        )
        ax.annotate(
            "benchmark optimum\n(lambda = 0)",
            xy=(benchmark_opt["Std Dev"] * 100, benchmark_opt["Expected Return"] * 100),
            xytext=(-70, 12),
            textcoords="offset points",
            color=THEORETICAL_BLUE,
            fontsize=9,
            arrowprops=dict(arrowstyle="->", color=THEORETICAL_BLUE, lw=1.2),
        )
        ax.annotate(
            "ESG-taste optimum",
            xy=(esg_opt["Std Dev"] * 100, esg_opt["Expected Return"] * 100),
            xytext=(16, -16),
            textcoords="offset points",
            color=ESG_GREEN,
            fontsize=9,
            arrowprops=dict(arrowstyle="->", color=ESG_GREEN, lw=1.2),
        )
        ax.set_xlabel("Std")
        ax.set_ylabel("Expected return")
        style_axis(ax)
        st.pyplot(fig)

        st.subheader("Top stock weights: λ = 0 benchmark")
        st.dataframe(
            format_weight_table(add_currency_to_weight_table(benchmark_weights.head(15), investment_amount)),
            use_container_width=True,
        )

        st.subheader("Top stock weights: chosen ESG taste")
        st.dataframe(
            format_weight_table(add_currency_to_weight_table(esg_weights.head(15), investment_amount)),
            use_container_width=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "Download benchmark stock weights",
                benchmark_weights.to_csv(index=False).encode("utf-8"),
                "benchmark_stock_weights.csv",
                "text/csv",
            )
        with c2:
            st.download_button(
                "Download ESG stock weights",
                esg_weights.to_csv(index=False).encode("utf-8"),
                "esg_stock_weights.csv",
                "text/csv",
            )

    except Exception as e:
        st.error(f"Could not build the stock-universe optimisation from the workbook: {e}")


# =========================================================
# Questionnaire gate
# =========================================================
if st.session_state.page == "questionnaire" and not st.session_state.onboarding_complete:
    onboarding_dialog()
    st.title("EcoVest")
    st.info("Please complete the questionnaire to continue.")
    st.stop()


# =========================================================
# Landing page
# =========================================================
if st.session_state.page == "intro":
    st.title("EcoVest")
    st.markdown(
        """
        **EcoVest** is a sustainable finance app designed to help investors compare traditional portfolio choices with ESG-aware alternatives.

        The app can work in two ways. If you already have your own asset assumptions, it lets you test those inputs in a theoretical setting. If you are newer to investing, or you want help finding a stock combination, it can also use the workbook stock universe to compare a broad mean-variance frontier against an ESG-screened frontier.

        The process is simple:
        1. You answer a short questionnaire.
        2. EcoVest identifies the route that best fits your needs.
        3. You receive portfolio results, frontier visuals, and stock-based comparisons.

        The results you are likely to observe are:
        - how stronger ESG preferences can shrink the investable frontier,
        - how the minimum-variance and highest-Sharpe portfolios change,
        - and how the final recommended allocation translates into actual £ amounts.
        """
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Continue to questionnaire", use_container_width=True):
            go_to("questionnaire")
    with c2:
        if st.button("Meet the team", use_container_width=True):
            go_to("credits")


# =========================================================
# Credits page
# =========================================================
elif st.session_state.page == "credits":
    st.title("EcoVest Contributions")

    credits_df = pd.DataFrame(
        [
            {
                "Student": "Javier Alramahi",
                "Student ID": "230206379",
                "Main Responsibilities": "Poster Design & Content Development",
                "Secondary Support Tasks": "Concept Development & Innovation",
            },
            {
                "Student": "Alexander Michael Elgen",
                "Student ID": "230255447",
                "Main Responsibilities": "Poster Design & Content Development",
                "Secondary Support Tasks": "Concept Development & Innovation",
            },
            {
                "Student": "Octavian Gopcalo",
                "Student ID": "230319831",
                "Main Responsibilities": "App Development & Implementation",
                "Secondary Support Tasks": "Visual Enhancement & Poster Refinement",
            },
            {
                "Student": "Om Naik",
                "Student ID": "230255850",
                "Main Responsibilities": "App Development & Implementation",
                "Secondary Support Tasks": "Visual Enhancement & Poster Refinement",
            },
            {
                "Student": "Kai Qin Ong",
                "Student ID": "221120451",
                "Main Responsibilities": "App Development & Implementation",
                "Secondary Support Tasks": "Visual Enhancement & Poster Refinement",
            },
            {
                "Student": "Ravi Sapan Nileshkumar Patel",
                "Student ID": "231173454",
                "Main Responsibilities": "Poster Design & Content Development",
                "Secondary Support Tasks": "Concept Development & Innovation",
            },
        ]
    )
    st.dataframe(credits_df, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back to home", use_container_width=True):
            go_to("intro")
    with c2:
        if st.button("Continue to questionnaire", use_container_width=True):
            go_to("questionnaire")


# =========================================================
# Inputs page
# =========================================================
elif st.session_state.page == "inputs":
    if is_experienced_find_mode():
        st.title("Asset Finder Preferences")
        st.caption(
            "Experienced Investor path: choose your risk profile and ESG preferences below. The app will show stock-universe results built from the workbook data."
        )

        with st.form("stock_finder_form"):
            st.subheader("Choose your risk aversion level")
            st.caption(
                "Risk aversion measures how much you dislike uncertainty. A higher value means you prefer steadier outcomes and are likely to hold less risky exposure overall."
            )
            risk_choice = st.radio(
                "How risk averse are you?",
                ["Aggressive", "Balanced", "Conservative", "Custom"],
                index=(
                    1
                    if st.session_state.risk_profile not in ["Aggressive", "Balanced", "Conservative", "Custom"]
                    else ["Aggressive", "Balanced", "Conservative", "Custom"].index(st.session_state.risk_profile)
                ),
                key="experienced_find_risk_choice",
            )

            custom_gamma = float(st.session_state.gamma)
            if risk_choice == "Custom":
                custom_gamma = st.slider(
                    "Select your custom risk aversion value",
                    min_value=0.5,
                    max_value=10.0,
                    value=float(min(max(st.session_state.gamma, 0.5), 10.0)),
                    step=0.1,
                    key="experienced_find_custom_gamma",
                )
                st.caption("Please enter a value between 0.5 and 10.0.")

            st.markdown("---")
            st.subheader("Choose your ESG preference level")
            st.caption(
                "This controls how strongly EcoVest prioritises greener assets. Higher values give more importance to ESG and less to pure efficiency."
            )
            esg_choice = st.radio(
                "Please select a number that reflects your ESG preferences:",
                ["Low ESG Impact", "Medium ESG Impact", "High ESG Impact", "Custom"],
                index=(
                    1
                    if st.session_state.esg_profile not in ["Low ESG Impact", "Medium ESG Impact", "High ESG Impact", "Custom"]
                    else ["Low ESG Impact", "Medium ESG Impact", "High ESG Impact", "Custom"].index(st.session_state.esg_profile)
                ),
                key="experienced_find_esg_choice",
            )

            custom_lambda = float(st.session_state.lambda_esg)
            if esg_choice == "Custom":
                custom_lambda = st.slider(
                    "Select your custom ESG intensity value",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(min(max(st.session_state.lambda_esg, 0.0), 1.0)),
                    step=0.01,
                    key="experienced_find_custom_lambda",
                )
                st.caption("Please enter a value between 0.0 and 1.0.")

            st.markdown("---")
            st.subheader("Optimisation settings")
            sample_points = st.slider(
                "Random portfolios sampled for the stock-universe plot",
                500,
                10000,
                int(st.session_state.sample_points),
                500,
            )
            trading_days = st.slider(
                "Trading days used to annualise daily covariance",
                200,
                260,
                int(st.session_state.trading_days),
                1,
            )

            submitted = st.form_submit_button("Continue to results")

        if submitted:
            gamma_value = float(custom_gamma) if risk_choice == "Custom" else RISK_MAP[risk_choice]
            lambda_value = float(custom_lambda) if esg_choice == "Custom" else ESG_MAP[esg_choice]

            st.session_state.gamma = gamma_value
            st.session_state.lambda_esg = lambda_value
            st.session_state.risk_profile = risk_choice
            st.session_state.esg_profile = esg_choice
            st.session_state.sample_points = sample_points
            st.session_state.trading_days = trading_days
            go_to("results")

    else:
        st.title("Portfolio Inputs")

        if is_experienced_existing_mode():
            st.caption(
                "Experienced Investor path: enter your existing 2-asset assumptions below. The frontier visuals will remain theoretical."
            )
        else:
            st.caption("These are the current model assumptions. You can still edit them if you want.")

        st.write("Enter all percentages as values from 0 to 100.")

        with st.form("input_form"):
            st.subheader("Asset 1 inputs")
            mu1_pct = st.number_input(
                "Expected return for Asset 1 (%)",
                0.0,
                100.0,
                float(st.session_state.mu1_pct),
                0.25,
                format="%.2f",
            )
            sigma1_pct = st.number_input(
                "Volatility for Asset 1 (%)",
                0.01,
                100.0,
                float(st.session_state.sigma1_pct),
                0.25,
                format="%.2f",
            )
            esg1 = st.number_input(
                "ESG score for Asset 1 (0 to 100)",
                0.0,
                100.0,
                float(st.session_state.esg1),
                1.0,
                format="%.1f",
            )

            st.markdown("---")

            st.subheader("Asset 2 inputs")
            mu2_pct = st.number_input(
                "Expected return for Asset 2 (%)",
                0.0,
                100.0,
                float(st.session_state.mu2_pct),
                0.25,
                format="%.2f",
            )
            sigma2_pct = st.number_input(
                "Volatility for Asset 2 (%)",
                0.01,
                100.0,
                float(st.session_state.sigma2_pct),
                0.25,
                format="%.2f",
            )
            esg2 = st.number_input(
                "ESG score for Asset 2 (0 to 100)",
                0.0,
                100.0,
                float(st.session_state.esg2),
                1.0,
                format="%.1f",
            )

            st.markdown("---")

            st.subheader("Model inputs")
            rf_pct = st.number_input(
                "Risk-free rate (%)",
                0.0,
                100.0,
                float(st.session_state.rf_pct),
                0.25,
                format="%.2f",
            )
            rho = st.slider(
                "Correlation between Asset 1 and Asset 2",
                -1.0,
                1.0,
                float(st.session_state.rho),
                0.01,
            )
            mix_points = st.slider(
                "Points used for the two-asset plot",
                201,
                5001,
                int(st.session_state.mix_points),
                100,
            )

            st.markdown("---")

            st.subheader("Investor preferences")
            st.caption(
                "Risk aversion measures how strongly you penalise volatility. Please enter a value between 0.1 and 10.0."
            )
            gamma = st.number_input(
                "Risk aversion γ",
                min_value=0.1,
                max_value=10.0,
                value=float(min(max(st.session_state.gamma, 0.1), 10.0)),
                step=0.10,
                format="%.2f",
            )

            st.caption(
                "ESG preference intensity shows how strongly you value greener assets. Please enter a value between 0.0 and 1.0."
            )
            lambda_esg = st.slider(
                "ESG preference intensity λ",
                0.0,
                1.0,
                float(st.session_state.lambda_esg),
                0.01,
            )

            st.markdown("---")
            st.subheader("Stock-universe settings")
            sample_points = st.slider(
                "Random portfolios sampled for the stock-universe plot",
                500,
                10000,
                int(st.session_state.sample_points),
                500,
            )
            trading_days = st.slider(
                "Trading days used to annualise daily covariance",
                200,
                260,
                int(st.session_state.trading_days),
                1,
            )

            submitted = st.form_submit_button("Continue to results")

        if submitted:
            st.session_state.mu1_pct = mu1_pct
            st.session_state.mu2_pct = mu2_pct
            st.session_state.sigma1_pct = sigma1_pct
            st.session_state.sigma2_pct = sigma2_pct
            st.session_state.esg1 = esg1
            st.session_state.esg2 = esg2
            st.session_state.rf_pct = rf_pct
            st.session_state.rho = rho
            st.session_state.mix_points = mix_points
            st.session_state.lambda_esg = lambda_esg
            st.session_state.gamma = gamma
            st.session_state.sample_points = sample_points
            st.session_state.trading_days = trading_days
            go_to("results")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Go to results"):
            go_to("results")
    with c2:
        if st.button("Back to home"):
            go_to("intro")
    with c3:
        if st.button("Start over"):
            reset_onboarding()


# =========================================================
# Results page
# =========================================================
elif st.session_state.page == "results":
    st.title("EcoVest Results")
    st.caption(f"Investment amount entered in questionnaire: {format_gbp(float(st.session_state.investment_amount))}")

    show_theoretical = is_experienced_existing_mode() or st.session_state.beginner_mode
    show_stock = is_experienced_find_mode() or st.session_state.beginner_mode

    if st.session_state.beginner_mode:
        st.success(
            f"First-time user mode active. Risk aversion γ = {st.session_state.gamma:.2f} and ESG intensity λ = {st.session_state.lambda_esg:.2f}."
        )
        st.caption("You are seeing both the theoretical optimisation view and the stock-universe view.")
    elif is_experienced_existing_mode():
        st.info(
            "Experienced Investor path: the main optimisation uses your own 2-asset inputs and the frontier visuals remain theoretical."
        )
    elif is_experienced_find_mode():
        st.info(
            "Experienced Investor path: the app is using the workbook stock universe to build your frontiers and portfolio suggestions."
        )

    mu = np.array([st.session_state.mu1_pct, st.session_state.mu2_pct]) / 100.0
    sigma = np.array([st.session_state.sigma1_pct, st.session_state.sigma2_pct]) / 100.0
    rf = st.session_state.rf_pct / 100.0
    rho = st.session_state.rho
    esg_scores = np.array([st.session_state.esg1, st.session_state.esg2]) / 100.0
    gamma = float(st.session_state.gamma)
    lambda_esg = float(st.session_state.lambda_esg)
    mix_points = int(st.session_state.mix_points)

    if show_theoretical and show_stock:
        tab1, tab_frontier, tab2 = st.tabs(
            [
                "Theoretical optimisation",
                "Frontier + CML visualisation",
                "Stock-universe optimisation",
            ]
        )
        with tab1:
            render_theoretical_tab(mu, sigma, rho, rf, esg_scores, gamma, lambda_esg, mix_points)
        with tab_frontier:
            render_frontier_visual_tab(mu, sigma, rho, rf, esg_scores, gamma, lambda_esg, mix_points)
        with tab2:
            render_stock_tab(lambda_esg=lambda_esg, gamma=gamma, rf=rf)

    elif show_theoretical:
        tab1, tab_frontier = st.tabs(
            [
                "Theoretical optimisation",
                "Frontier + CML visualisation",
            ]
        )
        with tab1:
            render_theoretical_tab(mu, sigma, rho, rf, esg_scores, gamma, lambda_esg, mix_points)
        with tab_frontier:
            render_frontier_visual_tab(mu, sigma, rho, rf, esg_scores, gamma, lambda_esg, mix_points)

    elif show_stock:
        tab_frontier, tab2 = st.tabs(
            [
                "Frontier + CML visualisation",
                "Stock-universe optimisation",
            ]
        )
        with tab_frontier:
            render_frontier_visual_tab(mu, sigma, rho, rf, esg_scores, gamma, lambda_esg, mix_points)
        with tab2:
            render_stock_tab(lambda_esg=lambda_esg, gamma=gamma, rf=rf)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Edit inputs"):
            go_to("inputs")
    with col2:
        if st.button("Back to home"):
            go_to("intro")
    with col3:
        if st.button("Refresh questionnaire"):
            reset_onboarding()
