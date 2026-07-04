import streamlit as st
import pandas as pd
import random
import os
import csv
from datetime import datetime
from itertools import combinations

# ---------- 配置 ----------
DATA_FILE = r"D:\chill_data\IEEE-Transactions-LaTeX2e-templates-and-instructions\sucai\all_votes.csv"   # 累积存储所有用户的数据
ADMIN_PASSWORD = "admin123"

st.set_page_config(page_title="三视频对比投票", layout="wide")
st.title("🎥 三视频对比 · 选择最好的一个")

# ---------- 自定义CSS：调大投票按钮 ----------
st.markdown("""
    <style>
    /* 增大 radio 选项的字体和间距 */
    div[role="radiogroup"] label {
        font-size: 24px !important;
        padding: 10px 20px !important;
    }
    /* 调整选项之间的间隔 */
    div[role="radiogroup"] {
        gap: 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- 初始化 session_state ----------
def init_state():
    if "videos" not in st.session_state:
        video_folder = r"D:\chill_data\IEEE-Transactions-LaTeX2e-templates-and-instructions\sucai\depoly"
        if not os.path.exists(video_folder):
            os.makedirs(video_folder, exist_ok=True)
            st.warning(f"请将视频文件放入 `{video_folder}` 文件夹")
            st.stop()
        exts = ('.mp4', '.webm', '.avi', '.mov', '.mkv')
        video_files = [f for f in os.listdir(video_folder) if f.lower().endswith(exts)]
        if not video_files:
            st.error("未找到任何视频文件，请检查文件夹")
            st.stop()
        st.session_state.videos = video_files
        st.session_state.video_paths = {
            v: os.path.join(video_folder, v) for v in video_files
        }

    if "triplets" not in st.session_state:
        v = st.session_state.videos
        if len(v) < 3:
            st.error("至少需要 3 个视频才能进行三组对比，请添加更多视频。")
            st.stop()
        all_combos = list(combinations(v, 3))
        random.shuffle(all_combos)
        max_groups = min(15, len(all_combos))
        st.session_state.triplets = all_combos[:max_groups]

    if "submitted" not in st.session_state:
        st.session_state.submitted = False

init_state()

# ---------- 获取新用户的序号 ----------
def get_next_user_serial():
    """返回下一个可用的用户序号（从1开始）"""
    if not os.path.exists(DATA_FILE):
        return 1
    try:
        df = pd.read_csv(DATA_FILE)
        if df.empty or 'user_id' not in df.columns:
            return 1
        # 提取所有 user_id，去掉前缀 "User_" 得到数字
        existing_ids = df['user_id'].dropna().unique()
        numbers = []
        for uid in existing_ids:
            if uid.startswith("User_"):
                try:
                    num = int(uid.split("_")[1])
                    numbers.append(num)
                except:
                    pass
        if not numbers:
            return 1
        return max(numbers) + 1
    except Exception as e:
        st.warning(f"读取数据文件时出错: {e}")
        return 1

# ---------- 数据记录函数 ----------
def record_user_votes(user_id, triplets, choices):
    """将当前用户的所有选择追加到 CSV 文件中"""
    file_exists = os.path.exists(DATA_FILE)
    rows = []
    for idx, (a, b, c) in enumerate(triplets):
        choice = choices.get(f"vote_{idx}")
        if choice in ["A", "B", "C"]:
            rows.append([user_id, idx, a, b, c, choice, datetime.now().isoformat()])
    if not rows:
        return
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['user_id', 'group_idx', 'video_A', 'video_B', 'video_C', 'choice', 'timestamp'])
        writer.writerows(rows)

# ---------- 侧边栏 ----------
with st.sidebar:
    st.header("📊 实验信息")
    total_groups = len(st.session_state.triplets)
    st.metric("总对比组数", total_groups)
    
    voted = 0
    for idx in range(total_groups):
        key = f"vote_{idx}"
        val = st.session_state.get(key)
        if val in ["A", "B", "C"]:
            voted += 1
    st.metric("已投票组数", f"{voted} / {total_groups}")

    st.divider()

    # ---------- 管理员入口 ----------
    st.subheader("🔐 管理员入口")
    password = st.text_input("请输入管理员密码", type="password", key="admin_pwd")
    if password == ADMIN_PASSWORD:
        st.success("验证通过，可管理数据")
        
        if st.button("📥 导出全部投票记录 (CSV)"):
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    csv_data = f.read()
                st.download_button(
                    label="点击下载 CSV",
                    data=csv_data,
                    file_name=f"all_votes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("暂无投票数据")

        if st.button("🔄 重置当前页面选择"):
            for key in list(st.session_state.keys()):
                if key.startswith("vote_"):
                    del st.session_state[key]
            st.session_state.submitted = False
            st.rerun()

        if st.button("⚠️ 清空全部历史数据 (不可恢复)"):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
                st.success("历史数据已清空")
                st.rerun()
    elif password:
        st.error("密码错误，请重试")
    else:
        st.info("请输入管理员密码以管理数据")

# ---------- 主界面 ----------
if st.session_state.submitted:
    st.success("✅ 您的投票已成功提交！感谢参与。")
    st.info("您可以选择「重置当前页面选择」重新投票（但会丢失当前提交记录）。")
else:
    st.markdown(f"### 共 {total_groups} 组对比，每组有三个视频，请选择您认为最好的一个")

    for idx, (vid_a, vid_b, vid_c) in enumerate(st.session_state.triplets):
        path_a = st.session_state.video_paths[vid_a]
        path_b = st.session_state.video_paths[vid_b]
        path_c = st.session_state.video_paths[vid_c]

        with st.container():
            st.markdown(f"**组 {idx+1}**")
            col1, col2, col3 = st.columns(3, gap="medium")
            with col1:
                st.video(path_a, format="video/mp4", start_time=0, width=300)
                st.caption(f"视频 A: {vid_a}")
            with col2:
                st.video(path_b, format="video/mp4", start_time=0, width=300)
                st.caption(f"视频 B: {vid_b}")
            with col3:
                st.video(path_c, format="video/mp4", start_time=0, width=300)
                st.caption(f"视频 C: {vid_c}")

            options = ["A", "B", "C"]
            current_val = st.session_state.get(f"vote_{idx}", None)
            if current_val not in options:
                current_val = None
            default_idx = options.index(current_val) if current_val in options else None

            st.radio(
                label="选择最好的视频：",
                options=options,
                index=default_idx,
                key=f"vote_{idx}",
                horizontal=True,
                label_visibility="collapsed"
            )
            st.markdown("---")

    # ---------- 提交按钮 ----------
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📨 提交所有投票", use_container_width=True):
            unfinished = []
            for idx in range(total_groups):
                key = f"vote_{idx}"
                val = st.session_state.get(key)
                if val not in ["A", "B", "C"]:
                    unfinished.append(idx+1)
            if unfinished:
                st.error(f"⚠️ 还有 {len(unfinished)} 组未选择（第 {', '.join(map(str, unfinished))} 组），请完成所有选择后再提交。")
            else:
                # 生成序号用户ID
                serial = get_next_user_serial()
                user_id = f"User_{serial}"
                # 记录到 CSV
                record_user_votes(user_id, st.session_state.triplets, st.session_state)
                st.session_state.submitted = True
                # 清空选择，让下一位用户使用
                for key in list(st.session_state.keys()):
                    if key.startswith("vote_"):
                        del st.session_state[key]
                st.rerun()