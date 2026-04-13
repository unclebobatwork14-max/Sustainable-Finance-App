import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
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
    "mix_points": 1001,
    "sample_points": 4000,
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
    if v.ndim != 1:
        raise ValueError("Input must be a 1D array")

    u = np.sort(v)[::-1]
    cssv = np.cumsum(u)
    rho = np.nonzero(u * np.arange(1, len(u) + 1) > (cssv - 1))[0][-1]
    theta = (cssv[rho] - 1) / (rho + 1)
    w = np.maximum(v - theta, 0)
    return w


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


def build_two_asset_objective_curve(
    mu: np.ndarray,
    sigma: np.ndarray,
    rho: float,
    rf: float,
    esg_scores: np.ndarray,
    gamma: float,
    lambda_esg: float,
    mix_points: int,
) -> pd.DataFrame:
    cov = var_covar(sigma, rho)
    rows = []

    for p1 in np.linspace(0.0, 1.0, mix_points):
        p = np.array([p1, 1.0 - p1], dtype=float)
        alpha = optimal_scale_for_direction(p, mu, cov, gamma)
        x = alpha * p
        metrics = portfolio_metrics(x, mu, cov, rf, esg_scores, gamma, lambda_esg)
        rows.append(
            {
                "Mix Asset 1": p1,
                "Mix Asset 2": 1.0 - p1,
                "x1": float(x[0]),
                "x2": float(x[1]),
                **metrics,
            }
        )

    return pd.DataFrame(rows)


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
    corner_x[greener_idx] = optimal_scale_for_direction(
        np.eye(2)[greener_idx],
        mu,
        cov,
        gamma,
    )
    corner_obj = objective_value(corner_x, mu, cov, gamma, lambda_esg, esg_scores)
    interior_x = np.array([
        float(opt_with_lambda["Weight Asset 1"]),
        float(opt_with_lambda["Weight Asset 2"]),
    ])
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
    cloud = rng.dirichlet(np.ones(n_assets), size=n_samples)
    return cloud


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
def format_optimal_summary(df: pd.DataFrame):
    format_map = {
        col: "{:.3f}" for col in df.columns if col.startswith("Weight ")
    }
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
    return df.style.format(
        {
            "Risky Weight": "{:.3f}",
            "Direction Share (within risky assets)": "{:.2%}",
            "ESG Score": "{:.2%}",
            "Expected Return": "{:.2%}",
        }
    )


# =========================================================
# Rendering helpers
# =========================================================
def render_theoretical_tab(mu, sigma, rho, rf, esg_scores, gamma, lambda_esg, mix_points):
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

    curve_benchmark = build_two_asset_objective_curve(mu, sigma, rho, rf, esg_scores, gamma, 0.0, mix_points)
    curve_esg = build_two_asset_objective_curve(mu, sigma, rho, rf, esg_scores, gamma, lambda_esg, mix_points)
    audit = audit_two_asset_solution(mu, sigma, rho, rf, esg_scores, gamma, lambda_esg)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Risk aversion γ", f"{gamma:.2f}")
    m2.metric("ESG taste λ", f"{lambda_esg:.2f}")
    m3.metric("Benchmark risky sum", f"{benchmark_opt['Risky Weight Sum']:.3f}")
    m4.metric("ESG-optimal risky sum", f"{esg_opt['Risky Weight Sum']:.3f}")

    st.subheader("Objective-optimal portfolio: λ = 0 benchmark")
    st.dataframe(format_optimal_summary(pd.DataFrame([benchmark_opt])), use_container_width=True)

    st.subheader("Objective-optimal portfolio: chosen ESG taste")
    st.dataframe(format_optimal_summary(pd.DataFrame([esg_opt])), use_container_width=True)

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

    st.subheader("Two-asset objective portfolios")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        curve_benchmark["Std Dev"] * 100,
        curve_benchmark["Expected Return"] * 100,
        color=THEORETICAL_BLUE,
        linewidth=2.4,
        label="Benchmark opportunity curve (λ = 0)",
    )
    ax.plot(
        curve_esg["Std Dev"] * 100,
        curve_esg["Expected Return"] * 100,
        color=ESG_GREEN,
        linewidth=2.4,
        label="Opportunity curve (chosen λ)",
        alpha=0.85,
    )
    ax.scatter(
        [benchmark_opt["Std Dev"] * 100],
        [benchmark_opt["Expected Return"] * 100],
        color=THEORETICAL_BLUE,
        s=60,
        zorder=5,
    )
    ax.scatter(
        [esg_opt["Std Dev"] * 100],
        [esg_opt["Expected Return"] * 100],
        color=ESG_GREEN,
        s=60,
        zorder=5,
    )
    ax.annotate(
        "benchmark optimum\n(λ = 0)",
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

    st.subheader("Risky-asset weights: λ = 0 benchmark")
    st.dataframe(format_weight_table(benchmark_weights), use_container_width=True)

    st.subheader("Risky-asset weights: chosen ESG taste")
    st.dataframe(format_weight_table(esg_weights), use_container_width=True)



def render_stock_tab(lambda_esg: float, gamma: float, rf: float):
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
        cloud_benchmark = build_stock_objective_cloud(p_cloud, mu, cov, rf, esg_scores, gamma, 0.0)
        cloud_esg = build_stock_objective_cloud(p_cloud, mu, cov, rf, esg_scores, gamma, lambda_esg)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Stocks in universe", f"{len(firms)}")
        m2.metric("Risk aversion γ", f"{gamma:.2f}")
        m3.metric("Benchmark risky sum", f"{benchmark_opt['Risky Weight Sum']:.3f}")
        m4.metric("ESG-optimal risky sum", f"{esg_opt['Risky Weight Sum']:.3f}")

        st.subheader("Objective-optimal stock portfolio: λ = 0 benchmark")
        st.dataframe(format_optimal_summary(pd.DataFrame([benchmark_opt])), use_container_width=True)

        st.subheader("Objective-optimal stock portfolio: chosen ESG taste")
        st.dataframe(format_optimal_summary(pd.DataFrame([esg_opt])), use_container_width=True)

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
            "benchmark optimum\n(λ = 0)",
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
        st.dataframe(format_weight_table(benchmark_weights.head(15)), use_container_width=True)

        st.subheader("Top stock weights: chosen ESG taste")
        st.dataframe(format_weight_table(esg_weights.head(15)), use_container_width=True)

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
# Force questionnaire before app use
# =========================================================
if not st.session_state.onboarding_complete:
    onboarding_dialog()
    st.title("ESG Portfolio Optimiser")
    st.info("Please complete the questionnaire to start using the app.")
    st.stop()


# =========================================================
# Inputs page
# =========================================================
if st.session_state.page == "inputs":
    if is_experienced_find_mode():
        st.title("Asset Finder Preferences")
        st.caption(
            "Experienced Investor path: choose your risk profile and ESG preferences below. The app will only show the stock-universe optimisation tab."
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

            submitted = st.form_submit_button("Continue to stock optimisation")

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
                "Experienced Investor path: enter your existing 2-asset combination below. The app will only show the theoretical optimisation tab."
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
            lambda_esg = st.slider(
                "ESG preference intensity λ",
                0.0,
                1.0,
                float(st.session_state.lambda_esg),
                0.01,
            )
            gamma = st.number_input(
                "Risk aversion γ",
                min_value=0.1,
                max_value=50.0,
                value=float(max(st.session_state.gamma, 0.1)),
                step=0.10,
                format="%.2f",
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

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Go to results"):
            go_to("results")
    with c2:
        if st.button("Start over"):
            reset_onboarding()


# =========================================================
# Results page
# =========================================================
elif st.session_state.page == "results":
    st.title("Results")

    show_theoretical = is_experienced_existing_mode() or st.session_state.beginner_mode
    show_stock = is_experienced_find_mode() or st.session_state.beginner_mode

    if st.session_state.beginner_mode:
        st.success(
            f"First-time user mode active. Risk aversion γ = {st.session_state.gamma:.2f} and ESG intensity λ = {st.session_state.lambda_esg:.2f}."
        )
        st.caption("You are seeing both tabs: the theoretical optimisation and the stock-universe optimisation.")
    elif is_experienced_existing_mode():
        st.info(
            "Experienced Investor path: only the theoretical optimisation tab is shown because you already have 2 assets."
        )
    elif is_experienced_find_mode():
        st.info(
            "Experienced Investor path: only the stock-universe optimisation tab is shown because you asked the app to help find an asset combination."
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
        tab1, tab2 = st.tabs(["Theoretical optimisation", "Stock-universe optimisation"])
        with tab1:
            render_theoretical_tab(mu, sigma, rho, rf, esg_scores, gamma, lambda_esg, mix_points)
        with tab2:
            render_stock_tab(lambda_esg=lambda_esg, gamma=gamma, rf=rf)
    elif show_theoretical:
        tab1 = st.tabs(["Theoretical optimisation"])[0]
        with tab1:
            render_theoretical_tab(mu, sigma, rho, rf, esg_scores, gamma, lambda_esg, mix_points)
    elif show_stock:
        tab2 = st.tabs(["Stock-universe optimisation"])[0]
        with tab2:
            render_stock_tab(lambda_esg=lambda_esg, gamma=gamma, rf=rf)

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
