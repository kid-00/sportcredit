import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="教练看板", page_icon="👥", layout="wide")

st.title("👥 教练端·团队风险看板")
st.caption("50名队员的信用分监控、风险分布与30天透支热力图")

np.random.seed(42)
n_players, n_days = 50, 30
players = [f"P{i+1:02d}" for i in range(n_players)]
dates = pd.date_range(end=pd.Timestamp.today(), periods=n_days)

base_load = np.random.randint(350, 750, n_players)
load_mat = np.zeros((n_players, n_days))
sleep_mat = np.zeros((n_players, n_days))
hrv_mat = np.zeros((n_players, n_days))
fatigue_mat = np.zeros((n_players, n_days))

for i in range(n_players):
    for d in range(n_days):
        load_mat[i, d] = base_load[i] + 100 * np.sin(d / 5 + i) + np.random.normal(0, 60)
        sleep_mat[i, d] = 7 + np.random.normal(0, 0.7)
        hrv_mat[i, d] = 60 + np.random.normal(0, 9)
        fatigue_mat[i, d] = 5 + np.random.normal(0, 1.3)
    if i % 10 == 0:
        load_mat[i, -5:] += 250
        sleep_mat[i, -5:] -= 1.8
        hrv_mat[i, -5:] -= 18
        fatigue_mat[i, -5:] += 2

def calc_score(load, sleep, hrv, fatigue, injury=False):
    s = 100
    s -= max(0, (load - 500) / 10)
    s -= max(0, (7 - sleep) * 8)
    s -= max(0, (60 - hrv) / 2)
    s -= max(0, (fatigue - 5) * 5)
    s -= 15 if injury else 0
    return int(max(0, min(100, s)))

score_mat = np.zeros((n_players, n_days))
for i in range(n_players):
    for d in range(n_days):
        score_mat[i, d] = calc_score(load_mat[i, d], sleep_mat[i, d], hrv_mat[i, d], fatigue_mat[i, d])

df = pd.DataFrame({
    "Player": players,
    "Score": score_mat[:, -1].astype(int),
    "Load": load_mat[:, -1].astype(int),
    "Sleep": np.round(sleep_mat[:, -1], 1),
    "HRV": hrv_mat[:, -1].astype(int),
    "Fatigue": fatigue_mat[:, -1].astype(int),
})
df["Risk"] = df["Score"].apply(lambda x: "Low" if x >= 80 else "Mid" if x >= 60 else "High")

c1, c2, c3, c4 = st.columns(4)
c1.metric("团队平均信用分", f"{df['Score'].mean():.0f}")
c2.metric("高风险人数", int((df["Risk"] == "High").sum()))
c3.metric("中风险人数", int((df["Risk"] == "Mid").sum()))
c4.metric("今日透支率", f"{(df['Score'] < 60).mean() * 100:.0f}%")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("🥧 风险等级分布")
    counts = df["Risk"].value_counts().reindex(["Low", "Mid", "High"]).fillna(0)
    fig1, ax1 = plt.subplots(figsize=(4, 4))
    colors = ["#2F9E44", "#F08C00", "#E03131"]
    ax1.pie(counts, labels=counts.index,
            autopct=lambda p: f"{int(round(p * counts.sum() / 100))}\n{p:.0f}%",
            colors=colors, startangle=90,
            wedgeprops={"edgecolor": "white", "linewidth": 2})
    ax1.set_title("Risk Level")
    st.pyplot(fig1)

with right:
    st.subheader("📊 信用分分布")
    fig2, ax2 = plt.subplots(figsize=(5, 4))
    ax2.hist(df["Score"], bins=10, color="#1971C2", edgecolor="white")
    ax2.axvline(60, color="#E03131", linestyle="--", label="Warning 60")
    ax2.axvline(80, color="#2F9E44", linestyle="--", label="High 80")
    ax2.set_xlabel("Score")
    ax2.set_ylabel("Count")
    ax2.legend(fontsize=8)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    st.pyplot(fig2)

st.divider()

st.subheader("🔥 30天信用分热力图")
st.caption("横轴日期，纵轴队员，颜色越红风险越高，越绿额度越高")

fig3, ax3 = plt.subplots(figsize=(12, 11))
im = ax3.imshow(score_mat, aspect="auto", cmap="RdYlGn", vmin=30, vmax=100)
ax3.set_xticks(range(0, n_days, 5))
ax3.set_xticklabels([dates[i].strftime("%m-%d") for i in range(0, n_days, 5)], fontsize=8)
ax3.set_yticks(range(n_players))
ax3.set_yticklabels(players, fontsize=7)
ax3.set_xlabel("Date")
ax3.set_ylabel("Player")
cbar = plt.colorbar(im, ax=ax3, fraction=0.02, pad=0.01)
cbar.set_label("Score")
st.pyplot(fig3)

st.divider()

st.subheader("🚨 高风险队员（优先干预）")
high = df[df["Risk"] == "High"].sort_values("Score")
if len(high) > 0:
    st.dataframe(high.reset_index(drop=True), use_container_width=True)
else:
    st.success("当前无高风险队员")

st.divider()

st.subheader("📋 全员信用分")
st.dataframe(df.sort_values("Score").reset_index(drop=True), use_container_width=True)
