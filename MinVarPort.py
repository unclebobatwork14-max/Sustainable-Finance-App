import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="ESG Portfolio Optimiser", layout="wide")

# =========================================================
# Defaults
# =========================================================
DEFAULTS = {
    "page": "inputs",
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
    "num_points": 1001,
    "frontier_points": 80,
    "trading_days": 252,
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
    st.session_state.page = "inputs"
    st.rerun()


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


@st.dialog("Welcome to the ESG Portfolio Optimiser", width="medium", dismissible=False)
def onboarding_dialog():
    step = st.session_state.onboarding_step

    if step == "investor_type":
        st.write("**Are you an experienced investor or a first time user on the app?**")
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
                st.session_state.onboarding_step = (
                    "experienced_path" if investor_choice == "Experienced Investor" else "first_time_path"
                )
                st.rerun()

    elif step == "experienced_path":
        st.write("**Which best describes what you want to do?**")
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
        st.write("**How risk averse are you?**")
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

        st.markdown("---")
        st.write("**Please select a number that reflects your ESG preferences:**")
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

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back", use_container_width=True, key="back_first_time"):
                st.session_state.onboarding_step = "investor_type"
                st.rerun()
        with c2:
            if st.button("Continue", use_container_width=True, key="continue_first_time"):
                apply_first_time_choices(risk_choice, esg_choice, custom_gamma, custom_lambda)


# =========================================================
# Tab 1: original 2-asset teaching model
# =========================================================
def var_covar(sigmas: np.ndarray, rho: float) -> np.ndarray:
    return np.array([
        [sigmas[0] ** 2, rho * sigmas[0] * sigmas[1]],
        [rho * sigmas[0] * sigmas[1], sigmas[1] ** 2],
    ])


def build_portfolio_grid(
    mu: np.ndarray,
    sigma: np.ndarray,
    rho: float,
    rf: float,
    esg_scores: np.ndarray,
    gamma: float,
    lambda_esg: float,
    num_points: int,
) -> pd.DataFrame:
    cov = var_covar(sigma, rho)
    weights = np.linspace(0, 1, num_points)

    rows = []
    for w1 in weights:
        w = np.array([w1, 1 - w1])
        exp_return = float(np.dot(mu, w))
        variance = float(np.dot(w, np.dot(cov, w)))
        std_dev = float(np.sqrt(max(variance, 0.0)))
        esg_score = float(np.dot(esg_scores, w))
        sharpe = np.nan if std_dev <= 1e-12 else (exp_return - rf) / std_dev
        utility = exp_return - 0.5 * gamma * variance + lambda_esg * esg_score

        rows.append(
            {
                "Weight Asset 1": w1,
                "Weight Asset 2": 1 - w1,
                "Expected Return": exp_return,
                "Variance": variance,
                "Std Dev": std_dev,
                "ESG Score": esg_score,
                "Sharpe Ratio": sharpe,
                "Utility": utility,
            }
        )

    return pd.DataFrame(rows)


def required_esg_threshold(df: pd.DataFrame, lambda_esg: float) -> float:
    s_min = float(df["ESG Score"].min())
    s_max = float(df["ESG Score"].max())
    return s_min + lambda_esg * (s_max - s_min)


# FIX: recompute Sharpe inside the selector using the same rf everywhere
# so the unrestricted tangency is always compared consistently with the ESG subset.
def select_key_portfolios(df: pd.DataFrame, rf: float):
    work = df.copy()
    work["Sharpe Ratio"] = np.where(
        work["Std Dev"] > 1e-12,
        (work["Expected Return"] - rf) / work["Std Dev"],
        np.nan,
    )

    valid = work[np.isfinite(work["Sharpe Ratio"])].copy()
    idx_mvp = work["Std Dev"].idxmin()
    idx_tan = valid["Sharpe Ratio"].idxmax()
    return work.loc[idx_mvp], work.loc[idx_tan]


def summary_df(mvp: pd.Series, tangency: pd.Series, labels: tuple[str, str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Portfolio": labels[0],
                "Weight Asset 1": mvp["Weight Asset 1"],
                "Weight Asset 2": mvp["Weight Asset 2"],
                "Expected Return": mvp["Expected Return"],
                "Std Dev": mvp["Std Dev"],
                "ESG Score": mvp["ESG Score"],
                "Sharpe Ratio": mvp["Sharpe Ratio"],
                "Utility": mvp["Utility"],
            },
            {
                "Portfolio": labels[1],
                "Weight Asset 1": tangency["Weight Asset 1"],
                "Weight Asset 2": tangency["Weight Asset 2"],
                "Expected Return": tangency["Expected Return"],
                "Std Dev": tangency["Std Dev"],
                "ESG Score": tangency["ESG Score"],
                "Sharpe Ratio": tangency["Sharpe Ratio"],
                "Utility": tangency["Utility"],
            },
        ]
    )


def format_table(df: pd.DataFrame):
    return df.style.format(
        {
            "Weight Asset 1": "{:.2%}",
            "Weight Asset 2": "{:.2%}",
            "Expected Return": "{:.2%}",
            "Std Dev": "{:.2%}",
            "ESG Score": "{:.2%}",
            "Sharpe Ratio": "{:.3f}",
            "Utility": "{:.4f}",
        }
    )


# =========================================================
# Tab 2: fast workbook loader
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


# =========================================================
# Markowitz helpers for tab 2
# =========================================================
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
    D = max(A * C - B**2, 1e-12)
    return inv_cov, ones, A, B, C, D


def gmv_weights(mu: np.ndarray, cov: np.ndarray) -> np.ndarray:
    inv_cov, ones, A, _, _, _ = frontier_constants(mu, cov)
    return (inv_cov @ ones) / A


def target_return_weights(mu: np.ndarray, cov: np.ndarray, target_return: float) -> np.ndarray:
    inv_cov, ones, A, B, C, D = frontier_constants(mu, cov)
    alpha = (C - B * target_return) / D
    beta = (A * target_return - B) / D
    return inv_cov @ (alpha * ones + beta * mu)


def portfolio_stats(weights: np.ndarray, mu: np.ndarray, cov: np.ndarray, esg: np.ndarray | None = None) -> dict:
    weights = np.asarray(weights, dtype=float)
    exp_return = float(weights @ mu)
    variance = float(weights @ cov @ weights)
    std_dev = float(np.sqrt(max(variance, 0.0)))
    out = {
        "Expected Return": exp_return,
        "Variance": variance,
        "Std Dev": std_dev,
    }
    if esg is not None:
        out["ESG Score"] = float(weights @ esg)
    return out


def build_frontier(mu: np.ndarray, cov: np.ndarray, esg: np.ndarray, num_points: int = 80):
    mu = np.asarray(mu, dtype=float)
    cov = np.asarray(cov, dtype=float)
    esg = np.asarray(esg, dtype=float)

    w_gmv = gmv_weights(mu, cov)
    gmv = portfolio_stats(w_gmv, mu, cov, esg)
    gmv["Weights"] = w_gmv

    target_min = float(min(mu.min(), gmv["Expected Return"]))
    target_max = float(max(mu.max(), gmv["Expected Return"]))
    if np.isclose(target_min, target_max):
        target_max = target_min + 1e-6

    rows = []
    for target in np.linspace(target_min, target_max, num_points):
        w = target_return_weights(mu, cov, target)
        stats = portfolio_stats(w, mu, cov, esg)
        rows.append(
            {
                "Expected Return": stats["Expected Return"],
                "Std Dev": stats["Std Dev"],
                "Variance": stats["Variance"],
                "ESG Score": stats["ESG Score"],
            }
        )

    frontier = pd.DataFrame(rows).sort_values("Std Dev").reset_index(drop=True)
    frontier["Efficient"] = frontier["Expected Return"] >= gmv["Expected Return"] - 1e-12
    return frontier, gmv


def weights_table(weights: np.ndarray, firms: pd.DataFrame) -> pd.DataFrame:
    out = firms[["Ticker", "Company", "ESG Rating", "ESG Score", "Expected Return"]].copy()
    out["Weight"] = weights
    out["Abs Weight"] = out["Weight"].abs()
    return out.sort_values("Abs Weight", ascending=False).reset_index(drop=True)


def default_esg_cutoff(asset1_esg_pct: float, asset2_esg_pct: float, portfolio_esg_cutoff: float) -> float:
    return max(min(asset1_esg_pct, asset2_esg_pct) / 100.0, portfolio_esg_cutoff)


def annualise_covariance(daily_cov: pd.DataFrame, trading_days: int) -> pd.DataFrame:
    return daily_cov * float(trading_days)


# =========================================================
# Rendering helpers
# =========================================================
def render_theoretical_tab(
    df_all: pd.DataFrame,
    df_esg: pd.DataFrame,
    rf: float,
    mvp_std: pd.Series,
    tan_std: pd.Series,
    mvp_esg: pd.Series,
    tan_esg: pd.Series,
    std_summary: pd.DataFrame,
    esg_summary: pd.DataFrame,
):
    st.subheader("1) Standard mean-variance frontier and CML")
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    x_all = df_all["Std Dev"] * 100
    y_all = df_all["Expected Return"] * 100
    rf_plot = rf * 100

    ax1.plot(x_all, y_all, linewidth=2, label="Mean-variance frontier (all portfolios)")
    sigma_line_1 = np.linspace(0, max(float(x_all.max()), float(tan_std["Std Dev"] * 100)) * 1.10, 200)
    cml_1 = rf_plot + float(tan_std["Sharpe Ratio"]) * sigma_line_1
    ax1.plot(sigma_line_1, cml_1, linestyle="--", linewidth=2, label="CML")
    ax1.scatter([0], [rf_plot], color="black", s=70, label="Risk-free rate")
    ax1.scatter(
        [mvp_std["Std Dev"] * 100],
        [mvp_std["Expected Return"] * 100],
        marker="o",
        s=120,
        label="Minimum variance portfolio",
    )
    ax1.scatter(
        [tan_std["Std Dev"] * 100],
        [tan_std["Expected Return"] * 100],
        marker="*",
        s=220,
        label="Tangency portfolio",
    )
    ax1.set_xlabel("Portfolio standard deviation (%)")
    ax1.set_ylabel("Expected return (%)")
    ax1.set_title("Standard frontier: all portfolios")
    ax1.set_xlim(left=0)
    ax1.set_ylim(bottom=0)
    ax1.grid(True)
    ax1.legend()
    st.pyplot(fig1)
    st.subheader("Summary table: Standard graph")
    st.dataframe(format_table(std_summary), use_container_width=True)

    st.subheader("2) ESG-screened frontier and CML")
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    x_esg = df_esg["Std Dev"] * 100
    y_esg = df_esg["Expected Return"] * 100
    ax2.plot(x_esg, y_esg, linewidth=2.5, label="ESG frontier")
    sigma_line_2 = np.linspace(0, max(float(x_esg.max()), float(tan_esg["Std Dev"] * 100)) * 1.10, 200)
    cml_2 = rf_plot + float(tan_esg["Sharpe Ratio"]) * sigma_line_2
    ax2.plot(sigma_line_2, cml_2, linestyle="--", linewidth=2, label="ESG CML")
    ax2.scatter([0], [rf_plot], color="black", s=70, label="Risk-free rate")
    ax2.scatter(
        [mvp_esg["Std Dev"] * 100],
        [mvp_esg["Expected Return"] * 100],
        marker="o",
        s=120,
        label="ESG minimum variance portfolio",
    )
    ax2.scatter(
        [tan_esg["Std Dev"] * 100],
        [tan_esg["Expected Return"] * 100],
        marker="*",
        s=220,
        label="ESG tangency portfolio",
    )
    ax2.set_xlabel("Portfolio standard deviation (%)")
    ax2.set_ylabel("Expected return (%)")
    ax2.set_title("ESG-screened frontier")
    ax2.set_xlim(left=0)
    ax2.set_ylim(bottom=0)
    ax2.grid(True)
    ax2.legend()
    st.pyplot(fig2)
    st.subheader("Summary table: ESG graph")
    st.dataframe(format_table(esg_summary), use_container_width=True)


def render_stock_tab(esg_cutoff: float | None):
    st.subheader("3) Stock-universe frontiers and minimum-variance portfolios")
    st.markdown(
        """
        This tab uses the uploaded matched workbook only.

        The graph shows:
        - the **theoretical frontier** from all matched stocks
        - the **ESG-screened frontier** from the reduced stock set

        Because the ESG case has fewer investable stocks, its feasible set should be weakly inside the full-stock frontier.
        """
    )

    try:
        firms, daily_cov, corr = load_fast_workbook()
        annual_cov = annualise_covariance(daily_cov, st.session_state.trading_days)

        if st.session_state.beginner_mode or is_experienced_find_mode() or esg_cutoff is None:
            default_cutoff = st.session_state.lambda_esg
        else:
            default_cutoff = default_esg_cutoff(
                asset1_esg_pct=st.session_state.esg1,
                asset2_esg_pct=st.session_state.esg2,
                portfolio_esg_cutoff=esg_cutoff,
            )

        st.write(f"Matched stocks available: **{len(firms)}**")

        min_company_esg_pct = st.number_input(
            "Minimum company ESG score for the screened frontier (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(default_cutoff * 100),
            step=1.0,
            format="%.1f",
            key="stock_universe_esg_cutoff",
        )

        firms_all = firms.copy()
        mu_all = firms_all["Expected Return"].to_numpy(dtype=float)
        esg_all = firms_all["ESG Score"].to_numpy(dtype=float)
        cov_all = annual_cov.loc[firms_all["Ticker"], firms_all["Ticker"]].to_numpy(dtype=float)
        frontier_all, gmv_all = build_frontier(
            mu_all, cov_all, esg_all, num_points=st.session_state.frontier_points
        )

        cutoff = min_company_esg_pct / 100.0
        firms_screened = firms_all[firms_all["ESG Score"] >= cutoff].copy().reset_index(drop=True)
        st.write(f"Stocks meeting ESG cutoff: **{len(firms_screened)}**")

        if len(firms_screened) < 2:
            st.warning("Fewer than 2 stocks meet the ESG cutoff. Lower the minimum company ESG score.")
        else:
            mu_scr = firms_screened["Expected Return"].to_numpy(dtype=float)
            esg_scr = firms_screened["ESG Score"].to_numpy(dtype=float)
            cov_scr = annual_cov.loc[firms_screened["Ticker"], firms_screened["Ticker"]].to_numpy(dtype=float)
            frontier_scr, gmv_scr = build_frontier(
                mu_scr, cov_scr, esg_scr, num_points=st.session_state.frontier_points
            )

            st.subheader("Stock-universe frontier graph")
            fig3, ax3 = plt.subplots(figsize=(11, 6))

            all_eff = frontier_all[frontier_all["Efficient"]].copy()
            scr_eff = frontier_scr[frontier_scr["Efficient"]].copy()

            ax3.plot(
                all_eff["Std Dev"] * 100,
                all_eff["Expected Return"] * 100,
                linewidth=2.2,
                label="Theoretical frontier: all matched stocks",
            )
            ax3.plot(
                scr_eff["Std Dev"] * 100,
                scr_eff["Expected Return"] * 100,
                linewidth=2.2,
                label="ESG-screened frontier",
            )
            ax3.scatter(
                [gmv_all["Std Dev"] * 100],
                [gmv_all["Expected Return"] * 100],
                marker="o",
                s=110,
                label="MVP: all matched stocks",
            )
            ax3.scatter(
                [gmv_scr["Std Dev"] * 100],
                [gmv_scr["Expected Return"] * 100],
                marker="*",
                s=220,
                label="MVP: ESG-screened stocks",
            )
            ax3.set_xlabel("Portfolio standard deviation (%)")
            ax3.set_ylabel("Expected return (%)")
            ax3.set_title("All-stock theoretical frontier vs ESG-screened frontier")
            ax3.grid(True)
            ax3.legend()
            st.pyplot(fig3)

            st.subheader("Minimum-variance portfolio summary")
            summary = pd.DataFrame(
                [
                    {
                        "Case": "Without ESG preference",
                        "Stocks": len(firms_all),
                        "Expected Return": gmv_all["Expected Return"],
                        "Std Dev": gmv_all["Std Dev"],
                        "ESG Score": gmv_all["ESG Score"],
                    },
                    {
                        "Case": "With ESG preference",
                        "Stocks": len(firms_screened),
                        "Expected Return": gmv_scr["Expected Return"],
                        "Std Dev": gmv_scr["Std Dev"],
                        "ESG Score": gmv_scr["ESG Score"],
                    },
                ]
            )
            st.dataframe(
                summary.style.format(
                    {
                        "Expected Return": "{:.2%}",
                        "Std Dev": "{:.2%}",
                        "ESG Score": "{:.2%}",
                    }
                ),
                use_container_width=True,
            )

            st.subheader("Top weights in minimum-variance portfolio: without ESG preference")
            weights_all = weights_table(gmv_all["Weights"], firms_all)
            st.dataframe(
                weights_all.head(10).style.format(
                    {
                        "ESG Score": "{:.2%}",
                        "Expected Return": "{:.2%}",
                        "Weight": "{:.2%}",
                        "Abs Weight": "{:.2%}",
                    }
                ),
                use_container_width=True,
            )

            st.subheader("Top weights in minimum-variance portfolio: with ESG preference")
            weights_scr = weights_table(gmv_scr["Weights"], firms_screened)
            st.dataframe(
                weights_scr.head(10).style.format(
                    {
                        "ESG Score": "{:.2%}",
                        "Expected Return": "{:.2%}",
                        "Weight": "{:.2%}",
                        "Abs Weight": "{:.2%}",
                    }
                ),
                use_container_width=True,
            )

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.download_button(
                    "Download all-stock MVP weights",
                    weights_all.to_csv(index=False).encode("utf-8"),
                    "all_stock_mvp_weights.csv",
                    "text/csv",
                )
            with c2:
                st.download_button(
                    "Download ESG MVP weights",
                    weights_scr.to_csv(index=False).encode("utf-8"),
                    "esg_stock_mvp_weights.csv",
                    "text/csv",
                )
            with c3:
                st.download_button(
                    "Download all-stock frontier",
                    frontier_all.to_csv(index=False).encode("utf-8"),
                    "all_stock_frontier.csv",
                    "text/csv",
                )
            with c4:
                st.download_button(
                    "Download ESG frontier",
                    frontier_scr.to_csv(index=False).encode("utf-8"),
                    "esg_stock_frontier.csv",
                    "text/csv",
                )

    except Exception as e:
        st.error(f"Could not build the stock-universe frontier from the workbook: {e}")


# =========================================================
# Force questionnaire before app use
# =========================================================
if not st.session_state.onboarding_complete:
    onboarding_dialog()
    st.title("ESG Portfolio Optimiser")
    st.info("Please complete the questionnaire to start using the app.")
    st.stop()


# =========================================================
# Page 1: Inputs
# =========================================================
if st.session_state.page == "inputs":
    if is_experienced_find_mode():
        st.title("Asset Finder Preferences")
        st.caption(
            "Experienced Investor path: choose your risk profile and ESG preferences below. The app will only show the stock-universe frontier tab."
        )

        with st.form("stock_finder_form"):
            st.subheader("Risk profile")
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

            st.markdown("---")
            st.subheader("ESG preferences")
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

            st.markdown("---")
            st.subheader("Firm-level frontier settings")
            frontier_points = st.slider(
                "Points for stock-universe frontier",
                30,
                150,
                int(st.session_state.frontier_points),
                10,
            )
            trading_days = st.slider(
                "Trading days used to annualise daily covariance",
                200,
                260,
                int(st.session_state.trading_days),
                1,
            )

            submitted = st.form_submit_button("Continue to stock finder")

        if submitted:
            gamma_value = float(custom_gamma) if risk_choice == "Custom" else RISK_MAP[risk_choice]
            lambda_value = float(custom_lambda) if esg_choice == "Custom" else ESG_MAP[esg_choice]

            st.session_state.gamma = gamma_value
            st.session_state.lambda_esg = lambda_value
            st.session_state.risk_profile = risk_choice
            st.session_state.esg_profile = esg_choice
            st.session_state.frontier_points = frontier_points
            st.session_state.trading_days = trading_days
            go_to("results")

    else:
        st.title("Portfolio Inputs")

        if is_experienced_existing_mode():
            st.caption(
                "Experienced Investor path: enter your existing 2-asset combination below. The app will only show the theoretical tab."
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

            st.subheader("Portfolio inputs")
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
            num_points = st.slider(
                "Number of portfolio weight points",
                101,
                5001,
                int(st.session_state.num_points),
                100,
            )

            st.markdown("---")

            st.subheader("Investor preferences")
            lambda_esg = st.slider(
                "ESG preference intensity λ",
                0.0,
                1.0,
                float(st.session_state.lambda_esg),
                0.01,
            )
            gamma = st.number_input(
                "Risk aversion γ",
                0.0,
                50.0,
                float(st.session_state.gamma),
                0.10,
                format="%.2f",
            )

            st.markdown("---")

            st.subheader("Firm-level frontier settings")
            frontier_points = st.slider(
                "Points for stock-universe frontier",
                30,
                150,
                int(st.session_state.frontier_points),
                10,
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
            st.session_state.num_points = num_points
            st.session_state.lambda_esg = lambda_esg
            st.session_state.gamma = gamma
            st.session_state.frontier_points = frontier_points
            st.session_state.trading_days = trading_days
            go_to("results")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Go to results"):
            go_to("results")
    with c2:
        if st.button("Start over"):
            reset_onboarding()


# =========================================================
# Page 2: Results
# =========================================================
elif st.session_state.page == "results":
    st.title("Results")

    show_theoretical = is_experienced_existing_mode() or st.session_state.beginner_mode
    show_stock = is_experienced_find_mode() or st.session_state.beginner_mode

    if st.session_state.beginner_mode:
        st.success(
            f"First-time user mode active. Risk aversion γ = {st.session_state.gamma:.2f} and ESG intensity λ = {st.session_state.lambda_esg:.2f}."
        )
        st.caption("You are seeing both tabs: the theoretical model and the stock-universe frontier.")
    elif is_experienced_existing_mode():
        st.info(
            "Experienced Investor path: only the theoretical model tab is shown because you already have 2 assets."
        )
    elif is_experienced_find_mode():
        st.info(
            "Experienced Investor path: only the stock-universe frontier tab is shown because you asked the app to help find an asset combination."
        )

    theoretical_payload = None
    esg_cutoff = None

    if show_theoretical:
        mu = np.array([st.session_state.mu1_pct, st.session_state.mu2_pct]) / 100.0
        sigma = np.array([st.session_state.sigma1_pct, st.session_state.sigma2_pct]) / 100.0
        rf = st.session_state.rf_pct / 100.0
        rho = st.session_state.rho
        esg_scores = np.array([st.session_state.esg1, st.session_state.esg2]) / 100.0
        lambda_esg = st.session_state.lambda_esg
        gamma = st.session_state.gamma
        num_points = st.session_state.num_points

        df_all = build_portfolio_grid(
            mu=mu,
            sigma=sigma,
            rho=rho,
            rf=rf,
            esg_scores=esg_scores,
            gamma=gamma,
            lambda_esg=lambda_esg,
            num_points=num_points,
        )

        esg_cutoff = required_esg_threshold(df_all, lambda_esg)
        df_esg = df_all[df_all["ESG Score"] >= esg_cutoff - 1e-12].copy()
        if df_esg.empty:
            df_esg = df_all.loc[[df_all["ESG Score"].idxmax()]].copy()

        # FIX APPLIED HERE
        mvp_std, tan_std = select_key_portfolios(df_all, rf)
        mvp_esg, tan_esg = select_key_portfolios(df_esg, rf)

        # Safety check: the ESG-feasible set is a subset of the unrestricted set,
        # so its max Sharpe should not exceed the unrestricted max Sharpe.
        if tan_esg["Sharpe Ratio"] > tan_std["Sharpe Ratio"] + 1e-12:
            st.warning(
                "Unexpected result detected: the ESG-screened Sharpe exceeds the unrestricted Sharpe. "
                "Please rerun the app or clear cache."
            )

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("ESG Cutoff", f"{esg_cutoff * 100:.1f}/100", f"λ = {lambda_esg:.2f}")
        m_col2.metric(
            "Tangency Return",
            f"{tan_std['Expected Return'] * 100:.1f}%",
            f"Sharpe {tan_std['Sharpe Ratio']:.3f}",
        )
        m_col3.metric("MVP Std Dev", f"{mvp_std['Std Dev'] * 100:.1f}%")
        m_col4.metric("ESG Tangency Sharpe", f"{tan_esg['Sharpe Ratio']:.3f}", "Post-screen")

        std_summary = summary_df(mvp_std, tan_std, ("Minimum Variance Portfolio", "Tangency Portfolio"))
        esg_summary = summary_df(
            mvp_esg,
            tan_esg,
            ("ESG Minimum Variance Portfolio", "ESG Tangency Portfolio"),
        )

        st.markdown(
            f"""
            **ESG screen used in the 2-asset ESG graph**

            Required portfolio ESG score = **{esg_cutoff * 100:.2f} / 100**
            """
        )

        theoretical_payload = {
            "df_all": df_all,
            "df_esg": df_esg,
            "rf": rf,
            "mvp_std": mvp_std,
            "tan_std": tan_std,
            "mvp_esg": mvp_esg,
            "tan_esg": tan_esg,
            "std_summary": std_summary,
            "esg_summary": esg_summary,
        }

    if show_theoretical and show_stock:
        tab_analysis, tab_stock = st.tabs(["Theoretical model", "Stock-universe frontier"])
        with tab_analysis:
            render_theoretical_tab(**theoretical_payload)
        with tab_stock:
            render_stock_tab(esg_cutoff)
    elif show_theoretical:
        tab_analysis = st.tabs(["Theoretical model"])[0]
        with tab_analysis:
            render_theoretical_tab(**theoretical_payload)
    elif show_stock:
        tab_stock = st.tabs(["Stock-universe frontier"])[0]
        with tab_stock:
            render_stock_tab(esg_cutoff)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Edit inputs"):
            go_to("inputs")
    with col2:
        if st.button("Refresh questionnaire"):
            reset_onboarding()
    with col3:
        if st.button("Stay on results"):
            st.rerun()
