import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import scipy.optimize as optimize
import streamlit_authenticator as stauth
import bcrypt

# ============================================================
# הגדרות כלליות
# ============================================================

st.set_page_config(
    page_title='מעבדת תמחור אג"ח',
    layout="wide",
    page_icon="🎓"
)

THEME = {
    "gold": "#C9A96E",
    "cream": "#F5EDD6",
    "dark": "#0B0E14",
    "panel": "#12161F",
    "border": "rgba(201,169,110,0.35)",
    "muted": "#A8A8A8",
    "green": "#00cc96",
    "red": "#EF553B",
    "blue": "#2980B9",
    "light_line": "rgba(255,255,255,0.08)",
}

PAYMENT_FREQUENCY_OPTIONS = {
    1: "שנתי",
    2: "חצי-שנתי (מקובל)",
    4: "רבעוני",
}

AMORTIZATION_OPTIONS = {
    "bullet": 'פדיון סופי (Bullet)',
    "equal_principal": 'פדיון לשיעורין, קרן שווה',
}

STYLING = f"""
<style>
:root {{
    --gold: {THEME["gold"]};
    --cream: {THEME["cream"]};
    --dark: {THEME["dark"]};
    --panel: {THEME["panel"]};
    --border: {THEME["border"]};
    --muted: {THEME["muted"]};
}}

.stApp, .stApp > header, [data-testid="stAppViewContainer"] {{
    background-color: var(--dark) !important;
    color: var(--cream) !important;
}}

html, body, [class*="css"] {{
    direction: rtl;
}}

h1, h2, h3, p, div, label, span {{
    direction: rtl !important;
    text-align: right !important;
    color: var(--cream) !important;
}}

section[data-testid="stSidebar"] {{
    background-color: #0F131B !important;
}}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="base-input"],
div[data-baseweb="textarea"] > div {{
    background-color: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}}

div[data-baseweb="select"] *,
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {{
    color: var(--cream) !important;
    -webkit-text-fill-color: var(--cream) !important;
}}

[data-baseweb="popover"] > div,
[data-baseweb="menu"],
div[role="listbox"],
ul[role="listbox"] {{
    background-color: var(--panel) !important;
}}

li[role="option"] {{
    background-color: var(--panel) !important;
}}

li[role="option"]:hover,
li[aria-selected="true"] {{
    background-color: #1e2430 !important;
}}

li[role="option"] span {{
    color: var(--cream) !important;
}}

/* סגנון לטאבים */
button[data-baseweb="tab"] {{
    background-color: transparent !important;
    color: var(--muted) !important;
    font-size: 1.1rem !important;
    padding-bottom: 10px !important;
}}

button[data-baseweb="tab"][aria-selected="true"] {{
    color: var(--gold) !important;
    border-bottom-color: var(--gold) !important;
}}

.metric-box {{
    background: var(--panel);
    border: 1px solid var(--border);
    padding: 18px;
    border-radius: 10px;
    text-align: center !important;
    min-height: 130px;
}}

.metric-title {{
    font-size: 0.95rem;
    color: var(--muted) !important;
    letter-spacing: 0.02em;
}}

.metric-value {{
    font-size: 2rem;
    color: var(--gold) !important;
    font-weight: bold;
    margin-top: 8px;
    line-height: 1.25;
}}

.metric-sub {{
    font-size: 0.9rem;
    color: var(--muted) !important;
    margin-top: 8px;
}}

.fair-value-box {{
    background: rgba(201,169,110,0.10);
    border: 2px solid var(--gold);
    padding: 18px;
    border-radius: 10px;
    text-align: center !important;
    min-height: 130px;
}}

.note-box {{
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    padding: 14px 16px;
    border-radius: 10px;
    margin: 8px 0 16px 0;
}}

.table-container {{
    overflow-x: auto;
    width: 100%;
    direction: rtl;
    margin-bottom: 15px;
}}

.custom-table {{
    width: 100%;
    border-collapse: collapse;
    color: var(--cream);
    font-size: 0.94rem;
    direction: ltr;
}}

.custom-table th {{
    color: var(--gold);
    border-bottom: 1px solid var(--border);
    padding: 12px 14px;
    text-align: center;
    white-space: nowrap;
    background: rgba(18,22,31,0.95);
    position: sticky;
    top: 0;
}}

.custom-table td {{
    border-bottom: 1px solid rgba(255,255,255,0.05);
    padding: 10px 14px;
    text-align: center;
    white-space: nowrap;
    direction: ltr;
}}

.custom-table tr:hover {{
    background: rgba(255,255,255,0.03);
}}

.katex-html {{
    text-align: center !important;
    display: block;
    margin: 12px 0;
}}

hr {{
    border-color: rgba(255,255,255,0.08) !important;
}}

[data-testid="stMetric"] {{
    background: var(--panel);
    border: 1px solid var(--border);
    padding: 10px;
    border-radius: 8px;
}}

.discount-summary {{
    background: rgba(201,169,110,0.07);
    border: 1px solid var(--border);
    padding: 12px 18px;
    border-radius: 10px;
    margin: 10px 0 0 0;
    text-align: center !important;
    font-size: 1.05rem;
    color: var(--cream) !important;
}}

.discount-summary b {{
    color: var(--gold) !important;
}}
</style>
"""

st.markdown(STYLING, unsafe_allow_html=True)

# ============================================================
# פונקציות חישוב
# ============================================================

def validate_inputs(face_value, coupon_rate_pct, market_yield_pct, years_to_maturity, payments_per_year):
    errors = []
    periods_exact = years_to_maturity * payments_per_year
    periods = int(round(periods_exact))

    if face_value <= 0:
        errors.append("הערך הנקוב חייב להיות חיובי.")
    if years_to_maturity <= 0:
        errors.append("מספר השנים לפדיון חייב להיות חיובי.")
    if payments_per_year <= 0:
        errors.append("מספר התשלומים בשנה חייב להיות חיובי.")
    if periods <= 0:
        errors.append("מספר התקופות המחושב חייב להיות חיובי.")
    if abs(periods_exact - periods) > 1e-9:
        errors.append("השילוב בין שנים לפדיון לבין תדירות התשלום חייב ליצור מספר שלם של תקופות.")
    if coupon_rate_pct < 0:
        errors.append("שער הקופון לא יכול להיות שלילי.")
    if market_yield_pct < 0:
        errors.append("תשואת השוק לא יכולה להיות שלילית במודל הנוכחי.")

    return errors, periods


def generate_bond_cashflows(face_value: float, coupon_rate_pct: float, market_yield_pct: float, years_to_maturity: float, payments_per_year: int, amortization_mode: str):
    errors, periods = validate_inputs(
        face_value=face_value,
        coupon_rate_pct=coupon_rate_pct,
        market_yield_pct=market_yield_pct,
        years_to_maturity=years_to_maturity,
        payments_per_year=payments_per_year,
    )

    if errors:
        raise ValueError("\n".join(errors))

    coupon_rate_annual = coupon_rate_pct / 100.0
    yield_annual = market_yield_pct / 100.0

    coupon_per_period = coupon_rate_annual / payments_per_year
    discount_per_period = yield_annual / payments_per_year

    remaining_principal = face_value
    equal_principal_payment = face_value / periods if amortization_mode == "equal_principal" else 0.0

    rows = []
    total_pv = 0.0
    macaulay_numerator = 0.0
    convexity_numerator = 0.0
    total_interest = 0.0
    total_principal_paid = 0.0

    for t in range(1, periods + 1):
        time_years = t / payments_per_year
        interest_payment = remaining_principal * coupon_per_period

        if amortization_mode == "bullet":
            principal_payment = face_value if t == periods else 0.0
        elif amortization_mode == "equal_principal":
            principal_payment = min(equal_principal_payment, remaining_principal)
        else:
            raise ValueError("סוג סילוקין לא נתמך.")

        total_cashflow = interest_payment + principal_payment
        discount_factor = 1 / ((1 + discount_per_period) ** t)
        pv_cashflow = total_cashflow * discount_factor

        total_pv += pv_cashflow
        macaulay_numerator += pv_cashflow * time_years
        
        convexity_numerator += pv_cashflow * (time_years ** 2 + time_years / payments_per_year)
        
        total_interest += interest_payment
        total_principal_paid += principal_payment

        remaining_after = max(remaining_principal - principal_payment, 0.0)

        rows.append({
            "תקופה": t,
            "שנים מהיום": time_years,
            "יתרת קרן בתחילת תקופה": remaining_principal,
            "תשלום ריבית": interest_payment,
            "תשלום קרן": principal_payment,
            "תזרים נומינלי": total_cashflow,
            "מקדם היוון": discount_factor,
            "ערך נוכחי (PV)": pv_cashflow,
            "יתרת קרן לאחר תשלום": remaining_after,
        })

        remaining_principal = remaining_after

    df = pd.DataFrame(rows)

    macaulay_duration = macaulay_numerator / total_pv if total_pv > 0 else 0.0
    modified_duration = macaulay_duration / (1 + discount_per_period) if (1 + discount_per_period) != 0 else 0.0
    convexity = (convexity_numerator / total_pv) / ((1 + discount_per_period) ** 2) if total_pv > 0 else 0.0

    return {
        "cashflows": df,
        "fair_value": total_pv,
        "macaulay_duration": macaulay_duration,
        "modified_duration": modified_duration,
        "convexity": convexity,
        "total_interest": total_interest,
        "total_principal_paid": total_principal_paid,
        "periods": periods,
    }


def price_bond_for_yield(face_value: float, coupon_rate_pct: float, market_yield_pct: float, years_to_maturity: float, payments_per_year: int, amortization_mode: str) -> float:
    result = generate_bond_cashflows(
        face_value=face_value,
        coupon_rate_pct=coupon_rate_pct,
        market_yield_pct=market_yield_pct,
        years_to_maturity=years_to_maturity,
        payments_per_year=payments_per_year,
        amortization_mode=amortization_mode,
    )
    return result["fair_value"]


def calculate_ytm_from_price(face_value, coupon_rate_pct, market_price, years_to_maturity, payments_per_year, amortization_mode):
    def yield_diff(y):
        implied_price = price_bond_for_yield(face_value, coupon_rate_pct, y * 100, years_to_maturity, payments_per_year, amortization_mode)
        return implied_price - market_price

    try:
        ytm_decimal = optimize.newton(yield_diff, x0=coupon_rate_pct/100)
        return ytm_decimal * 100
    except (RuntimeError, ValueError):
        return None


def get_bond_position_vs_par(face_value, fair_value, coupon_rate_pct, market_yield_pct):
    par_diff_pct = ((fair_value / face_value) - 1) * 100 if face_value != 0 else 0.0

    if abs(par_diff_pct) < 0.25:
        label = "נסחר סביב פארי"
        color = THEME["muted"]
    elif fair_value > face_value:
        label = 'אג"ח בפרמיה מעל הפארי'
        color = THEME["green"]
    else:
        label = 'אג"ח בדיסקאונט מתחת לפארי'
        color = THEME["red"]

    if abs(coupon_rate_pct - market_yield_pct) < 0.05:
        intuition = "קופון דומה לתשואת השוק ולכן המחיר קרוב לפארי."
    elif coupon_rate_pct > market_yield_pct:
        intuition = "הקופון גבוה מתשואת השוק ולכן המחיר נוטה להיות מעל הפארי."
    else:
        intuition = "הקופון נמוך מתשואת השוק ולכן המחיר נוטה להיות מתחת לפארי."

    return label, color, par_diff_pct, intuition


def get_market_pricing_status(fair_value, market_price):
    if market_price is None:
        return "לא הוזן מחיר שוק", THEME["muted"], None

    diff_pct = ((market_price / fair_value) - 1) * 100 if fair_value != 0 else 0.0

    if abs(diff_pct) < 0.5:
        return "🟢 מתומחר קרוב לשווי התיאורטי", THEME["green"], diff_pct
    if diff_pct > 0:
        return f"🔴 יקר מהשווי התיאורטי בכ-{abs(diff_pct):.2f}%", THEME["red"], diff_pct
    return f"🟢 זול מהשווי התיאורטי בכ-{abs(diff_pct):.2f}%", THEME["green"], diff_pct


def estimate_price_change_from_duration(modified_duration, convexity, delta_yield_pct):
    delta_y = delta_yield_pct / 100.0
    return (-modified_duration * delta_y + 0.5 * convexity * (delta_y ** 2)) * 100.0


def format_df_for_display(df: pd.DataFrame) -> pd.DataFrame:
    display_df = df.copy()
    numeric_cols_2 = [
        "שנים מהיום",
        "יתרת קרן בתחילת תקופה",
        "תשלום ריבית",
        "תשלום קרן",
        "תזרים נומינלי",
        "ערך נוכחי (PV)",
        "יתרת קרן לאחר תשלום",
    ]
    for col in numeric_cols_2:
        display_df[col] = display_df[col].map(lambda x: f"{x:,.2f}")

    display_df["מקדם היוון"] = display_df["מקדם היוון"].map(lambda x: f"{x:.6f}")
    display_df["תקופה"] = display_df["תקופה"].astype(int)
    return display_df


@st.cache_data
def build_sensitivity_table(face_value: float, coupon_rate_pct: float, years_to_maturity: float, payments_per_year: int, amortization_mode: str, base_yield_pct: float) -> pd.DataFrame:
    sensitivity_yields = sorted(set([
        max(0.0, base_yield_pct - 2.0),
        max(0.0, base_yield_pct - 1.0),
        base_yield_pct,
        base_yield_pct + 1.0,
        base_yield_pct + 2.0,
    ]))

    rows = []
    for y in sensitivity_yields:
        price = price_bond_for_yield(
            face_value=face_value,
            coupon_rate_pct=coupon_rate_pct,
            market_yield_pct=y,
            years_to_maturity=years_to_maturity,
            payments_per_year=payments_per_year,
            amortization_mode=amortization_mode,
        )
        rows.append({
            "תשואת שוק (%)": y,
            "מחיר תיאורטי": price,
            "פער מפארי (%)": ((price / face_value) - 1) * 100 if face_value != 0 else 0.0,
        })

    return pd.DataFrame(rows)


@st.cache_data
def build_reverse_sensitivity_table(face_value: float, coupon_rate_pct: float, years_to_maturity: float, payments_per_year: int, amortization_mode: str, base_price: float) -> pd.DataFrame:
    sensitivity_prices = sorted(set([
        max(0.01, base_price - 2.0),
        max(0.01, base_price - 1.0),
        base_price,
        base_price + 1.0,
        base_price + 2.0,
    ]))

    rows = []
    for p in sensitivity_prices:
        ytm = calculate_ytm_from_price(
            face_value=face_value,
            coupon_rate_pct=coupon_rate_pct,
            market_price=p,
            years_to_maturity=years_to_maturity,
            payments_per_year=payments_per_year,
            amortization_mode=amortization_mode
        )
        if ytm is not None:
            rows.append({
                "מחיר שוק": p,
                "YTM נגזר (%)": ytm,
                "פער מפארי (%)": ((p / face_value) - 1) * 100 if face_value != 0 else 0.0,
            })
    return pd.DataFrame(rows)


@st.cache_data
def build_price_yield_curve(face_value: float, coupon_rate_pct: float, years_to_maturity: float, payments_per_year: int, amortization_mode: str, base_yield_pct: float) -> pd.DataFrame:
    y_min = max(0.0, base_yield_pct - 5.0)
    y_max = base_yield_pct + 5.0
    y_values = np.arange(y_min, y_max + 0.0001, 0.25)

    prices = []
    for y in y_values:
        p = price_bond_for_yield(
            face_value=face_value,
            coupon_rate_pct=coupon_rate_pct,
            market_yield_pct=float(y),
            years_to_maturity=years_to_maturity,
            payments_per_year=payments_per_year,
            amortization_mode=amortization_mode,
        )
        prices.append(p)

    return pd.DataFrame({
        "תשואת שוק (%)": y_values,
        "מחיר": prices,
    })


# ============================================================
# פונקציות גרפיות
# ============================================================

def plot_cashflow_components(df: pd.DataFrame, show_remaining_principal: bool):
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["שנים מהיום"],
        y=df["תשלום ריבית"],
        name='תשלום ריבית',
        marker_color=THEME["blue"]
    ))

    fig.add_trace(go.Bar(
        x=df["שנים מהיום"],
        y=df["תשלום קרן"],
        name='תשלום קרן',
        marker_color=THEME["gold"]
    ))

    layout_kwargs = dict(
        barmode='stack',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=THEME["cream"]),
        xaxis=dict(
            title='שנים מהיום',
            gridcolor=THEME["light_line"]
        ),
        yaxis=dict(
            title='סכום תשלום תקופתי',
            gridcolor=THEME["light_line"]
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=40, r=40, t=30, b=30),
        hovermode="x unified"
    )

    if show_remaining_principal:
        fig.add_trace(go.Scatter(
            x=df["שנים מהיום"],
            y=df["יתרת קרן לאחר תשלום"],
            name='יתרת קרן לאחר תשלום',
            mode='lines+markers',
            line=dict(color=THEME["cream"], width=2, dash='dot'),
            yaxis='y2'
        ))
        layout_kwargs["yaxis2"] = dict(
            title='יתרת קרן (ציר ימין)',
            overlaying='y',
            side='right',
            showgrid=False,
            tickfont=dict(color=THEME["cream"]),
            titlefont=dict(color=THEME["cream"]),
        )

    fig.update_layout(**layout_kwargs)
    return fig


def plot_discounted_vs_nominal(df: pd.DataFrame):
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["שנים מהיום"],
        y=df["תזרים נומינלי"],
        name='תזרים נומינלי',
        marker_color='rgba(255,255,255,0.18)',
        marker_line_color='rgba(255,255,255,0.40)',
        marker_line_width=1
    ))

    fig.add_trace(go.Bar(
        x=df["שנים מהיום"],
        y=df["ערך נוכחי (PV)"],
        name='ערך נוכחי מהוון',
        marker_color=THEME["gold"]
    ))

    fig.update_layout(
        barmode='group',
        bargap=0.18,
        bargroupgap=0.06,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=THEME["cream"]),
        xaxis=dict(title='שנים מהיום', gridcolor=THEME["light_line"]),
        yaxis=dict(title='סכום', gridcolor=THEME["light_line"]),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=40, r=40, t=30, b=30),
        hovermode="x unified"
    )

    return fig


def plot_price_yield_curve(curve_df: pd.DataFrame, current_yield: float, current_price: float, face_value: float):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=curve_df["תשואת שוק (%)"],
        y=curve_df["מחיר"],
        mode="lines",
        name='מחיר מול תשואה',
        line=dict(color=THEME["gold"], width=3)
    ))

    fig.add_trace(go.Scatter(
        x=[current_yield],
        y=[current_price],
        mode="markers",
        name='הנקודה הנוכחית',
        marker=dict(size=12, color=THEME["blue"], line=dict(color=THEME["cream"], width=2))
    ))

    fig.add_hline(
        y=face_value,
        line_dash="dot",
        line_color=THEME["muted"],
        annotation_text="פארי",
        annotation_position="top right",
        annotation_font_color=THEME["muted"],
    )

    fig.add_vline(
        x=current_yield,
        line_dash="dash",
        line_color=THEME["blue"],
        opacity=0.45,
        annotation_text=f"תשואה נוכחית: {current_yield:.1f}%",
        annotation_position="top right",
        annotation_font_color=THEME["blue"],
    )

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=THEME["cream"]),
        xaxis=dict(title='תשואת שוק (%)', gridcolor=THEME["light_line"]),
        yaxis=dict(title='מחיר תיאורטי', gridcolor=THEME["light_line"]),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=40, r=40, t=30, b=30),
        hovermode="x unified"
    )

    return fig


# ============================================================
# המעבדה עצמה (מופעלת רק לאחר התחברות מוצלחת)
# ============================================================
def run_bond_lab():
    st.markdown(
        f"<h1 style='color:{THEME['gold']}; text-align:center !important;'>🎓 מעבדה חינוכית: תמחור והיוון אג\"ח</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='text-align:center !important; color:{THEME['muted']} !important;'>כלי לימודי שממחיש כיצד אג\"ח מתנהגת, כיצד מחשבים מחיר תיאורטי, ואיך היוון תזרימים עובד בפועל</p>",
        unsafe_allow_html=True
    )

    st.divider()

    col_in1, col_in2, col_in3 = st.columns(3)

    with col_in1:
        st.subheader("⚙️ מאפייני האיגרת")
        face_value = st.number_input(
            "ערך נקוב (Face Value)",
            min_value=1.0,
            value=100.0,
            step=10.0,
            help='הסכום שהמנפיק מתחייב להחזיר לבעל האג"ח.'
        )
        coupon_rate = st.number_input(
            "שער קופון שנתי (%)",
            min_value=0.0,
            value=4.0,
            step=0.1,
            help="הריבית החוזית השנתית על הערך הנקוב."
        )
        years_to_maturity = st.number_input(
            "שנים לפדיון",
            min_value=0.25,
            value=5.0,
            step=0.25,
            help="משך הזמן שנותר עד לפדיון הסופי."
        )

    with col_in2:
        st.subheader("📅 מבנה תשלומים")
        payment_freq = st.selectbox(
            "תדירות תשלום ריבית בשנה",
            options=list(PAYMENT_FREQUENCY_OPTIONS.keys()),
            format_func=lambda x: PAYMENT_FREQUENCY_OPTIONS[x],
            index=1
        )

        amortization_mode = st.radio(
            "סוג סילוקין",
            options=list(AMORTIZATION_OPTIONS.keys()),
            format_func=lambda x: AMORTIZATION_OPTIONS[x],
            help="Bullet: הקרן מוחזרת בסוף. קרן שווה: החזר קרן אחיד לאורך חיי האיגרת."
        )

    with col_in3:
        st.subheader("📈 נתוני שוק")
        market_yield = st.number_input(
            "תשואת שוק נדרשת / שיעור היוון (%)",
            min_value=0.0,
            value=6.0,
            step=0.1,
            format="%.2f",
            help='זהו שיעור ההיוון שלפיו השוק מתמחר היום תזרימים מאג"ח דומה בסיכון ובמח"מ.'
        )

        market_price_text = st.text_input(
            'מחיר שוק נוכחי להשוואה (אופציונלי)',
            value="95",
            help="אפשר להשאיר ריק אם לא רוצים להשוות למחיר שוק בפועל."
        )

    market_price = None
    market_price_text = market_price_text.strip()
    implied_ytm = None

    if market_price_text != "":
        try:
            market_price = float(market_price_text)
            if market_price < 0:
                st.error("מחיר שוק לא יכול להיות שלילי.")
                st.stop()
            implied_ytm = calculate_ytm_from_price(face_value, coupon_rate, market_price, years_to_maturity, payment_freq, amortization_mode)
        except ValueError:
            st.error("מחיר השוק שהוזן אינו מספר תקין.")
            st.stop()

    try:
        result = generate_bond_cashflows(
            face_value=face_value,
            coupon_rate_pct=coupon_rate,
            market_yield_pct=market_yield,
            years_to_maturity=years_to_maturity,
            payments_per_year=payment_freq,
            amortization_mode=amortization_mode,
        )
    except ValueError as e:
        st.error(str(e))
        st.stop()

    df_cashflows = result["cashflows"]
    fair_value = result["fair_value"]
    macaulay_duration = result["macaulay_duration"]
    modified_duration = result["modified_duration"]
    convexity = result["convexity"]
    total_interest = result["total_interest"]
    total_nominal_cashflows = df_cashflows["תזרים נומינלי"].sum()

    market_status_text, market_status_color, market_diff_pct = get_market_pricing_status(
        fair_value=fair_value,
        market_price=market_price
    )

    par_label, par_color, par_diff_pct, par_intuition = get_bond_position_vs_par(
        face_value=face_value,
        fair_value=fair_value,
        coupon_rate_pct=coupon_rate,
        market_yield_pct=market_yield
    )

    approx_price_change_up_1 = estimate_price_change_from_duration(modified_duration, convexity, 1.0)
    approx_price_change_down_1 = estimate_price_change_from_duration(modified_duration, convexity, -1.0)

    st.divider()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class='fair-value-box'>
                <div class='metric-title'>השווי התיאורטי המחושב</div>
                <div class='metric-value'>{fair_value:,.2f}</div>
                <div class='metric-sub'>מחיר לפי היוון תזרימים</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        ytm_display = f"YTM גלום: {implied_ytm:.2f}%" if implied_ytm is not None else "לא חושב YTM"
        st.markdown(
            f"""
            <div class='metric-box'>
                <div class='metric-title'>תמחור מול מחיר שוק</div>
                <div class='metric-value' style='color:{market_status_color} !important; font-size:1.45rem;'>{market_status_text}</div>
                <div class='metric-sub'>{ytm_display}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            f"""
            <div class='metric-box'>
                <div class='metric-title'>מח"מ מקולי</div>
                <div class='metric-value'>{macaulay_duration:.2f}</div>
                <div class='metric-sub'>משך חיים ממוצע משוקלל בשנים</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:
        st.markdown(
            f"""
            <div class='metric-box'>
                <div class='metric-title'>Modified Duration</div>
                <div class='metric-value'>{modified_duration:.2f}</div>
                <div class='metric-sub'>קמירות (Convexity): {convexity:.2f}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    c5, c6, c7, c8 = st.columns(4)

    with c5:
        st.markdown(
            f"""
            <div class='metric-box'>
                <div class='metric-title'>מול פארי</div>
                <div class='metric-value' style='color:{par_color} !important; font-size:1.4rem;'>{par_label}</div>
                <div class='metric-sub'>פער מפארי: {par_diff_pct:.2f}%</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c6:
        st.markdown(
            f"""
            <div class='metric-box'>
                <div class='metric-title'>סך תזרים נומינלי</div>
                <div class='metric-value'>{total_nominal_cashflows:,.2f}</div>
                <div class='metric-sub'>קרן + ריבית ללא היוון</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c7:
        st.markdown(
            f"""
            <div class='metric-box'>
                <div class='metric-title'>סך תשלומי ריבית</div>
                <div class='metric-value'>{total_interest:,.2f}</div>
                <div class='metric-sub'>ריבית חוזית מצטברת</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c8:
        st.markdown(
            f"""
            <div class='metric-box'>
                <div class='metric-title'>קירוב רגישות למחיר</div>
                <div class='metric-value' style='font-size:1.35rem;'>+1% תשואה ≈ {approx_price_change_up_1:.2f}%</div>
                <div class='metric-sub'>-1% תשואה ≈ {approx_price_change_down_1:.2f}%</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        f"""
        <div class='note-box'>
        <b>אינטואיציה:</b> {par_intuition}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    tab1, tab2, tab3 = st.tabs([
        "📊 תמחור תיאורטי (תשואה ← מחיר)", 
        "🏢 חדר עסקאות (מחיר ← YTM)", 
        "🧮 לוח סילוקין מפורט"
    ])

    with tab1:
        st.subheader("🧠 הרעיון הכלכלי: איך תשואת השוק משפיעה על המחיר")
        st.markdown(
            """
            אג"ח היא סדרת תזרימי מזומנים עתידיים. כדי להעריך מהו המחיר ההוגן שלה היום, אנו לוקחים כל תזרים ומהוונים אותו חזרה להיום, 
            לפי תשואת השוק הנדרשת (האלטרנטיבה בסיכון דומה). 
            <br>ככל שהריבית/התשואה בשוק עולה, הערך הנוכחי (PV) של התזרימים הללו קטן, ולכן המחיר של איגרת החוב יורד (ולהפך).
            """, unsafe_allow_html=True
        )
        st.latex(r"PV = \sum_{t=1}^{n}\frac{CF_t}{(1+r)^t}")
        
        st.markdown("<br>", unsafe_allow_html=True)

        col_t1_1, col_t1_2 = st.columns(2)
        
        with col_t1_1:
            st.subheader("📉 תזרים נומינלי מול ערך נוכחי")
            fig_pv = plot_discounted_vs_nominal(df_cashflows)
            st.plotly_chart(fig_pv, use_container_width=True, config={'displayModeBar': False})
            
            if total_nominal_cashflows > 0:
                discount_pct = (1 - fair_value / total_nominal_cashflows) * 100
                st.markdown(
                    f"<div class='discount-summary'>סך ההיוון: <b>{discount_pct:.1f}%</b> מהתזרים הנומינלי נשחק עקב עיתוי הכסף בזמן</div>",
                    unsafe_allow_html=True
                )

        with col_t1_2:
            st.subheader('📈 עקומת תמחור: מחיר מול תשואת שוק')
            curve_df = build_price_yield_curve(
                face_value=face_value, coupon_rate_pct=coupon_rate,
                years_to_maturity=years_to_maturity, payments_per_year=payment_freq,
                amortization_mode=amortization_mode, base_yield_pct=market_yield
            )
            fig_curve = plot_price_yield_curve(
                curve_df=curve_df, current_yield=market_yield,
                current_price=fair_value, face_value=face_value
            )
            st.plotly_chart(fig_curve, use_container_width=True, config={'displayModeBar': False})

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🧪 טבלת רגישות: כיצד שינוי בתשואה ישפיע על המחיר התיאורטי?")
        
        sensitivity_df = build_sensitivity_table(
            face_value=face_value, coupon_rate_pct=coupon_rate,
            years_to_maturity=years_to_maturity, payments_per_year=payment_freq,
            amortization_mode=amortization_mode, base_yield_pct=market_yield
        ).copy()

        sensitivity_display = sensitivity_df.copy()
        sensitivity_display["תשואת שוק (%)"] = sensitivity_display["תשואת שוק (%)"].map(lambda x: f"{x:.2f}%")
        sensitivity_display["מחיר תיאורטי"] = sensitivity_display["מחיר תיאורטי"].map(lambda x: f"{x:,.2f}")
        sensitivity_display["פער מפארי (%)"] = sensitivity_display["פער מפארי (%)"].map(lambda x: f"{x:.2f}%")

        st.markdown(
            "<div class='table-container'>" +
            sensitivity_display.to_html(index=False, classes="custom-table", escape=False) +
            "</div>",
            unsafe_allow_html=True
        )

    with tab2:
        st.subheader("🏢 מציאות שוק ההון: המחיר קובע את התשואה (YTM)")
        st.markdown(
            """
            <div class='note-box'>
            בניגוד לספרי הלימוד (שם קודם בוחרים את שיעור ההיוון ומחשבים מחיר), <b>בחדר עסקאות קורה בדיוק ההפך</b>: 
            המחיר הוא נתון אובייקטיבי שנקבע בבורסה על ידי כוחות של היצע וביקוש. מתוך המחיר הזה, המשקיעים גוזרים את <b>התשואה לפדיון (YTM)</b> - שהיא שיעור התשואה הפנימי (IRR) שיקבל מי שיקנה את האיגרת במחיר השוק הנוכחי ויחזיק בה עד לפדיון.
            </div>
            """, unsafe_allow_html=True
        )
        
        st.subheader("🔄 טבלת רגישות הפוכה: מהו ה-YTM הנגזר ממחירי שוק שונים?")
        st.markdown(
            "הטבלה הבאה לוקחת את מחיר השוק שהזנת למעלה (או את השווי התיאורטי, אם לא הזנת), ומדגימה מה יקרה לתשואה לפדיון אם מחיר האיגרת במסך המסחר יעלה או יירד."
        )

        base_price_for_reverse = market_price if market_price is not None else fair_value
        
        reverse_sens_df = build_reverse_sensitivity_table(
            face_value=face_value, coupon_rate_pct=coupon_rate,
            years_to_maturity=years_to_maturity, payments_per_year=payment_freq,
            amortization_mode=amortization_mode, base_price=base_price_for_reverse
        ).copy()
        
        if not reverse_sens_df.empty:
            reverse_display = reverse_sens_df.copy()
            reverse_display["מחיר שוק"] = reverse_display["מחיר שוק"].map(lambda x: f"{x:,.2f}")
            reverse_display["YTM נגזר (%)"] = reverse_display["YTM נגזר (%)"].map(lambda x: f"{x:.2f}%")
            reverse_display["פער מפארי (%)"] = reverse_display["פער מפארי (%)"].map(lambda x: f"{x:.2f}%")

            st.markdown(
                "<div class='table-container'>" +
                reverse_display.to_html(index=False, classes="custom-table", escape=False) +
                "</div>",
                unsafe_allow_html=True
            )

    with tab3:
        st.subheader("⏱️ ציר זמן: מרכיבי התזרים לאורך חיי האיגרת")
        show_remaining_principal_tab3 = st.checkbox("הצג גם יתרת קרן (קו מקווקו)", value=False)
        fig_cashflows = plot_cashflow_components(df_cashflows, show_remaining_principal=show_remaining_principal_tab3)
        st.plotly_chart(fig_cashflows, use_container_width=True, config={'displayModeBar': False})

        st.subheader("🧮 טבלת סילוקין מפורטת")
        st.markdown(
            "פירוט של כל תקופת תשלום: כמה ממנה הוא החזר ריבית, כמה החזר קרן, מקדם ההיוון לאותה תקופה, והערך הנוכחי של התזרים הבדיד."
        )
        display_df = format_df_for_display(df_cashflows)
        st.markdown(
            "<div class='table-container'>" +
            display_df.to_html(index=False, classes="custom-table", escape=False) +
            "</div>",
            unsafe_allow_html=True
        )

    st.divider()

    st.subheader("📚 מסקנות לימודיות (Takeaways)")
    st.markdown(
        """
        <div class='note-box'>
        1. <b>הקשר ההפוך (מחיר ↔ תשואה):</b> עליית תשואה בשוק מובילה לירידה במחיר האג"ח. הקשר הזה אינו לינארי, אלא קמור (אפקט הקמירות/Convexity מספק רווחיות א-סימטרית לטובת המשקיע).<br><br>
        2. <b>YTM:</b> בפרקטיקה, השוק קובע את המחיר בהתאם לסיכון ופרמיות נדרשות, והמשקיעים גוזרים מהמחיר את התשואה לפדיון.<br><br>
        3. <b>אפקט הקופון:</b> קופון שגבוה מתשואת השוק ← מחיר האג"ח נוטה להיסחר בפרמיה מעל הפארי. קופון נמוך מהתשואה ← מחיר דיסקאונט.<br><br>
        4. <b>סיכון ריבית (מח"מ):</b> מח"מ מקולי מתאר את הזמן הממוצע המשוקלל לקבלת הכסף, והמח"מ המותאם (Modified Duration) מתרגם את זה לקירוב הרגישות של מחיר האג"ח לכל תזוזה של 1% בריבית.<br><br>
        5. <b>לוחות סילוקין:</b> באג"ח פדיון לשיעורין, הקרן מוחזרת בהדרגה לאורך חיי האיגרת, ולכן רוב התזרימים מתקבלים מוקדם יותר, מה שמקצר משמעותית את המח"מ בהשוואה לאג"ח Bullet.
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# מנגנון ההתחברות (Login) עוקף בעיות גרסה
# ============================================================
def main():
    # יצירת מנגנון גיבוב פנימי ואמין באמצעות ספריית bcrypt
    passwords_to_hash = ['123456', 'pass123']
    hashed_passwords = [bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') for p in passwords_to_hash]

    credentials = {
        "usernames": {
            "student1": {
                "email": "student1@example.com",
                "name": "תלמיד 1",
                "password": hashed_passwords[0]
            },
            "student2": {
                "email": "student2@example.com",
                "name": "תלמיד 2",
                "password": hashed_passwords[1]
            }
        }
    }

    authenticator = stauth.Authenticate(
        credentials,
        'bond_lab_cookie',
        'secret_signature_key',
        30
    )

    # מנגנון התחברות שמכסה גם את הגרסאות הישנות וגם את החדשות ביותר של הספרייה
    try:
        authenticator.login('main')
    except TypeError:
        try:
            authenticator.login('Login', 'main')
        except Exception:
            authenticator.login()

    if st.session_state.get("authentication_status"):
        # הצגת כפתור התנתקות וברכה בשורה אחת בראש המסך הראשי
        col_logout, col_greet = st.columns([1, 8])
        
        with col_logout:
            authenticator.logout('התנתק', 'main')
            
        with col_greet:
            st.markdown(
                f"<div style='padding-top: 8px; font-size: 1.1rem;'>שלום <b>{st.session_state.get('name', 'תלמיד')}</b> 👋</div>", 
                unsafe_allow_html=True
            )
            
        run_bond_lab()
        
    elif st.session_state.get("authentication_status") is False:
        st.error('שם משתמש או סיסמה שגויים. נסה שוב.')
        
    elif st.session_state.get("authentication_status") is None:
        st.info('נא להזין שם משתמש וסיסמה כדי לגשת למעבדת האג"ח.')

if __name__ == "__main__":
    main()
