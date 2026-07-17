"""
app.py — Dashboard Performa Kabupaten/Kota di Riau
Berdasarkan Persentase Target Sensus yang Diselesaikan
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from data_loader import load_from_excel, load_from_gsheet, split_provinsi

# ──────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Performa Sensus Riau",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────
# CUSTOM CSS — Light Theme
# ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
.stApp { font-family: 'Inter', sans-serif !important; }
.main .block-container { padding-top: 1.5rem; max-width: 1400px; }

/* ── KPI card ── */
.kpi-card {
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(0, 0, 0, 0.05);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    backdrop-filter: blur(10px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
}
.kpi-value {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #0ea5e9, #4f46e5);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.2;
}
.kpi-label { font-size: 0.85rem; color: #64748b; margin-top: 0.4rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
.kpi-sublabel { font-size: 0.95rem; color: #0f172a; margin-top: 0.25rem; font-weight: 600; }

/* ── Header ── */
.dashboard-header { text-align: center; padding: 1rem 0 2rem 0; }
.dashboard-header h1 { font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #0284c7, #4f46e5, #be185d); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.2rem; }
.dashboard-header p { color: #64748b; font-size: 1.05rem; font-weight: 400; }

.section-divider { height: 1px; background: linear-gradient(90deg, transparent, #e2e8f0, transparent); margin: 2rem 0; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────
# COLOR PALETTE
# ──────────────────────────────────────────────────
COLORS = [
    "#0ea5e9", "#10b981", "#f59e0b", "#f43f5e", "#8b5cf6",
    "#06b6d4", "#ec4899", "#84cc16", "#d946ef", "#f97316",
    "#14b8a6", "#6366f1",
]

def get_color_map(names):
    return {name: COLORS[i % len(COLORS)] for i, name in enumerate(names)}


# ──────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗂️ Sumber Data")
    data_source = st.radio("Pilih sumber data:", ["📊 Google Sheets (Live)", "📁 Upload File Excel"], index=0)

    df_nilai = None
    df_ranking = None

    if data_source == "📊 Google Sheets (Live)":
        default_url = "https://docs.google.com/spreadsheets/d/1NU5Ws-RDvLEYqfl_06KvKWWQdd3RrxVwLPomX5D_9VY/edit?gid=997418498#gid=997418498"
        gsheet_url = st.text_input("URL Google Sheets:", value=default_url)
        if gsheet_url:
            try:
                with st.spinner("Mengambil data dari Google Sheets..."):
                    df_nilai, df_ranking = load_from_gsheet(gsheet_url)
                st.success(f"✅ Data berhasil dimuat")
            except Exception as e:
                st.error(f"❌ Gagal memuat: {e}")
    else:
        uploaded = st.file_uploader("Upload file Excel (.xlsx):", type=["xlsx"])
        if uploaded:
            try:
                with st.spinner("Membaca file Excel..."):
                    df_nilai, df_ranking = load_from_excel(uploaded)
                st.success(f"✅ Data berhasil dimuat")
            except Exception as e:
                st.error(f"❌ Gagal memuat: {e}")

    st.markdown("---")

    if df_nilai is not None:
        df_nilai_kab, sr_nilai_prov = split_provinsi(df_nilai)
        df_ranking_kab, sr_ranking_prov = split_provinsi(df_ranking)
        all_kab = df_nilai_kab.index.tolist()
        all_dates = df_nilai_kab.columns.tolist()

        st.markdown("### 🔍 Filter")
        selected_kab = st.multiselect("Pilih Kabupaten/Kota:", options=all_kab, default=all_kab)
        show_provinsi = st.toggle("📌 Tampilkan benchmark Provinsi", value=True)
        
        st.markdown("#### 📅 Rentang Tanggal")
        if len(all_dates) > 1:
            start_idx, end_idx = st.slider(
                "Pilih rentang tanggal:",
                min_value=0, max_value=len(all_dates) - 1,
                value=(0, len(all_dates) - 1),
                format=f"Day %d",
            )
            st.caption(f"**{all_dates[start_idx]}** s/d **{all_dates[end_idx]}**")
            selected_dates = all_dates[start_idx:end_idx + 1]
        else:
            selected_dates = all_dates

        df_n = df_nilai_kab.loc[selected_kab, selected_dates] if selected_kab else df_nilai_kab[selected_dates]
        df_r = df_ranking_kab.loc[selected_kab, selected_dates] if selected_kab else df_ranking_kab[selected_dates]
        sr_prov_n = sr_nilai_prov[selected_dates] if sr_nilai_prov is not None else None
    else:
        st.stop()


# ──────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-header">
    <h1>Dashboard Performa Sensus Riau 2026</h1>
    <p>Persentase Target Sensus yang Diselesaikan per Kabupaten/Kota</p>
</div>
""", unsafe_allow_html=True)

tab_overview, tab_compare, tab_race, tab_raw = st.tabs([
    "📊 Overview & Metrik", "📈 Analisis Lanjutan", "🏆 Animasi Ranking", "📋 Data"
])

last_date = selected_dates[-1]
first_date = selected_dates[0]
color_map = get_color_map(all_kab)
max_val_global = df_nilai.max().max()

TEXT_COLOR = "#1e293b"
GRID_COLOR = "rgba(0,0,0,0.06)"

# ════════════════════════════════════════════════════
# TAB 1: OVERVIEW
# ════════════════════════════════════════════════════
with tab_overview:
    nilai_terakhir = df_n[last_date].sort_values(ascending=False)
    ranking_terakhir = df_r[last_date].sort_values(ascending=True)
    top1_name = ranking_terakhir.index[0]
    top1_val = nilai_terakhir.loc[top1_name]
    
    growth = df_n[last_date] - df_n[first_date] if len(selected_dates) >= 2 else pd.Series(0, index=df_n.index)
    prov_val = sr_prov_n[last_date] if sr_prov_n is not None else df_n[last_date].mean()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">🥇 #{int(ranking_terakhir.iloc[0])}</div>
            <div class="kpi-label">Terbaik Saat Ini</div>
            <div class="kpi-sublabel">{top1_name} ({top1_val:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value" style="background: linear-gradient(135deg, #10b981, #059669); -webkit-background-clip: text;">🚀 +{growth.max():.1f}%</div>
            <div class="kpi-label">Progres Tercepat</div>
            <div class="kpi-sublabel">{growth.idxmax()}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value" style="background: linear-gradient(135deg, #d97706, #b45309); -webkit-background-clip: text;">{prov_val:.1f}%</div>
            <div class="kpi-label">Rata-rata Provinsi</div>
            <div class="kpi-sublabel">Tgl {last_date}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value" style="background: linear-gradient(135deg, #e11d48, #be123c); -webkit-background-clip: text;">📉 +{growth.min():.1f}%</div>
            <div class="kpi-label">Progres Terlambat</div>
            <div class="kpi-sublabel">{growth.idxmin()}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    st.markdown("#### 📈 Tren Individual (Small Multiples)")
    df_melt = df_n.reset_index().melt(id_vars="index", value_vars=selected_dates, var_name="Date", value_name="Progress")
    df_melt.rename(columns={"index": "Kabupaten"}, inplace=True)
    
    fig_facet = px.area(
        df_melt, x="Date", y="Progress", facet_col="Kabupaten", facet_col_wrap=4,
        color="Kabupaten", color_discrete_map=color_map,
        height=500
    )
    
    fig_facet.update_traces(line_shape='spline', fill='tozeroy', fillcolor=None, fillpattern_shape=None)
    fig_facet.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=TEXT_COLOR),
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=False, hovermode="x unified"
    )
    
    fig_facet.update_xaxes(
        categoryorder='array', categoryarray=selected_dates,
        showgrid=False, showticklabels=False, zeroline=False
    )
    fig_facet.update_yaxes(
        showgrid=False, showticklabels=False, zeroline=False, 
        range=[0, max_val_global * 1.1]
    )
    fig_facet.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    
    st.plotly_chart(fig_facet, use_container_width=True)


# ════════════════════════════════════════════════════
# TAB 2: ANALISIS LANJUTAN
# ════════════════════════════════════════════════════
with tab_compare:
    st.markdown("#### 🔍 Fokus Perbandingan")
    
    st.markdown("##### 📈 Tren Detail Terpilih")
    fig_val = go.Figure()
    for kab in selected_kab:
        fig_val.add_trace(go.Scatter(
            x=selected_dates, y=df_n.loc[kab].values,
            mode="lines", name=kab,
            line=dict(color=color_map[kab], width=3, shape="spline"),
            hovertemplate=f"<b>{kab}</b><br>%{{x}}<br>%{{y:.1f}}%<extra></extra>",
        ))
        
    if show_provinsi and sr_prov_n is not None:
        fig_val.add_trace(go.Scatter(
            x=selected_dates, y=sr_prov_n.values,
            mode="lines", name="PROVINSI RIAU",
            line=dict(color="#94a3b8", width=2, dash="dash", shape="spline"),
        ))

    fig_val.update_layout(
        height=450, margin=dict(l=20, r=20, t=10, b=40),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        xaxis=dict(
            gridcolor=GRID_COLOR, categoryorder='array', 
            categoryarray=selected_dates, tickangle=-45
        ),
        yaxis=dict(gridcolor=GRID_COLOR),
        hovermode="x unified", font=dict(family="Inter", color=TEXT_COLOR)
    )
    st.plotly_chart(fig_val, use_container_width=True)


# ════════════════════════════════════════════════════
# TAB 3: ANIMASI
# ════════════════════════════════════════════════════
with tab_race:
    st.markdown("#### 🏆 Animasi Pergerakan Peringkat Harian")
    
    col_ctrl1, col_ctrl2 = st.columns([3, 1])
    with col_ctrl1:
        frame_idx = st.slider(
            "📅 Kontrol Waktu:",
            min_value=0, max_value=len(selected_dates) - 1,
            value=len(selected_dates) - 1,
            format=f"Day %d",
        )
    with col_ctrl2:
        st.write("") 
        auto_play = st.button("▶️ Mulai Auto-Play", use_container_width=True)

    current_date = selected_dates[frame_idx]
    
    # Layout mirip Matplotlib: Kiri Bar, Kanan Line
    col_bar, col_line = st.columns([1, 1.5])
    bar_placeholder = col_bar.empty()
    line_placeholder = col_line.empty()

    def draw_animation_frame(d_idx, container_bar, container_line):
        d = selected_dates[d_idx]
        
        # --- 1. Bar Chart (Kiri) ---
        vals_anim = df_n[d].sort_values(ascending=True)
        bar_c = [color_map.get(k, "#0ea5e9") for k in vals_anim.index]
        
        fig_bar = go.Figure(go.Bar(
            y=vals_anim.index, x=vals_anim.values, orientation="h",
            marker=dict(color=bar_c), text=[f"{v:.1f}%" for v in vals_anim.values],
            textposition="outside", textfont=dict(size=12, color=TEXT_COLOR),
            hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>"
        ))
        fig_bar.update_layout(
            height=500, margin=dict(l=10, r=40, t=50, b=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            title=dict(text=f"Tanggal {d}", font=dict(size=16, color=TEXT_COLOR)),
            xaxis=dict(range=[0, max_val_global * 1.15], showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False), bargap=0.15,
            font=dict(family="Inter", color=TEXT_COLOR)
        )
        container_bar.plotly_chart(fig_bar, use_container_width=True)

        # --- 2. Line Chart (Kanan) ---
        fig_line = go.Figure()
        x_dates = selected_dates[:d_idx+1]
        
        for kab in df_r.index:
            y_vals = df_r.loc[kab, x_dates].values
            fig_line.add_trace(go.Scatter(
                x=x_dates, y=y_vals,
                mode="lines+markers",
                name=kab,
                line=dict(color=color_map.get(kab, "#0ea5e9"), width=2),
                marker=dict(size=6),
            ))
            # Text at the end of the line
            if len(x_dates) > 0:
                fig_line.add_annotation(
                    x=x_dates[-1], y=y_vals[-1],
                    text=kab, showarrow=False,
                    xanchor="left", xshift=10,
                    font=dict(size=10, color=color_map.get(kab, "#0ea5e9"), weight="bold")
                )

        n_kabupaten = len(df_r.index)
        fig_line.update_layout(
            height=500, margin=dict(l=10, r=100, t=50, b=40), 
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            title=dict(text="Riwayat Ranking", font=dict(size=16, color=TEXT_COLOR)),
            xaxis=dict(
                gridcolor=GRID_COLOR,
                categoryorder='array', categoryarray=selected_dates,
                range=[-0.5, len(selected_dates) + 2.5] # space for text labels
            ),
            yaxis=dict(
                title="Ranking",
                gridcolor=GRID_COLOR,
                autorange="reversed",
                dtick=1,
                range=[n_kabupaten + 0.5, 0.5]
            ),
            showlegend=False,
            font=dict(family="Inter", color=TEXT_COLOR)
        )
        # Vertical dotted line for current frame
        fig_line.add_vline(x=d, line_width=1.5, line_dash="dot", line_color="gray")
        
        container_line.plotly_chart(fig_line, use_container_width=True)

    # Autoplay logic
    if auto_play:
        for i in range(len(selected_dates)):
            draw_animation_frame(i, bar_placeholder, line_placeholder)
            time.sleep(0.4)
    else:
        # Draw current frame based on slider
        draw_animation_frame(frame_idx, bar_placeholder, line_placeholder)


# ════════════════════════════════════════════════════
# TAB 4: DATA
# ════════════════════════════════════════════════════
with tab_raw:
    st.markdown("#### 📋 Export Data Mentah")
    
    df_display = df_n.copy()
    if show_provinsi and sr_prov_n is not None:
        df_display.loc["PROVINSI RIAU"] = sr_prov_n
    
    st.dataframe(df_display.round(2), use_container_width=True)
    st.download_button("📥 Download CSV", data=df_display.to_csv(), file_name="data_sensus.csv")

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.85rem;'>Dashboard Analitik Sensus Riau 2026 | Sinkronisasi Google Sheets</p>", unsafe_allow_html=True)
