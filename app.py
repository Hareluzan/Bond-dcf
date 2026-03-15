import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# ============================================================
# פונקציות מתמטיות להיוון וחישוב אג"ח
# ============================================================
def generate_bond_cashflows(face_value, coupon_rate_pct, ytm_pct, years_to_maturity, payments_per_year, is_amortizing):
    periods = int(years_to_maturity * payments_per_year)
    rate_per_period = (coupon_rate_pct / 100) / payments_per_year
    discount_per_period = (ytm_pct / 100) / payments_per_year
    
    schedule = []
    remaining_principal = face_value
    
    # אם זה פדיון לשיעורין, הקרן מחולקת שווה בשווה על פני כל התקופות
    principal_payment = face_value / periods if is_amortizing else 0
    
    total_pv = 0
    macaulay_numerator = 0
    
    for t in range(1, periods + 1):
        interest_payment = remaining_principal * rate_per_period
        
        if not is_amortizing and t == periods:
            prin_pay = face_value # פדיון סופי (Bullet)
        elif is_amortizing:
            prin_pay = principal_payment
        else:
            prin_pay = 0
            
        total_cf = interest_payment + prin_pay
        discount_factor = 1 / ((1 + discount_per_period) ** t)
        pv_cf = total_cf * discount_factor
        
        total_pv += pv_cf
        macaulay_numerator += pv_cf * (t / payments_per_year)
        
        # חישוב היתרה לאחר התשלום כדי שהקו בגרף ירד לאפס בסוף
        remaining_after = remaining_principal - prin_pay
        
        schedule.append({
            "תקופה (t)": t,
            "שנה מחושבת": round(t / payments_per_year, 2),
            "יתרת קרן (לאחר תשלום)": round(remaining_after, 2),
            "תשלום ריבית": round(interest_payment, 2),
            "תשלום קרן": round(prin_pay, 2),
            "תזרים נומינלי": round(total_cf, 2),
            "ערך נוכחי (PV)": round(pv_cf, 2)
        })
        
        remaining_principal = remaining_after
        
    macd = macaulay_numerator / total_pv if total_pv > 0 else 0
    
    return pd.DataFrame(schedule), total_pv, macd

# ============================================================
# עיצוב ויזואלי (CSS מותאם)
# ============================================================
STYLING = """
<style>
:root { --gold: #C9A96E; --cream: #F5EDD6; --dark: #0B0E14; --panel: #12161F; --border: rgba(201,169,110,0.35); }

/* כפיית מצב כהה וטקסטים בהירים */
.stApp, .stApp > header, [data-testid="stAppViewContainer"] { background-color: var(--dark) !important; color: var(--cream) !important; }
h1, h2, h3, p, div, label, span { direction: rtl !important; text-align: right !important; color: var(--cream) !important; }

/* עיצוב המדדים והקוביות */
.metric-box { background: var(--panel); border: 1px solid var(--border); padding: 20px; border-radius: 8px; text-align: center !important; }
.metric-title { font-size: 1rem; color: #A8A8A8 !important; text-transform: uppercase; letter-spacing: 0.05em; }
.metric-value { font-size: 2.2rem; color: var(--gold) !important; font-weight: bold; margin-top: 5px; }
.fair-value-box { background: rgba(201,169,110,0.1); border: 2px solid var(--gold); padding: 20px; border-radius: 8px; text-align: center !important; }

/* תיקון שדות הקלט */
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="base-input"] { background-color: var(--panel) !important; border: 1px solid var(--border) !important; border-radius: 4px !important; }
div[data-baseweb="select"] *, div[data-baseweb="input"] input { color: var(--cream) !important; -webkit-text-fill-color: var(--cream) !important; }
[data-baseweb="popover"] > div, [data-baseweb="menu"], div[role="listbox"], ul[role="listbox"] { background-color: var(--panel) !important; }
li[role="option"] { background-color: var(--panel) !important; }
li[role="option"]:hover, li[aria-selected="true"] { background-color: #1e2430 !important; }
li[role="option"] span { color: var(--cream) !important; }

/* הגנה על אייקוני נגישות */
.st-visually-hidden, .visually-hidden { display: none !important; }

/* טבלת HTML */
.table-container { overflow-x: auto; width: 100%; direction: rtl; margin-bottom: 15px; }
.custom-table { width: 100%; border-collapse: collapse; color: var(--cream); }
.custom-table th { color: var(--gold); border-bottom: 1px solid var(--border); padding: 12px 15px; text-align: right; white-space: nowrap; background: rgba(18,22,31,0.9); }
.custom-table td { border-bottom: 1px solid rgba(255,255,255,0.05); padding: 10px 15px; text-align: right; white-space: nowrap; }
.custom-table tr:hover { background: rgba(255,255,255,0.03); }

/* מירכוז נוסחאות מתמטיות של Streamlit */
.katex-html { text-align: center !important; display: block; margin: 15px 0;}
</style>
"""

# ============================================================
# אפליקציה
# ============================================================
def main():
    st.set_page_config(page_title="מעבדת תמחור אג\"ח", layout="wide", page_icon="🎓")
    st.markdown(STYLING, unsafe_allow_html=True)
    
    st.markdown("<h1 style='color:#C9A96E; text-align:center !important;'>🎓 מעבדה חינוכית: תמחור והיוון אג\"ח (DCF)</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center !important; color:#A8A8A8 !important;'>למד כיצד השוק מתמחר איגרות חוב באמצעות היוון תזרימי מזומנים עתידיים</p>", unsafe_allow_html=True)
    
    st.divider()
    
    # --- אזור הזנת פרמטרים ---
    col_in1, col_in2, col_in3 = st.columns(3)
    
    with col_in1:
        st.subheader("⚙️ מאפייני האיגרת")
        face_value = st.number_input("ערך נקוב (Face Value)", min_value=10.0, value=100.0, step=10.0, help="הסכום שהחברה לוותה ושצריך להחזיר.")
        coupon_rate = st.number_input("שער קופון שנתי (%)", min_value=0.0, value=4.0, step=0.5, help="הריבית החוזית שהחברה משלמת כל שנה מתוך הערך הנקוב.")
        years_to_maturity = st.number_input("שנים לפדיון (Time to Maturity)", min_value=0.5, value=5.0, step=0.5)
        
    with col_in2:
        st.subheader("📅 מבנה תשלומים")
        payment_freq = st.selectbox("תדירות תשלום ריבית בשנה", options=[1, 2, 4], format_func=lambda x: {1: "שנתי", 2: "חצי-שנתי (מקובל)", 4: "רבעוני"}[x], index=0)
        amortization_type = st.radio("סוג סילוקין (החזר קרן)", options=["פדיון סופי (Bullet)", "פדיון לשיעורין (Amortizing)"], help="בולט: הקרן חוזרת כולה בסוף. לשיעורין: הקרן מחולקת ומוחזרת לאורך חיי האג\"ח.")
        is_amortizing = amortization_type == "פדיון לשיעורין (Amortizing)"
        
    with col_in3:
        st.subheader("📈 נתוני שוק חיה")
        ytm = st.number_input("תשואה לפדיון נדרשת (Discount Rate %)", min_value=0.1, value=6.0, step=0.5, help="שיעור ההיוון. הריבית שהמשקיעים דורשים היום בשוק עבור סיכון דומה.")
        market_price = st.number_input("מחיר שוק נוכחי (אופציונלי להשוואה)", min_value=0.0, value=95.0, step=1.0)
        
    # --- חישוב ---
    df_cashflows, fair_value, macd = generate_bond_cashflows(face_value, coupon_rate, ytm, years_to_maturity, payment_freq, is_amortizing)
    
    st.divider()
    
    # --- הצגת תוצאות סופיות ---
    st.subheader("📊 תוצאות התמחור התיאורטי (Fair Value)")
    
    st.markdown("""
    <div dir='rtl' style='margin-bottom: 10px;'>
    <b>הנוסחה הבסיסית להיוון:</b> אנו לוקחים כל תזרים מזומנים עתידי מתוך לוח הסילוקין, ומחלקים אותו במקדם ההיוון המבוסס על הריבית שהשוק דורש (התשואה לפדיון).
    </div>
    """, unsafe_allow_html=True)
    
    st.latex(r"PV = \sum_{t=1}^{n} \frac{CF_t}{(1 + r)^t}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    r1, r2, r3, r4 = st.columns(4)
    
    with r1:
        st.markdown(f"<div class='fair-value-box'><div class='metric-title'>השווי ההוגן המחושב (PV)</div><div class='metric-value' style='font-size:2.8rem;'>{fair_value:.2f}</div></div>", unsafe_allow_html=True)
    
    with r2:
        if market_price == 0:
            status_text = "לא הוזן מחיר שוק"
            status_color = "#A8A8A8"
        else:
            diff_pct = ((market_price / fair_value) - 1) * 100
            if abs(diff_pct) < 0.5:
                status_text = "🟢 מתומחר הוגן (Fairly Valued)"
                status_color = "#00cc96"
            elif diff_pct > 0:
                status_text = f"🔴 יקר מהשווי התיאורטי ב-{abs(diff_pct):.1f}%"
                status_color = "#EF553B"
            else:
                status_text = f"🟢 זול מהשווי התיאורטי ב-{abs(diff_pct):.1f}%"
                status_color = "#00cc96"
            
        st.markdown(f"<div class='metric-box'><div class='metric-title'>מצב תמחור בשוק</div><div class='metric-value' style='color:{status_color} !important; font-size:1.6rem; margin-top:15px;'>{status_text}</div></div>", unsafe_allow_html=True)

    with r3:
        st.markdown(f"<div class='metric-box'><div class='metric-title'>מח\"מ (Macaulay Duration)</div><div class='metric-value'>{macd:.2f} <span style='font-size:1rem; color:#A8A8A8 !important;'>שנים</span></div></div>", unsafe_allow_html=True)
        
    with r4:
        total_nominal_return = df_cashflows['תזרים נומינלי'].sum()
        st.markdown(f"<div class='metric-box'><div class='metric-title'>סך תזרים נומינלי (ללא היוון)</div><div class='metric-value'>{total_nominal_return:.2f}</div></div>", unsafe_allow_html=True)

    st.divider()

    # --- גרף 1: ציר זמן מרכיבי התזרים (קרן מול ריבית) ---
    st.subheader("⏱️ ציר זמן: מרכיבי התזרים ויתרת הקרן")
    st.markdown("גרף זה ממחיש ממה מורכב כל תשלום (קרן וריבית) לאורך חיי האיגרת, וכיצד יתרת החוב הולכת ופוחתת עד לסילוק המלא.")
    
    fig_time = go.Figure()
    
    # עמודות תשלום ריבית
    fig_time.add_trace(go.Bar(
        x=df_cashflows['שנה מחושבת'],
        y=df_cashflows['תשלום ריבית'],
        name='תשלום ריבית (קופון)',
        marker_color='#2980B9' # כחול יוקרתי לריבית
    ))
    
    # עמודות החזר קרן
    fig_time.add_trace(go.Bar(
        x=df_cashflows['שנה מחושבת'],
        y=df_cashflows['תשלום קרן'],
        name='החזר קרן',
        marker_color='#C9A96E' # זהב לקרן
    ))
    
    # קו יתרת קרן 
    fig_time.add_trace(go.Scatter(
        x=df_cashflows['שנה מחושבת'],
        y=df_cashflows['יתרת קרן (לאחר תשלום)'],
        name='יתרת קרן בלתי מסולקת',
        mode='lines+markers',
        line=dict(color='#F5EDD6', width=2, dash='dot'), # צבע קרם לקו היתרה
        yaxis='y2'
    ))
    
    fig_time.update_layout(
        barmode='stack', # עמודות מוערמות
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#F5EDD6'),
        xaxis=dict(title='שנים מהיום', gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title='סכום התשלום התקופתי', gridcolor='rgba(255,255,255,0.05)'),
        yaxis2=dict(title='יתרת הקרן', overlaying='y', side='right', showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
        margin=dict(l=50, r=50, t=30, b=30),
    )
    st.plotly_chart(fig_time, use_container_width=True)

    st.divider()
    
    # --- גרף 2: נומינלי מול מהוון ---
    st.subheader("📉 מפל ההיוון: נומינלי מול PV")
    st.markdown("שים לב כיצד ככל שהזמן עובר, ה**ערך הנוכחי (PV)** של כל שקל נשחק משמעותית בגלל מרכיב הזמן והריבית. תלמידים: שנו את 'תשואה לפדיון' וראו כיצד השחיקה משתנה.")
    
    fig_pv = go.Figure()
    
    fig_pv.add_trace(go.Bar(
        x=df_cashflows['שנה מחושבת'], 
        y=df_cashflows['תזרים נומינלי'],
        name='תזרים כספי חוזי (נומינלי)',
        marker_color='rgba(255, 255, 255, 0.1)',
        marker_line_color='rgba(255, 255, 255, 0.3)',
        marker_line_width=1
    ))
    
    fig_pv.add_trace(go.Bar(
        x=df_cashflows['שנה מחושבת'], 
        y=df_cashflows['ערך נוכחי (PV)'],
        name='ערך נוכחי מהוון (PV)',
        marker_color='#C9A96E'
    ))
    
    fig_pv.update_layout(
        barmode='overlay',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#F5EDD6'),
        xaxis=dict(title='שנים מהיום', gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title='סכום', gridcolor='rgba(255,255,255,0.05)'),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
        margin=dict(l=50, r=50, t=30, b=30),
    )
    st.plotly_chart(fig_pv, use_container_width=True)
    
    st.divider()
    
    # --- לוח סילוקין ---
    st.subheader("🧮 לוח סילוקין מפורט")
    st.markdown("כאן ניתן לראות בדיוק את החישוב עבור כל תקופה. הכפל את ה'תזרים הנומינלי' ב'מקדם היוון' כדי לקבל את הערך הנוכחי להיום.")
    
    # שימוש בטבלת HTML מותאמת אישית לגלילה חלקה למניעת קטיעת טקסטים
    st.markdown("<div class='table-container'>" + df_cashflows.to_html(index=False, classes="custom-table", float_format="%.2f") + "</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
