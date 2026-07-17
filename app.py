"""
app.py — Dashboard Performa Kabupaten/Kota di Riau
Berdasarkan Persentase Target Sensus yang Diselesaikan
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
# CUSTOM CSS — Glassmorphism & Spacing
# ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
.stApp { font-family: 'Inter', sans-serif !important; }
.main .block-container { padding-top: 1.5rem; max-width: 1400px; }

/* ── KPI card ── */
.kpi-card {
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    backdrop-filter: blur(10px);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.kpi-card:hover {
    transform: translateY(-2px);
    border-color: rgba(14, 165, 233, 0.4);
}
.kpi-value {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.2;
}
.kpi-label { font-size: 0.85rem; color: #94a3b8; margin-top: 0.4rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
.kpi-sublabel { font-size: 0.95rem; color: #f8fafc; margin-top: 0.25rem; font-weight: 600; }

/* ── Header ── */
.dashboard-header { text-align: center; padding: 1rem 0 2rem 0; }
.dashboard-header h1 { font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #0ea5e9, #8b5cf6, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.2rem; }
.dashboard-header p { color: #94a3b8; font-size: 1.05rem; font-weight: 400; }

.section-divider { height: 1px; background: linear-gradient(90deg, transparent, #0ea5e9, transparent); margin: 2rem 0; opacity: 0.2; }
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

# ════════════════════════════════════════════════════
# TAB 1: OVERVIEW
# ════════════════════════════════════════════════════
with tab_overview:
    # --- KPI Cards ---
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
            <div class="kpi-value" style="background: linear-gradient(135deg, #34d399, #10b981); -webkit-background-clip: text;">🚀 +{growth.max():.1f}%</div>
            <div class="kpi-label">Pertumbuhan Tercepat</div>
            <div class="kpi-sublabel">{growth.idxmax()}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value" style="background: linear-gradient(135deg, #fbbf24, #f59e0b); -webkit-background-clip: text;">{prov_val:.1f}%</div>
            <div class="kpi-label">Rata-rata Provinsi</div>
            <div class="kpi-sublabel">Tgl {last_date}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value" style="background: linear-gradient(135deg, #fb7185, #f43f5e); -webkit-background-clip: text;">📉 +{growth.min():.1f}%</div>
            <div class="kpi-label">Pertumbuhan Terlambat</div>
            <div class="kpi-sublabel">{growth.idxmin()}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # --- Modern Layout: Table + Small Multiples ---
    col_left, col_right = st.columns([1, 1.8])

    with col_left:
        st.markdown(f"#### 🏅 Peringkat (Tgl {last_date})")
        # Modern Progress Column Dataframe
        df_display = pd.DataFrame({
            "Kabupaten/Kota": ranking_terakhir.index,
            "Rank": ranking_terakhir.values.astype(int),
            "Progress": [nilai_terakhir.loc[n] for n in ranking_terakhir.index],
            "Growth": [growth.loc[n] for n in ranking_terakhir.index]
        })
        
        st.dataframe(
            df_display,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", format="#%d"),
                "Progress": st.column_config.ProgressColumn(
                    "Penyelesaian", format="%.1f%%",
                    min_value=0, max_value=max_val_global * 1.1
                ),
                "Growth": st.column_config.NumberColumn("Pertumbuhan", format="+%.1f%%")
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )

    with col_right:
        st.markdown("#### 📈 Tren Individual (Small Multiples)")
        # Replacing the spaghetti chart with Small Multiples / Facets
        # Melt the dataframe for Plotly Express
        df_melt = df_n.reset_index().melt(id_vars="index", value_vars=selected_dates, var_name="Date", value_name="Progress")
        df_melt.rename(columns={"index": "Kabupaten"}, inplace=True)
        
        fig_facet = px.area(
            df_melt, x="Date", y="Progress", facet_col="Kabupaten", facet_col_wrap=4,
            color="Kabupaten", color_discrete_map=color_map,
            height=500
        )
        
        fig_facet.update_traces(line_shape='spline', fill='tozeroy', fillcolor=None, fillpattern_shape=None)
        
        fig_facet.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#f8fafc"),
            margin=dict(l=10, r=10, t=30, b=10),
            showlegend=False,
            hovermode="x unified"
        )
        
        # Lock category order to prevent zigzag and hide grids
        fig_facet.update_xaxes(
            categoryorder='array', categoryarray=selected_dates,
            showgrid=False, showticklabels=False, zeroline=False
        )
        fig_facet.update_yaxes(
            showgrid=False, showticklabels=False, zeroline=False, 
            range=[0, max_val_global * 1.1]
        )
        # Clean facet titles
        fig_facet.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        
        st.plotly_chart(fig_facet, use_container_width=True)


# ════════════════════════════════════════════════════
# TAB 2: ANALISIS LANJUTAN
# ════════════════════════════════════════════════════
with tab_compare:
    st.markdown("#### 🔍 Fokus Perbandingan")
    
    col_slope, col_line = st.columns([1, 1.5])
    
    with col_slope:
        st.markdown("##### 🏁 Start vs End (Slopegraph)")
        st.caption(f"Dari {first_date} ke {last_date}")
        
        fig_slope = go.Figure()
        for kab in selected_kab:
            v_start = df_n.loc[kab, first_date]
            v_end = df_n.loc[kab, last_date]
            fig_slope.add_trace(go.Scatter(
                x=[first_date, last_date], y=[v_start, v_end],
                mode="lines+markers+text",
                name=kab,
                text=[f"", f"{v_end:.1f}%"],
                textposition="middle right",
                line=dict(color=color_map[kab], width=3),
                marker=dict(size=8),
                hovertemplate=f"<b>{kab}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>"
            ))
            
        fig_slope.update_layout(
            height=450,
            margin=dict(l=20, r=60, t=10, b=30),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            xaxis=dict(showgrid=False, categoryorder='array', categoryarray=[first_date, last_date]),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False)
        )
        st.plotly_chart(fig_slope, use_container_width=True)

    with col_line:
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
                line=dict(color="#cbd5e1", width=2, dash="dash", shape="spline"),
            ))

        fig_val.update_layout(
            height=450, margin=dict(l=20, r=20, t=10, b=40),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            xaxis=dict(
                gridcolor="rgba(255,255,255,0.05)", categoryorder='array', 
                categoryarray=selected_dates, tickangle=-45
            ),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            hovermode="x unified",
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
    st.markdown(f"#### Data per: **{current_date}**")

    # Bar chart
    vals = df_n[current_date].sort_values(ascending=True)
    bar_colors = [color_map.get(k, "#0ea5e9") for k in vals.index]

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        y=vals.index, x=vals.values, orientation="h",
        marker=dict(color=bar_colors, line_width=0, pattern_shape=None),
        text=[f"{v:.1f}%" for v in vals.values], textposition="outside",
        textfont=dict(size=13, color="#f8fafc", family="Inter"),
        hovertemplate="<b>%{y}</b><br>%{x:.2f}%<extra></extra>",
    ))
    fig_bar.update_layout(
        height=500, margin=dict(l=10, r=60, t=10, b=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0, max_val_global * 1.15], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False),
        bargap=0.15
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="bar_race")

    # Autoplay loop
    if auto_play:
        placeholder = st.empty()
        for d in selected_dates:
            vals_anim = df_n[d].sort_values(ascending=True)
            bar_c = [color_map.get(k, "#0ea5e9") for k in vals_anim.index]
            fig_a = go.Figure(go.Bar(
                y=vals_anim.index, x=vals_anim.values, orientation="h",
                marker=dict(color=bar_c), text=[f"{v:.1f}%" for v in vals_anim.values],
                textposition="outside", textfont=dict(size=13, color="#f8fafc")
            ))
            fig_a.update_layout(
                height=500, margin=dict(l=10, r=60, t=40, b=20),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                title=dict(text=f"📅 {d}", x=0.5, font=dict(size=20, color="#f8fafc")),
                xaxis=dict(range=[0, max_val_global * 1.15], showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False), bargap=0.15
            )
            placeholder.plotly_chart(fig_a, use_container_width=True)
            time.sleep(0.4)


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
st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.85rem;'>Dashboard Analitik Sensus Riau 2026 | Sinkronisasi Google Sheets</p>", unsafe_allow_html=True)
