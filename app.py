import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import requests # 新增：用于网络请求
import json     # 新增：用于解析数据
import re       # 新增：用于正则提取

# ==========================================
# 1. 配置与样式 (Configuration & CSS)
# ==========================================
# [严格保留你的原版代码]
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
# 2. 数据服务 (Data Services - 已接入真实接口)
# ==========================================

# [新增函数：获取真实数据]
def fetch_real_data(code):
    try:
        url = f"http://fundgz.1234567.com.cn/js/{code}.js"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=1)
        r.encoding = "utf-8"
        text = r.text
        if "jsonpgz(" in text:
            content = text.split("jsonpgz(")[1].rstrip(");")
            data = json.loads(content)
            return data
    except:
        return None
    return None

if 'data_initialized' not in st.session_state:
    
    # [修改：不再使用随机名称，而是定义一组真实的基金代码]
    # 格式：(代码, 备用名称, 板块ID)
    TARGET_FUNDS = [
        ("161725", "招商中证白酒", "cons"),
        ("005827", "易方达蓝筹", "cons"),
        ("320007", "诺安成长", "tech"),
        ("003096", "中欧医疗", "med"),
        ("000001", "华夏上证50", "fin"), 
        ("001156", "申万新能源", "enrg"),
        ("161028", "富国中证", "enrg"),
        ("519732", "交银定期", "fin"),
        ("000001", "上证指数", "fin"), # 用于模拟市场指数
    ]
    
    # 模拟板块 (保留你的原始定义)
    SECTORS = [
        {"id": "tech", "name": "半导体", "change": 1.25},
        {"id": "cons", "name": "白酒消费", "change": -0.45},
        {"id": "fin", "name": "银行金融", "change": 0.12},
        {"id": "enrg", "name": "新能源", "change": 2.30},
        {"id": "med", "name": "医药医疗", "change": -1.10},
        {"id": "prop", "name": "军工制造", "change": 0.85},
    ]

    # 生成基金数据 (接入真实数据，但保持你的数据结构字段不变)
    funds = []
    
    # 为了防止请求太慢，这里加个简单的 spinner
    with st.spinner('正在同步天天基金网数据...'):
        for i, (code, fallback_name, sector_id) in enumerate(TARGET_FUNDS):
            
            # 调用真实接口
            real_data = fetch_real_data(code)
            
            # 准备数据字段
            if real_data:
                name = real_data['name']
                nav = float(real_data['gsz'])
                change_pct = float(real_data['gszzl'])
            else:
                name = fallback_name
                nav = 1.0000
                change_pct = 0.00
            
            # [为了兼容你的UI：模拟分时数据]
            # 接口不提供历史分时，保留你的随机生成逻辑以适配 sparkline
            history = [nav * (1 + (np.sin(x/10) * 0.05) + (np.random.random()*0.02)) for x in range(50)]
            
            # [为了兼容你的UI：模拟持仓]
            # 接口不提供持仓，保留你的随机生成逻辑
            holdings = [
                {"name": f"股票-{j}", "percent": np.random.randint(2, 9), "change": np.random.uniform(-3, 3)} 
                for j in range(1, 11)
            ]

            # 严格保持你的字典结构
            funds.append({
                "id": f"fund-{code}", # 唯一ID
                "name": name,
                "code": code,
                "nav": nav,
                "changePercent": change_pct,
                "sectorId": sector_id,
                "history": history,
                "topHoldings": holdings
            })
    
    st.session_state.funds = funds
    st.session_state.sectors = SECTORS
    
    # 用户持仓 (Portfolio) - 使用真实数据中的前两只
    st.session_state.portfolio = [
        {**funds[0], "heldAmount": 2000, "avgCost": funds[0]['nav'] * 1.05}, # 模拟成本
        {**funds[3], "heldAmount": 500, "avgCost": funds[3]['nav'] * 0.98},
    ]
    
    # 用户自选 (Watchlist) - 使用真实数据中的ID
    st.session_state.watchlist_ids = [funds[1]['id'], funds[2]['id'], funds[5]['id']]
    st.session_state.watchlist_groups = {
        funds[1]['id']: 'all',
        funds[2]['id']: 'tech',
        funds[5]['id']: 'all'
    }
    
    st.session_state.data_initialized = True

# 状态管理 (保留你的原始逻辑)
if 'view' not in st.session_state:
    st.session_state.view = 'PORTFOLIO' # PORTFOLIO, WATCHLIST, MARKET
if 'selected_fund' not in st.session_state:
    st.session_state.selected_fund = None
if 'watchlist_active_group' not in st.session_state:
    st.session_state.watchlist_active_group = 'all'

# ==========================================
# 3. 辅助组件 (Helper Components)
# ==========================================
# [严格保留你的原版代码]

def get_color_class(value):
    return "text-up" if value >= 0 else "text-down"

def draw_sparkline(data, is_positive):
    color = '#ef4444' if is_positive else '#22c55e'
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
        # 使用 Plotly 绘制迷你图
        st.plotly_chart(draw_sparkline(fund['history'], is_up), use_container_width=True, config={'staticPlot': True})
        
    with col3:
        st.markdown(f"""
        <div style="text-align: right; line-height:1.2;">
            <div class="text-sm font-bold text-mono text-slate-800">{fund['nav']:.4f}</div>
            <div class="text-xs font-bold text-mono {color_class}">{sign}{fund['changePercent']:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 点击查看详情 (Streamlit 按钮模拟)
    if st.button(f"查看详情", key=f"btn_{fund['id']}_{int(time.time())}", use_container_width=True):
        st.session_state.selected_fund = fund
        st.rerun()
    st.markdown("---")

# ==========================================
# 4. 视图逻辑 (Views)
# ==========================================
# [严格保留你的原版代码]

def view_portfolio():
    # [功能植入] 增加一个刷新按钮，其他不变
    if st.button("🔄 刷新数据 (获取最新净值)", use_container_width=True):
        del st.session_state.data_initialized
        st.rerun()

    # 计算总资产
    total_asset = sum([item['nav'] * item['heldAmount'] for item in st.session_state.portfolio])
    total_cost = sum([item['avgCost'] * item['heldAmount'] for item in st.session_state.portfolio])
    total_gain = total_asset - total_cost
    total_gain_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0
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

    # 操作按钮
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
    
    # 分组 Tabs
    groups = [{'id': 'all', 'name': '全部'}, {'id': 'tech', 'name': '科技'}, {'id': 'safe', 'name': '稳健'}]
    
    cols = st.columns(len(groups))
    for idx, g in enumerate(groups):
        with cols[idx]:
            if st.button(g['name'], key=f"group_{g['id']}", use_container_width=True, 
                         type="primary" if st.session_state.watchlist_active_group == g['id'] else "secondary"):
                st.session_state.watchlist_active_group = g['id']
                st.rerun()
                
    # 筛选基金
    watchlist_funds = [f for f in st.session_state.funds if f['id'] in st.session_state.watchlist_ids]
    
    if st.session_state.watchlist_active_group != 'all':
        # 简单模拟分组过滤
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
    # 市场指数
    st.markdown("### 市场指数")
    
    # [功能植入] 这里尝试获取上证指数（对应代码000001在funds里）
    sh_index = next((f for f in st.session_state.funds if f['code'] == '000001'), None)
    
    indices = [
        {"name": "上证指数", "val": sh_index['nav'] if sh_index else 3050.23, "pct": sh_index['changePercent'] if sh_index else 0.45},
        {"name": "深证成指", "val": 9580.11, "pct": -0.24}, # 暂无数据
        {"name": "创业板指", "val": 1890.55, "pct": 0.28}, # 暂无数据
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
            
    # 板块风向
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

    # 市场风向标 (全部基金)
    st.markdown("### 市场风向标")
    for fund in st.session_state.funds[:5]: # 只显示前5个
        render_fund_row(fund)

def view_detail():
    fund = st.session_state.selected_fund
    
    # 顶部导航条
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

    # 核心数据区域
    is_up = fund['changePercent'] >= 0
    color_class = get_color_class(fund['changePercent'])
    sign = "+" if is_up else ""
    
    st.markdown(f"""
    <div style="background: white; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 16px; border: 1px solid #e2e8f0;">
        <div class="text-xs font-mono text-slate-400">{fund['code']}</div>
        <div class="font-mono font-bold {color_class}" style="font-size: 3rem; letter-spacing: -2px;">{fund['nav']:.4f}</div>
        <div class="font-mono font-bold text-sm {color_class}">{sign}{fund['changePercent']:.2f}%</div>
        <div class="text-xs text-slate-400 mt-2">更新于: {datetime.now().strftime('%H:%M:%S')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 图表 Tabs
    tab1, tab2 = st.tabs(["分时走势", "近30日"])
    
    with tab1:
        # 分时图
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
        # 30日模拟数据
        dates = pd.date_range(end=datetime.now(), periods=30)
        vals = [fund['nav'] * (1 + np.random.uniform(-0.05, 0.05)) for _ in range(30)]
        df_30 = pd.DataFrame({'date': dates, 'value': vals})
        fig2 = px.line(df_30, x='date', y='value')
        fig2.update_traces(line_color='#0f172a')
        fig2.update_layout(height=200, margin=dict(l=0, r=0, t=10, b=20))
        st.plotly_chart(fig2, use_container_width=True)

    # 重仓持股表格
    st.markdown("### 重仓持股")
    df_holdings = pd.DataFrame(fund['topHoldings'])
    # 格式化数据以展示
    for _, row in df_holdings.iterrows():
        c1, c2, c3 = st.columns([2, 1, 1])
        c1.write(row['name'])
        c2.write(f"{row['percent']:.2f}%")
        color = get_color_class(row['change'])
        c3.markdown(f"<span class='{color} font-bold text-mono'>{'+' if row['change']>0 else ''}{row['change']:.2f}%</span>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 4px 0; opacity: 0.5;'>", unsafe_allow_html=True)

    # 底部交易区域 (模拟 Modal)
    st.markdown("---")
    with st.expander("📝 记录交易 / 调仓", expanded=True):
        col_type = st.columns(2)
        type_buy = col_type[0].button("买入 / 加仓", use_container_width=True, type="primary")
        type_sell = col_type[1].button("卖出 / 减仓", use_container_width=True)
        
        amount = st.number_input("金额 (CNY)", value=1000.0, step=100.0)
        
        # 垂直滚动的日期选择 (Streamlit 原生只能用 select_slider 或 date_input 模拟)
        st.markdown('<label class="text-xs font-bold text-slate-500 uppercase">交易日期 (近2周)</label>', unsafe_allow_html=True)
        date_options = [(datetime.now() - timedelta(days=i)).date() for i in range(14)]
        selected_date = st.selectbox("选择日期", date_options, format_func=lambda x: x.strftime("%m月%d日 %A"))
        
        if st.button("确认提交", type="primary", use_container_width=True):
            st.success(f"已记录: {selected_date} {'买入' if not type_sell else '卖出'} {amount}元")
            time.sleep(1)
            st.session_state.selected_fund = None
            st.rerun()

# ==========================================
# 5. 主程序入口 (Main App)
# ==========================================
# [严格保留你的原版代码]

def main():
    # 检查是否处于详情模式
    if st.session_state.selected_fund is not None:
        view_detail()
        return

    # 顶部 Logo
    col_logo, col_search = st.columns([1, 2])
    with col_logo:
        st.markdown("#### 🦉 咕咕基金")
    with col_search:
        # [功能植入] 使搜索框生效
        search_query = st.text_input("Search", placeholder="搜索代码/名称", label_visibility="collapsed")
        if search_query and len(search_query) >= 6:
            # 尝试搜索并跳转
            with st.spinner("Search..."):
                res = fetch_real_data(search_query)
                if res:
                    found_fund = {
                         "id": f"fund-{search_query}",
                         "name": res['name'],
                         "code": search_query,
                         "nav": float(res['gsz']),
                         "changePercent": float(res['gszzl']),
                         "sectorId": "all",
                         "history": [float(res['gsz'])] * 50, # 模拟历史
                         "topHoldings": []
                    }
                    st.session_state.selected_fund = found_fund
                    st.rerun()

    # 主视图渲染
    if st.session_state.view == 'PORTFOLIO':
        view_portfolio()
    elif st.session_state.view == 'WATCHLIST':
        view_watchlist()
    elif st.session_state.view == 'MARKET':
        view_market()

    # 底部导航 (固定在页面最下方，使用 columns 模拟)
    st.markdown("---") # Spacer
    st.markdown("<br><br>", unsafe_allow_html=True) # Spacer for fixed nav
    
    # 使用 Streamlit columns 放在底部 (模拟 Bottom Nav)
    # 注意：Streamlit 原生不支持完全固定在底部的交互式组件，这里放在页面流的最下方
    
    # 简单的 Tab 切换器模拟底部导航
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
