import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import json
import re
from datetime import datetime, timedelta
import time

# ==========================================
# 1. 配置与样式 (完全保留你的原版 CSS)
# ==========================================
st.set_page_config(
    page_title="咕咕基金",
    page_icon="📈",
    layout="centered", # 模拟手机竖屏体验
    initial_sidebar_state="collapsed"
)

# 自定义 CSS 以复刻 React App 的视觉风格
st.markdown("""
<style>
    /* 全局字体与背景 */
    .stApp {
        background-color: #f1f5f9;
        font-family: "Inter", -apple-system, sans-serif;
    }
    
    /* 隐藏 Streamlit 默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 颜色定义 */
    :root {
        --up-color: #f87171;
        --down-color: #4ade80;
        --dark-bg: #0f172a;
    }

    /* 资产卡片样式 */
    .asset-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 16px;
        padding: 24px;
        color: white;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }
    
    /* 基金列表项样式 */
    .fund-item {
        background-color: white;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #e2e8f0;
        margin-bottom: 12px;
        transition: all 0.2s;
    }
    .fund-item:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    /* 文字工具类 */
    .text-up { color: #ef4444; font-weight: bold; }
    .text-down { color: #22c55e; font-weight: bold; }
    .text-mono { font-family: 'JetBrains Mono', monospace; }
    .text-xs { font-size: 0.75rem; }
    .text-sm { font-size: 0.875rem; }
    .text-lg { font-size: 1.125rem; }
    .font-bold { font-weight: 700; }
    .text-slate-400 { color: #94a3b8; }
    .text-slate-500 { color: #64748b; }
    .text-slate-800 { color: #1e293b; }

    /* 底部导航模拟 */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        border-top: 1px solid #e2e8f0;
        padding: 10px;
        text-align: center;
        z-index: 999;
    }
    
    /* 调整按钮样式以接近原生 */
    .stButton button {
        border-radius: 8px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 真实数据获取逻辑 (New Real Data Engine)
# ==========================================

def fetch_real_fund_data(code):
    """从天天基金获取实时估值"""
    try:
        url = f"http://fundgz.1234567.com.cn/js/{code}.js"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=2)
        res.encoding = 'utf-8'
        text = res.text
        if "jsonpgz(" in text:
            content = text.split("jsonpgz(")[1].rstrip(");")
            data = json.loads(content)
            return {
                "name": data['name'],
                "nav": float(data['gsz']),
                "change": float(data['gszzl']),
                "time": data['gztime']
            }
    except:
        return None
    return None

# ==========================================
# 3. 数据初始化 (Data Initialization)
# ==========================================

if 'data_initialized' not in st.session_state:
    
    # 定义我们要追踪的真实基金列表 (替换了之前的随机名字)
    # 格式: (代码, 简称, 板块ID)
    REAL_FUNDS = [
        ("161725", "招商白酒", "cons"),
        ("005827", "易方达蓝筹", "cons"),
        ("320007", "诺安成长", "tech"),
        ("003096", "中欧医疗", "med"),
        ("000001", "华夏上证50", "fin"), # 代替余额宝位置
        ("001156", "申万新能源", "enrg"),
        ("161028", "富国中证", "enrg"),
        ("519732", "交银定期", "fin")
    ]
    
    # 模拟板块 (保持你的逻辑)
    SECTORS = [
        {"id": "tech", "name": "半导体", "change": 1.25},
        {"id": "cons", "name": "白酒消费", "change": -0.45},
        {"id": "fin", "name": "银行金融", "change": 0.12},
        {"id": "enrg", "name": "新能源", "change": 2.30},
        {"id": "med", "name": "医药医疗", "change": -1.10},
        {"id": "prop", "name": "军工制造", "change": 0.85},
    ]

    funds = []
    
    # 进度条 (因为第一次加载真实数据会慢一点点)
    progress_bar = st.progress(0)
    
    for i, (code, short_name, sec_id) in enumerate(REAL_FUNDS):
        # 1. 获取真实数据
        real_data = fetch_real_fund_data(code)
        
        # 2. 如果获取失败，用模拟数据兜底，防止 App 崩溃
        if real_data:
            current_nav = real_data['nav']
            change_pct = real_data['change']
            full_name = real_data['name']
        else:
            current_nav = 1.0000
            change_pct = 0.00
            full_name = short_name + "(离线)"

        # 3. 补全 UI 需要的其他数据 (历史走势、持仓)
        # 注意：天天基金简易接口不提供分时图和持仓，这里为了保留你的 UI 效果，
        # 我们基于真实净值生成一个模拟曲线，确保 sparkline 不会空着。
        history = [current_nav * (1 + (np.sin(x/5) * 0.01) + (np.random.uniform(-0.01, 0.01))) for x in range(20)]
        
        holdings = [
            {"name": f"模拟持仓-{j}", "percent": np.random.randint(2, 9), "change": np.random.uniform(-3, 3)} 
            for j in range(1, 6)
        ]

        funds.append({
            "id": f"fund-{code}", # 使用代码作为唯一ID
            "name": full_name,
            "code": code,
            "nav": current_nav,
            "changePercent": change_pct,
            "sectorId": sec_id,
            "history": history,     # 你的 sparkline 需要这个
            "topHoldings": holdings # 你的详情页需要这个
        })
        progress_bar.progress((i + 1) / len(REAL_FUNDS))
    
    progress_bar.empty()
    
    st.session_state.funds = funds
    st.session_state.sectors = SECTORS
    
    # 用户持仓 (Portfolio) - 这里我把前两个真实基金设为持仓
    st.session_state.portfolio = [
        {**funds[0], "heldAmount": 5000, "avgCost": funds[0]['nav'] * 1.05}, # 假装亏了点
        {**funds[3], "heldAmount": 2000, "avgCost": funds[3]['nav'] * 0.90}, # 假装赚了点
    ]
    
    # 用户自选 (Watchlist)
    st.session_state.watchlist_ids = [funds[1]['id'], funds[2]['id'], funds[5]['id']]
    st.session_state.watchlist_groups = {
        funds[1]['id']: 'all',
        funds[2]['id']: 'tech',
        funds[5]['id']: 'all'
    }
    
    st.session_state.data_initialized = True

# 状态管理
if 'view' not in st.session_state:
    st.session_state.view = 'PORTFOLIO'
if 'selected_fund' not in st.session_state:
    st.session_state.selected_fund = None
if 'watchlist_active_group' not in st.session_state:
    st.session_state.watchlist_active_group = 'all'

# ==========================================
# 4. 辅助组件 (完全保留你的原版代码)
# ==========================================

def get_color_class(value):
    return "text-up" if value >= 0 else "text-down"

def draw_sparkline(data, is_positive):
    color = '#ef4444' if is_positive else '#22c55e'
    # 简单处理一下数据防止报错
    if not data: data = [1, 1]
    df = pd.DataFrame({'val': data, 'idx': range(len(data))})
    fig = px.area(df, x='idx', y='val', height=40)
    fig.update_traces(line_color=color, fillcolor=color, opacity=0.1)
    fig.update_layout(
        showlegend=False, 
        xaxis_visible=False, 
        yaxis_visible=False, 
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def render_fund_row(fund, is_holding=False):
    """渲染单个基金行"""
    col1, col2, col3 = st.columns([3, 2, 2])
    
    is_up = fund['changePercent'] >= 0
    sign = "+" if is_up else ""
    color_class = get_color_class(fund['changePercent'])
    
    with col1:
        st.markdown(f"""
        <div style="line-height:1.2;">
            <div class="text-sm font-bold text-slate-800">{fund['name']}</div>
            <div class="text-xs text-mono text-slate-400">{fund['code']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.plotly_chart(draw_sparkline(fund['history'], is_up), use_container_width=True, config={'staticPlot': True})
        
    with col3:
        st.markdown(f"""
        <div style="text-align: right; line-height:1.2;">
            <div class="text-sm font-bold text-mono text-slate-800">{fund['nav']:.4f}</div>
            <div class="text-xs font-bold text-mono {color_class}">{sign}{fund['changePercent']:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button(f"查看详情", key=f"btn_{fund['id']}_{int(time.time())}", use_container_width=True):
        st.session_state.selected_fund = fund
        st.rerun()
    st.markdown("---")

# ==========================================
# 5. 视图逻辑 (保留原版，仅增加了搜索逻辑)
# ==========================================

def view_portfolio():
    # 刷新按钮 (Refresh Data)
    if st.button("🔄 刷新实时数据", use_container_width=True):
        # 清除缓存，强制重新加载
        del st.session_state.data_initialized
        st.rerun()

    # 计算总资产 (使用真实净值)
    total_asset = sum([item['nav'] * item['heldAmount'] for item in st.session_state.portfolio])
    total_cost = sum([item['avgCost'] * item['heldAmount'] for item in st.session_state.portfolio])
    total_gain = total_asset - total_cost
    day_gain = sum([(item['nav'] - (item['nav'] / (1 + item['changePercent']/100))) * item['heldAmount'] for item in st.session_state.portfolio])

    # 资产卡片
    st.markdown(f"""
    <div class="asset-card">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 20px;">
            <div>
                <div style="font-size: 10px; text-transform: uppercase; opacity: 0.7; font-weight: bold; letter-spacing: 1px;">总资产 (CNY)</div>
                <div style="font-size: 32px; font-weight: bold; font-family: monospace;">{total_asset:,.2f}</div>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 8px;">
                <div style="font-size: 10px; opacity: 0.7;">持有基金</div>
                <div style="font-weight: bold; text-align: right;">{len(st.session_state.portfolio)}</div>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px;">
            <div>
                <div style="font-size: 10px; opacity: 0.7; margin-bottom: 4px;">今日盈亏</div>
                <div class="font-mono font-bold" style="font-size: 18px; color: {'#f87171' if day_gain >= 0 else '#4ade80'};">
                    {'+' if day_gain > 0 else ''}{day_gain:.2f}
                </div>
            </div>
            <div>
                <div style="font-size: 10px; opacity: 0.7; margin-bottom: 4px;">累计盈亏</div>
                <div class="font-mono font-bold" style="font-size: 18px; color: {'#f87171' if total_gain >= 0 else '#4ade80'};">
                    {'+' if total_gain > 0 else ''}{total_gain:.2f}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 持仓列表
    st.markdown('<div class="font-bold text-slate-800 text-sm uppercase mb-3">持仓明细</div>', unsafe_allow_html=True)
    
    if not st.session_state.portfolio:
        st.info("暂无持仓，快去添加吧")
    else:
        for item in st.session_state.portfolio:
            market_val = item['nav'] * item['heldAmount']
            gain = market_val - (item['avgCost'] * item['heldAmount'])
            
            with st.container():
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"**{item['name']}**")
                    st.markdown(f"<span class='text-xs text-slate-400'>{item['code']}</span>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<div style='text-align:right; font-weight:bold;'>{market_val:,.2f}</div>", unsafe_allow_html=True)
                    color = get_color_class(gain)
                    st.markdown(f"<div style='text-align:right;' class='text-xs {color}'>{'+' if gain>0 else ''}{gain:.2f}</div>", unsafe_allow_html=True)
                
                if st.button("详情", key=f"port_btn_{item['id']}"):
                    st.session_state.selected_fund = item
                    st.rerun()
                st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("➕ 手动添加", use_container_width=True):
            st.toast("功能开发中...", icon="🚧")
    with col_b:
        uploaded_file = st.file_uploader("📷 截图导入", label_visibility="collapsed")
        if uploaded_file:
            st.toast("正在识别图片...", icon="🤖")

def view_watchlist():
    st.markdown("### 自选基金")
    
    groups = [{'id': 'all', 'name': '全部'}, {'id': 'tech', 'name': '科技'}, {'id': 'safe', 'name': '稳健'}]
    
    cols = st.columns(len(groups))
    for idx, g in enumerate(groups):
        with cols[idx]:
            if st.button(g['name'], key=f"group_{g['id']}", use_container_width=True, 
                         type="primary" if st.session_state.watchlist_active_group == g['id'] else "secondary"):
                st.session_state.watchlist_active_group = g['id']
                st.rerun()
                
    watchlist_funds = [f for f in st.session_state.funds if f['id'] in st.session_state.watchlist_ids]
    
    if st.session_state.watchlist_active_group != 'all':
        filtered_ids = [fid for fid, gid in st.session_state.watchlist_groups.items() if gid == st.session_state.watchlist_active_group]
        watchlist_funds = [f for f in watchlist_funds if f['id'] in filtered_ids]

    if not watchlist_funds:
        st.markdown("""
        <div style="text-align: center; padding: 40px; color: #94a3b8; font-size: 12px; background: white; border-radius: 12px; border: 1px dashed #e2e8f0;">
            暂无自选基金
        </div>
        """, unsafe_allow_html=True)
    else:
        for fund in watchlist_funds:
            render_fund_row(fund)
            
    if st.button("管理分组", use_container_width=True):
        st.toast("打开分组管理器", icon="⚙️")

def view_market():
    # 真实的大盘指数获取比较麻烦，这里我们用几个具代表性的ETF的实时数据来模拟大盘风向
    # 上证50(000001), 创业板(159915) -> 对应我们抓取的 REAL_FUNDS 里的数据
    # 为了防止报错，我们查找 ID 包含特定代码的
    
    sh_index = next((f for f in st.session_state.funds if "000001" in f['code']), {'nav': 3000, 'changePercent': 0.5})
    cy_index = next((f for f in st.session_state.funds if "161028" in f['code']), {'nav': 2000, 'changePercent': -0.5})
    
    st.markdown("### 市场指数 (参考)")
    indices = [
        {"name": "上证参考", "val": sh_index['nav'], "pct": sh_index['changePercent']},
        {"name": "新能源指", "val": cy_index['nav'], "pct": cy_index['changePercent']},
        {"name": "纳斯达克", "val": 1890.55, "pct": 0.28}, # 暂无数据，保持模拟
    ]
    
    idx_cols = st.columns(3)
    for i, idx in enumerate(indices):
        is_up = idx['pct'] >= 0
        color = "#ef4444" if is_up else "#22c55e"
        with idx_cols[i]:
            st.markdown(f"""
            <div style="background: white; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
                <div class="text-xs text-slate-500 font-bold">{idx['name']}</div>
                <div class="text-lg font-bold font-mono" style="color:{color}">{idx['val']}</div>
                <div class="text-xs font-mono font-bold" style="color:{color}">{'+' if is_up else ''}{idx['pct']}%</div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("### 板块风向")
    sec_cols = st.columns(3)
    for i, sec in enumerate(st.session_state.sectors):
        col_idx = i % 3
        with sec_cols[col_idx]:
            intensity = min(abs(sec['change']), 2.0) / 2.0
            base_r, base_g, base_b = (239, 68, 68) if sec['change'] > 0 else (34, 197, 94)
            bg_color = f"rgba({base_r}, {base_g}, {base_b}, {0.1 + intensity * 0.4})"
            text_color = f"rgb({base_r}, {base_g}, {base_b})"
            
            st.markdown(f"""
            <div style="background: {bg_color}; padding: 12px; border-radius: 8px; margin-bottom: 8px; text-align: center; cursor: pointer;">
                <div class="text-sm font-bold text-slate-800">{sec['name']}</div>
                <div class="text-xs font-mono font-bold" style="color: {text_color}">{'+' if sec['change']>0 else ''}{sec['change']}%</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("### 市场风向标")
    for fund in st.session_state.funds[:5]:
        render_fund_row(fund)

def view_detail():
    fund = st.session_state.selected_fund
    
    col_back, col_title, col_star = st.columns([1, 4, 1])
    with col_back:
        if st.button("←", key="back_btn"):
            st.session_state.selected_fund = None
            st.rerun()
    with col_title:
        st.markdown(f"<div style='text-align:center; font-weight:bold; padding-top: 5px;'>{fund['name']}</div>", unsafe_allow_html=True)
    with col_star:
        is_watched = fund['id'] in st.session_state.watchlist_ids
        if st.button("★" if is_watched else "☆", key="star_btn"):
            if is_watched:
                st.session_state.watchlist_ids.remove(fund['id'])
                st.toast("已取消关注")
            else:
                st.session_state.watchlist_ids.append(fund['id'])
                st.toast("已加入自选")
            st.rerun()

    is_up = fund['changePercent'] >= 0
    color_class = get_color_class(fund['changePercent'])
    sign = "+" if is_up else ""
    
    st.markdown(f"""
    <div style="background: white; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 16px; border: 1px solid #e2e8f0;">
        <div class="text-xs font-mono text-slate-400">{fund['code']}</div>
        <div class="font-mono font-bold {color_class}" style="font-size: 3rem; letter-spacing: -2px;">{fund['nav']:.4f}</div>
        <div class="font-mono font-bold text-sm {color_class}">{sign}{fund['changePercent']:.2f}%</div>
        <div class="text-xs text-slate-400 mt-2">更新于: {datetime.now().strftime('%H:%M:%S')} (实时)</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["分时走势", "近30日"])
    
    with tab1:
        df_intra = pd.DataFrame({'value': fund['history'], 'time': range(len(fund['history']))})
        fig = px.area(df_intra, x='time', y='value')
        color = '#ef4444' if is_up else '#22c55e'
        fig.update_traces(line_color=color, fillcolor=color, opacity=0.1)
        fig.update_layout(
            height=200, 
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
            plot_bgcolor='white'
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        dates = pd.date_range(end=datetime.now(), periods=30)
        vals = [fund['nav'] * (1 + np.random.uniform(-0.05, 0.05)) for _ in range(30)]
        df_30 = pd.DataFrame({'date': dates, 'value': vals})
        fig2 = px.line(df_30, x='date', y='value')
        fig2.update_traces(line_color='#0f172a')
        fig2.update_layout(height=200, margin=dict(l=0, r=0, t=10, b=20))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 重仓持股 (数据源限制，暂为模拟)")
    df_holdings = pd.DataFrame(fund['topHoldings'])
    for _, row in df_holdings.iterrows():
        c1, c2, c3 = st.columns([2, 1, 1])
        c1.write(row['name'])
        c2.write(f"{row['percent']:.2f}%")
        color = get_color_class(row['change'])
        c3.markdown(f"<span class='{color} font-bold text-mono'>{'+' if row['change']>0 else ''}{row['change']:.2f}%</span>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 4px 0; opacity: 0.5;'>", unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("📝 记录交易 / 调仓", expanded=True):
        col_type = st.columns(2)
        type_buy = col_type[0].button("买入 / 加仓", use_container_width=True, type="primary")
        type_sell = col_type[1].button("卖出 / 减仓", use_container_width=True)
        
        amount = st.number_input("金额 (CNY)", value=1000.0, step=100.0)
        
        st.markdown('<label class="text-xs font-bold text-slate-500 uppercase">交易日期 (近2周)</label>', unsafe_allow_html=True)
        date_options = [(datetime.now() - timedelta(days=i)).date() for i in range(14)]
        selected_date = st.selectbox("选择日期", date_options, format_func=lambda x: x.strftime("%m月%d日 %A"))
        
        if st.button("确认提交", type="primary", use_container_width=True):
            st.success(f"已记录: {selected_date} {'买入' if not type_sell else '卖出'} {amount}元")
            time.sleep(1)
            st.session_state.selected_fund = None
            st.rerun()

# ==========================================
# 6. 主程序入口 (保留搜索框接入)
# ==========================================

def main():
    if st.session_state.selected_fund is not None:
        view_detail()
        return

    col_logo, col_search = st.columns([1, 2])
    with col_logo:
        st.markdown("#### 🦉 咕咕基金")
    with col_search:
        # 接入真实搜索功能
        search_q = st.text_input("Search", placeholder="输入代码 (如 161725)", label_visibility="collapsed")
        if search_q and len(search_q) >= 6:
            # 搜索逻辑
            with st.spinner("🔍 查找中..."):
                res = fetch_real_fund_data(search_q)
                if res:
                    # 构造成符合 UI 的数据对象
                    found_fund = {
                        "id": f"fund-{search_q}",
                        "name": res['name'],
                        "code": search_q,
                        "nav": res['nav'],
                        "changePercent": res['change'],
                        "sectorId": "all",
                        "history": [res['nav']] * 20, # 模拟历史
                        "topHoldings": []
                    }
                    st.session_state.selected_fund = found_fund
                    st.rerun()
                else:
                    st.error("未找到基金")

    if st.session_state.view == 'PORTFOLIO':
        view_portfolio()
    elif st.session_state.view == 'WATCHLIST':
        view_watchlist()
    elif st.session_state.view == 'MARKET':
        view_market()

    st.markdown("---") # Spacer
    st.markdown("<br><br>", unsafe_allow_html=True) 
    
    nav_cols = st.columns(3)
    buttons = [
        ('PORTFOLIO', '💼 资产'), 
        ('WATCHLIST', '⭐ 自选'), 
        ('MARKET', '📊 行情')
    ]
    
    for idx, (view_name, label) in enumerate(buttons):
        with nav_cols[idx]:
            is_active = st.session_state.view == view_name
            if st.button(label, key=f"nav_{view_name}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.view = view_name
                st.rerun()

if __name__ == "__main__":
    main()
