import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="运动信用卡", page_icon="💳", layout="wide")

st.title("💳 运动信用卡·负荷风控师")
st.caption("把训练负荷当作刷卡消费，把恢复能力当作还款能力")

with st.sidebar:
    st.header("今日运动数据")
    load = st.slider("近7天训练负荷", 0, 1000, 500)
    sleep = st.slider("昨晚睡眠(小时)", 0.0, 12.0, 7.0, 0.5)
    hrv = st.slider("HRV(ms)", 10, 120, 60)
    fatigue = st.slider("主观疲劳(1-10)", 1, 10, 5)
    injury = st.checkbox("有近期伤病史")
    st.divider()
    st.caption("拖动滑块，信用分与建议实时变化")

def calc_score(load, sleep, hrv, fatigue, injury):
    s = 100
    s -= max(0, (load - 500) / 10)
    s -= max(0, (7 - sleep) * 8)
    s -= max(0, (60 - hrv) / 2)
    s -= max(0, (fatigue - 5) * 5)
    s -= 15 if injury else 0
    return int(max(0, min(100, s)))

score = calc_score(load, sleep, hrv, fatigue, injury)

if score >= 80:
    level, risk, color = "高额度", "低", "🟢"
elif score >= 60:
    level, risk, color = "中额度", "中", "🟡"
else:
    level, risk, color = "低额度·建议恢复", "高", "🔴"

col1, col2, col3 = st.columns(3)
col1.metric("运动信用分", f"{score} / 100")
col2.metric("今日训练额度", level)
col3.metric("风险等级", f"{color} {risk}")

st.progress(score / 100)

st.divider()

st.subheader("📈 近90天信用分趋势")

np.random.seed(7)
days = 90
dates = pd.date_range(end=pd.Timestamp.today(), periods=days)

load_h = 500 + 120 * np.sin(np.arange(days) / 7) + np.random.normal(0, 70, days)
sleep_h = 7 + np.random.normal(0, 0.7, days)
hrv_h = 60 + np.random.normal(0, 9, days)
fatigue_h = 5 + np.random.normal(0, 1.3, days)

for i in range(days):
    if i % 28 < 3:
        load_h[i] += 220
        sleep_h[i] -= 1.6
        hrv_h[i] -= 16
        fatigue_h[i] += 2

scores_h = [calc_score(load_h[i], sleep_h[i], hrv_h[i], fatigue_h[i], False) for i in range(days)]

fig2, ax2 = plt.subplots(figsize=(10, 3))
ax2.plot(dates, scores_h, color="#1971C2", linewidth=2, label="Score")
ax2.axhline(80, color="#2F9E44", linestyle="--", alpha=0.6, label="High 80")
ax2.axhline(60, color="#E03131", linestyle="--", alpha=0.6, label="Warning 60")
ax2.fill_between(dates, 60, scores_h, where=(np.array(scores_h) < 60), color="#FFA8A8", alpha=0.6)
ax2.set_ylim(0, 105)
ax2.set_ylabel("Score")
ax2.legend(loc="lower left", fontsize=8)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
st.pyplot(fig2)

c1, c2, c3 = st.columns(3)
c1.metric("90天平均信用分", f"{np.mean(scores_h):.0f}")
c2.metric("高风险天数", int(np.sum(np.array(scores_h) < 60)))
c3.metric("透支次数", int(np.sum(np.diff((np.array(scores_h) < 60).astype(int)) == 1)))

st.divider()

left, right = st.columns([1.2, 1])

with left:
    st.subheader("📊 今日风险来源归因")
    labels, values = [], []
    d_load = max(0, (load - 500) / 10)
    d_sleep = max(0, (7 - sleep) * 8)
    d_hrv = max(0, (60 - hrv) / 2)
    d_fatigue = max(0, (fatigue - 5) * 5)
    if d_load > 0: labels.append("High Load"); values.append(round(d_load, 1))
    if d_sleep > 0: labels.append("Low Sleep"); values.append(round(d_sleep, 1))
    if d_hrv > 0: labels.append("Low HRV"); values.append(round(d_hrv, 1))
    if d_fatigue > 0: labels.append("High Fatigue"); values.append(round(d_fatigue, 1))
    if injury: labels.append("Injury History"); values.append(15)

    if values:
        fig, ax = plt.subplots(figsize=(6, 3))
        bars = ax.barh(labels, values, color="#E8590C")
        ax.set_xlabel("Deduction")
        ax.invert_yaxis()
        for bar, v in zip(bars, values):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    f"-{v}", va='center', fontsize=9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        st.pyplot(fig)
    else:
        st.success("各项指标正常，无扣分项。")

with right:
    st.subheader("💊 恢复还款计划")
    if score >= 80:
        st.success("**今日可正常训练**\n\n- 保持当前节奏\n- 训练后拉伸 10 分钟\n- 睡眠不少于 7.5 小时")
    elif score >= 60:
        st.warning("**建议降额训练**\n\n- 强度降低 20%\n- 增加 10 分钟拉伸\n- 今晚睡眠 ≥ 7.5 小时\n- 补水 2L 以上")
    else:
        st.error("**今日强制恢复**\n\n- 暂停高强度训练\n- 低强度活动 20 分钟\n- 拉伸 + 泡沫轴放松\n- 睡眠 ≥ 8 小时\n- 明日重新评估")

    st.info("💡 **信用机制**：连续 3 天信用分 ≥ 85，可解锁更高训练额度；连续 2 天 < 60，系统自动降额并推送恢复任务。")

st.divider()
with st.expander("📖 运动信用卡怎么用？"):
    st.markdown("""
    - **刷卡消费 = 训练负荷**：每次训练都在“刷”你的运动额度
    - **还款能力 = 睡眠 + HRV + 恢复 + 营养**
    - **征信记录 = 伤病史 + 训练年限**
    - **信用额度 = 今日可承受训练量**
    - **透支预警 = 伤病风险预警**
    - **还款计划 = 恢复方案**
    """)
