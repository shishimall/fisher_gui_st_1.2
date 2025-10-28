# fisher_gui_st

# ===============================================================
# 📊 Fisher's Exact Test App (Dual Mode: File / Manual Input)
# Version: 1.205 (Japanese Font + Persistent Inputs + Comments Restored)
# Author: Yuuji Miyahara
# ===============================================================

import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import fisher_exact
import matplotlib.pyplot as plt
import io
import xlsxwriter
from matplotlib import font_manager as fm

# ===============================================================
# 🈶 日本語フォント設定（確実に反映される方式）
# ===============================================================
def set_japanese_font():
    """日本語フォントを自動検出して適用"""
    candidates = [
        "C:/Windows/Fonts/ipaexg.ttf",        # IPAex Gothic (Windows)
        "C:/Windows/Fonts/msgothic.ttc",      # MS Gothic
        "C:/Windows/Fonts/meiryo.ttc",        # Meiryo
        "/usr/share/fonts/truetype/ipafont-gothic/ipagp.ttf",  # Linux
        "/usr/share/fonts/opentype/ipaexg/ipaexg.ttf",         # Streamlit Cloud
        "/System/Library/Fonts/ヒラギノ角ゴシック W5.ttc",   # macOS
    ]
    for path in candidates:
        if fm.os.path.exists(path):
            prop = fm.FontProperties(fname=path)
            plt.rcParams["font.family"] = prop.get_name()
            plt.rcParams["font.sans-serif"] = [prop.get_name()]
            plt.rcParams["axes.unicode_minus"] = False
            return prop
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.unicode_minus"] = False
    return None

jp_font = set_japanese_font()

# ---------------------------------
# Page Settings
# ---------------------------------
st.set_page_config(page_title="Fisher's Exact Test Tool", layout="centered")
st.title("📊 Fisherの正確検定アプリ（完全日本語対応＋コメント復活版）")

st.markdown("""
このツールでは、2群の **不良率（0=良品, 1=不良）** を比較し、  
Fisherの正確検定により **統計的な有意差** を評価します。  

---
### 🧭 モード選択の考え方
| モード | 目的 | 特徴 |
|:--|:--|:--|
| 📁 **ファイルから** | データ構造の理解・教育 | 実際の0/1データを使ってFisher検定の仕組みを体感 |
| 🔢 **集計値を手入力** | 実務での迅速な比較 | Nと不良数のみで即結果を確認 |
---
""")

# ---------------------------------
# Mode Selection
# ---------------------------------
mode = st.radio("入力方法を選択してください：", ("📁 ファイルから", "🔢 集計値を手入力"), horizontal=True)
alpha = st.slider("有意水準（α）", 0.001, 0.10, 0.05, step=0.001)
purpose = st.radio(
    "今回の試作の目的を選択してください：",
    ("差がなくなることを期待（同等を目指す）", "差が出ることを期待（改良・強化を目指す）"),
    horizontal=True
)

# ===============================================================
# 📁 FILE INPUT MODE
# ===============================================================
if mode == "📁 ファイルから":
    uploaded_file = st.file_uploader("CSVまたはExcelファイルをアップロード", type=["csv", "xlsx"])

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.subheader("✏️ データプレビュー")
        st.dataframe(df.head())

        colnames = df.columns.tolist()
        col1 = st.selectbox("群1のカラム名", colnames)
        col2 = st.selectbox("群2のカラム名", colnames, index=1 if len(colnames) > 1 else 0)

        # --- グラフ設定永続化 ---
        if "graph_title" not in st.session_state:
            st.session_state.graph_title = "Comparison of Two Groups"
        if "y_label" not in st.session_state:
            st.session_state.y_label = "Defect Rate (%)"

        st.markdown("### 📈 グラフ設定")
        st.text_input("グラフタイトルを入力", key="graph_title")
        st.text_input("Y軸ラベルを入力", key="y_label")

        if st.button("⚖️ 検定を実行（ファイル入力）"):
            data1 = df[col1].dropna().astype(int)
            data2 = df[col2].dropna().astype(int)

            fail1, ok1 = data1.sum(), len(data1) - data1.sum()
            fail2, ok2 = data2.sum(), len(data2) - data2.sum()

            table = [[fail1, ok1], [fail2, ok2]]
            oddsratio, p_val = fisher_exact(table)
            rate1, rate2 = fail1 / len(data1) * 100, fail2 / len(data2) * 100

            # ----- コメント生成 -----
            if p_val < alpha:
                main_result = f"群2（{col2}）の不良率 {rate2:.2f}% は、群1（{col1}）と比較して有意に異なります。"
                significance = f"p値 = {p_val:.4f} ＜ α = {alpha:.3f} → **統計的に有意な差あり**。"
            else:
                main_result = f"群2（{col2}）の不良率 {rate2:.2f}% は、群1（{col1}）と比較して統計的に有意な差は認められません。"
                significance = f"p値 = {p_val:.4f} ≥ α = {alpha:.3f} → **統計的に有意な差なし**。"

            if purpose == "差がなくなることを期待（同等を目指す）":
                note = (
                    "有意差が見られなかったため、**同等化達成の可能性**が示唆されます。"
                    if p_val >= alpha
                    else "有意差が確認されたため、**対策効果が不十分**の可能性があります。"
                )
            else:
                note = (
                    "有意差が確認されたため、**改良効果が確認された結果**です。"
                    if p_val < alpha
                    else "有意差が見られなかったため、**改良効果は確認されませんでした。**"
                )

            result_text = f"{main_result}\n{significance}\n\n📘 {note}"

            # ----- 結果表示 -----
            st.markdown("### ✅ 検定結果")
            st.write(f"{col1}: 不良 {fail1} / n={len(data1)} → {rate1:.2f}%")
            st.write(f"{col2}: 不良 {fail2} / n={len(data2)} → {rate2:.2f}%")
            st.write(f"オッズ比: {oddsratio:.3f}")
            st.write(f"p値: {p_val:.5f}")

            # コメント（報告書転記可）
            st.markdown("### 💬 コメント（報告書転記可）")
            st.text_area("", value=result_text, height=180, label_visibility="collapsed")

            # ----- グラフ描画 -----
            st.markdown("### 📈 Defect Rate Comparison (English Graph)")
            fig, ax = plt.subplots(figsize=(5, 3))
            ax.bar([col1, col2], [rate1, rate2], color=["skyblue", "orange"])
            ax.set_ylabel(st.session_state.y_label, fontproperties=jp_font)
            ax.set_title(st.session_state.graph_title, fontproperties=jp_font)
            ax.set_ylim(0, max(rate1, rate2) * 1.4 if max(rate1, rate2) > 0 else 1)
            for i, v in enumerate([rate1, rate2]):
                ax.text(i, v + 0.3, f"{v:.2f}%", ha='center', fontsize=10, fontproperties=jp_font)
            st.pyplot(fig)

            # ----- Excel出力 -----
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df_out = pd.DataFrame({
                    "Group": [col1, col2],
                    "Defects": [fail1, fail2],
                    "Good": [ok1, ok2],
                    "Defect Rate(%)": [rate1, rate2],
                    "Sample Size": [len(data1), len(data2)]
                })
                df_out.to_excel(writer, sheet_name="Fisher_Result", index=False)
            st.download_button(
                "📥 Download as Excel",
                output.getvalue(),
                "fisher_result.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("ファイルをアップロードすると検定を実行できます。")

# ===============================================================
# 🔢 MANUAL INPUT MODE
# ===============================================================
else:
    st.subheader("🔢 集計値から直接入力")
    st.markdown("ファイルを使わず、**サンプル数(N)** と **不良数** を直接入力して比較します。")

    colA, colB = st.columns(2)
    with colA:
        name1 = st.text_input("群1の名前（例：旧仕様）", "Group1")
        n1 = st.number_input("群1の総サンプル数", min_value=1, value=100)
        f1 = st.number_input("群1の不良数", min_value=0, value=5)
    with colB:
        name2 = st.text_input("群2の名前（例：新仕様）", "Group2")
        n2 = st.number_input("群2の総サンプル数", min_value=1, value=100)
        f2 = st.number_input("群2の不良数", min_value=0, value=3)

    if "graph_title" not in st.session_state:
        st.session_state.graph_title = "Comparison of Two Groups"
    if "y_label" not in st.session_state:
        st.session_state.y_label = "Defect Rate (%)"

    st.markdown("### 📈 グラフ設定")
    st.text_input("グラフタイトルを入力", key="graph_title")
    st.text_input("Y軸ラベルを入力", key="y_label")

    if st.button("⚖️ 検定を実行（集計値入力）"):
        ok1, ok2 = n1 - f1, n2 - f2
        table = [[f1, ok1], [f2, ok2]]
        oddsratio, p_val = fisher_exact(table)
        rate1, rate2 = f1 / n1 * 100, f2 / n2 * 100

        # ----- コメント生成 -----
        if p_val < alpha:
            main_result = f"群2（{name2}）の不良率 {rate2:.2f}% は、群1（{name1}）と比較して有意に異なります。"
            significance = f"p値 = {p_val:.4f} ＜ α = {alpha:.3f} → **統計的に有意な差あり**。"
        else:
            main_result = f"群2（{name2}）の不良率 {rate2:.2f}% は、群1（{name1}）と比較して統計的に有意な差は認められません。"
            significance = f"p値 = {p_val:.4f} ≥ α = {alpha:.3f} → **統計的に有意な差なし**。"

        if purpose == "差がなくなることを期待（同等を目指す）":
            note = (
                "有意差が見られなかったため、**同等化達成の可能性**が示唆されます。"
                if p_val >= alpha
                else "有意差が確認されたため、**対策効果が不十分**の可能性があります。"
            )
        else:
            note = (
                "有意差が確認されたため、**改良効果が確認された結果**です。"
                if p_val < alpha
                else "有意差が見られなかったため、**改良効果は確認されませんでした。**"
            )

        result_text = f"{main_result}\n{significance}\n\n📘 {note}"

        # 結果表示
        st.markdown("### ✅ 検定結果")
        st.write(f"{name1}: 不良 {f1} / n={n1} → {rate1:.2f}%")
        st.write(f"{name2}: 不良 {f2} / n={n2} → {rate2:.2f}%")
        st.write(f"オッズ比: {oddsratio:.3f}")
        st.write(f"p値: {p_val:.5f}")

        st.markdown("### 💬 コメント（報告書転記可）")
        st.text_area("", value=result_text, height=180, label_visibility="collapsed")

        st.markdown("### 📈 Defect Rate Comparison (English Graph)")
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.bar([name1, name2], [rate1, rate2], color=["skyblue", "orange"])
        ax.set_ylabel(st.session_state.y_label, fontproperties=jp_font)
        ax.set_title(st.session_state.graph_title, fontproperties=jp_font)
        ax.set_ylim(0, max(rate1, rate2) * 1.4 if max(rate1, rate2) > 0 else 1)
        for i, v in enumerate([rate1, rate2]):
            ax.text(i, v + 0.3, f"{v:.2f}%", ha='center', fontsize=10, fontproperties=jp_font)
        st.pyplot(fig)

        st.success("検定完了。結果を報告書にご活用ください。")
