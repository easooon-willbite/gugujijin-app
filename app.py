import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import json
import re
from datetime import datetime
import time

# ==========================================
# 1. 核心数据引擎 (Real Data Engine)
# ==========================================

@st.cache_data(ttl=60) # 缓存60秒，避免频繁请求
def get_fund_realtime(code):
    """获取单个基金的实时估值"""
    try:
        url = f"http://fundgz.1234567.com.cn/js/{code}.js"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=3)
        res.encoding = 'utf-8'
        text = res.text
        
        if "jsonpgz(" in text:
            content = text.split("jsonpgz(")[1].rstrip(");")
            data = json.loads(content)
            
            # 构造符合我们 App 格式的数据字典
            return {
                "id": code,
                "code": code,
                "name": data['name'],
                "nav": float(data['gsz']), # 实时估值
                "nav_date": data['gztime'],
                "changePercent": float(data['gszzl']),
                "prev_nav": float(data['dwjz']), # 昨日净值
                "update_time": data['gztime']
            }
    except:
        return None

def get_market_indices():
    """获取市场核心指数 (用ETF替代指数，因为数据源限制)"""
    # 000300(沪深300), 159915(创业板), 159949(创业板50) -> 这里用热门指数基金代替大盘看板
    indices = [
        {"code": "000001", "name": "上证指数(参考华夏)", "proxy": "000001"}, 
        {"code": "161725", "name": "白酒指数(招商)", "proxy": "161725"},
        {"code": "007460", "name": "半导体(华夏)", "proxy": "007460"}
    ]
    results = []
    for idx in indices:
        data = get_fund_realtime(idx['code']) # 注意：这里为了简便，用场外联接基金走势代表大盘
        if data:
            results.append({
                "name": idx['name'], 
                "val": data['nav'], 
                "pct": data['changePercent']
            })
    return results

# ==========================================
# 2. 配置与样式 (Configuration & CSS)
# ==========================================
st.set_page_config(
    page_title="咕咕基金",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
    
    /* 卡片风格 */
    .asset-card {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        border-radius: 16px;
        padding: 20px;
        color: white;
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.2);
        margin-bottom: 24px;
    }
    
    /* 涨跌颜色 */
    .text-up { color: #dc2626; font-weight: 600; }
    .text-down { color: #16a34a; font-weight: 600; }
    .text-gray { color: #64748b; }
    
    /* 列表项 */
    .fund-row {
        background: white;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: transform 0.1s;
    }
    .fund-row:active { transform: scale(0.98); }
    
    /* 底部导航占位 */
    .bottom-spacer { height: 80px; }
    
    /* 隐藏 Streamlit 按钮边框，使其更像点击区域 */
    .stButton button {
        border: none;
        background: transparent;
        box-shadow: none;
        padding: 0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 状态管理 (State Management)
# ==========================================

# 初始化默认基金列表 (如果第一次打开)
if 'init_setup' not in st.session_state:
    # 预设一些热门基金代码
    default_codes = ["161725", "005827", "000001", "161028", "001156"]
    st.session_state.my_funds = []
    
    # 首次加载去抓取一下
    with st.spinner("正在连接交易所..."):
        for code in default_codes:
            f_data = get_fund_realtime(code)
            if f_data:
                # 模拟持仓数据 (held_share: 持有份额, cost: 成本价)
                f_data['held_share'] = 1000 if code == "161725" else 0 
                f_data['cost'] = f_data['nav'] * 1.02 # 假装亏一点
                st.session_state.my_funds.append(f_data)
                
    st.session_state.watchlist = ["003096", "001594"] # 也是代码
    st.session_state.view = 'PORTFOLIO'
    st.session_state.init_setup = True

if 'selected_fund_detail' not in st.session_state:
    st.session_state.selected_fund_detail = None

# ==========================================
# 4. 辅助函数 (Helpers)
# ==========================================

def render_fund_card(fund, is_holding=False):
    """渲染列表中的单行基金"""
    is_up = fund['changePercent'] >= 0
    color = "text-up" if is_up else "text-down"
    sign = "+" if is_up else ""
    
    # 使用 Streamlit 原生布局
    with st.container():
        c1, c2, c3 = st.columns([3, 2, 2])
        
        with c1:
            st.markdown(f"**{fund['name']}**")
            st.markdown(f"<span style='color:#94a3b8; font-size:12px'>{fund['code']}</span>", unsafe_allow_html=True)
            
        with c2:
            # 迷你走势图 (用随机数模拟，因为接口没提供分时)
            mock_trend = [fund['nav'] * (1 + np.random.uniform(-0.01, 0.01)) for _ in range(10)]
            fig = px.line(y=mock_trend)
            fig.update_traces(line_color='#dc2626' if is_up else '#16a34a', line_width=2)
            fig.update_layout(showlegend=False, xaxis_visible=False, yaxis_visible=False, margin=dict(l=0,r=0,t=0,b=0), height=30)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        with c3:
            st.markdown(f"<div style='text-align:right; font-weight:bold'>{fund['nav']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:right' class='{color}'>{sign}{fund['changePercent']}%</div>", unsafe_allow_html=True)
        
        # 点击进入详情
        if st.button(f"查看详情 {fund['code']}", key=f"btn_{fund['code']}"):
            st.session_state.selected_fund_detail = fund
            st.rerun()
        
        st.markdown("<hr style='margin:8px 0; opacity:0.3'>", unsafe_allow_html=True)

# ==========================================
# 5. 页面视图 (Views)
# ==========================================

def view_portfolio():
    # 重新获取最新数据 (刷新)
    if st.button("🔄 刷新数据", use_container_width=True):
        updated_funds = []
        for f in st.session_state.my_funds:
            new_data = get_fund_realtime(f['code'])
            if new_data:
                # 保留持仓信息
                new_data['held_share'] = f.get('held_share', 0)
                new_data['cost'] = f.get('cost', 0)
                updated_funds.append(new_data)
        st.session_state.my_funds = updated_funds
        st.toast("数据已更新", icon="✅")

    # 计算总资产
    total_asset = sum([f['nav'] * f['held_share'] for f in st.session_state.my_funds])
    total_profit = sum([(f['nav'] - f['cost']) * f['held_share'] for f in st.session_state.my_funds])
    
    st.markdown(f"""
    <div class="asset-card">
        <div style="font-size:12px; opacity:0.8">总资产估值 (CNY)</div>
        <div style="font-size:32px; font-weight:bold; font-family:monospace">{total_asset:,.2f}</div>
        <div style="margin-top:10px; display:flex; gap:20px">
            <div>
                <div style="font-size:10px; opacity:0.8">持有收益</div>
                <div style="font-weight:bold">{total_profit:+.2f}</div>
            </div>
            <div>
                <div style="font-size:10px; opacity:0.8">今日预估</div>
                <div style="font-weight:bold">{(total_asset * 0.005):+.2f} (模拟)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("我的持仓")
    # 只显示有持仓份额的
    holdings = [f for f in st.session_state.my_funds if f['held_share'] > 0]
    if not holdings:
        st.info("暂无持仓，请点击搜索添加")
    for fund in holdings:
        render_fund_card(fund, is_holding=True)

def view_watchlist():
    st.subheader("自选关注")
    # 遍历自选列表并实时获取
    for code in st.session_state.watchlist:
        data = get_fund_realtime(code)
        if data:
            render_fund_card(data)
        else:
            st.warning(f"无法获取 {code} 数据")

def view_market():
    st.subheader("市场风向")
    indices = get_market_indices()
    
    cols = st.columns(3)
    for i, idx in enumerate(indices):
        is_up = idx['pct'] >= 0
        color = "#dc2626" if is_up else "#16a34a"
        with cols[i]:
            st.markdown(f"""
            <div style="background:white; padding:10px; border-radius:8px; text-align:center; border:1px solid #e2e8f0">
                <div style="font-size:12px; color:#64748b">{idx['name']}</div>
                <div style="font-size:18px; font-weight:bold; color:{color}">{idx['val']}</div>
                <div style="font-size:12px; font-weight:bold; color:{color}">{idx['pct']}%</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.write("")
    st.subheader("热门基金 (实时)")
    # 这里我们随机展示一些热门代码
    hot_codes = ["005918", "005827", "161725", "003096"]
    for code in hot_codes:
        data = get_fund_realtime(code)
        if data:
            render_fund_card(data)

def view_detail_page():
    fund = st.session_state.selected_fund_detail
    
    if st.button("← 返回列表"):
        st.session_state.selected_fund_detail = None
        st.rerun()
        
    st.title(fund['name'])
    st.caption(f"代码: {fund['code']} | 更新: {fund['update_time']}")
    
    # 大数字
    is_up = fund['changePercent'] >= 0
    color = "red" if is_up else "green"
    
    c1, c2 = st.columns(2)
    c1.metric("实时估值", f"{fund['nav']}", delta=f"{fund['changePercent']}%")
    c2.metric("昨日净值", f"{fund['prev_nav']}")
    
    # 模拟持仓操作
    with st.expander("交易操作", expanded=True):
        col1, col2 = st.columns(2)
        if col1.button("买入", use_container_width=True, type="primary"):
            # 简单模拟加仓逻辑
            new_fund = fund.copy()
            new_fund['held_share'] = 1000
            new_fund['cost'] = fund['nav']
            # 检查是否已存在
            existing = next((f for f in st.session_state.my_funds if f['code'] == fund['code']), None)
            if existing:
                existing['held_share'] += 1000
            else:
                st.session_state.my_funds.append(new_fund)
            st.toast(f"已买入 {fund['name']}", icon="💰")
            
        if col2.button("加入自选", use_container_width=True):
            if fund['code'] not in st.session_state.watchlist:
                st.session_state.watchlist.append(fund['code'])
                st.toast("已加入自选")

# ==========================================
# 6. 主程序 (Main)
# ==========================================

def main():
    # 1. 如果有详情页请求，优先显示详情
    if st.session_state.selected_fund_detail:
        view_detail_page()
        return

    # 2. 顶部搜索栏 (全局)
    search_query = st.text_input("🔍 搜索基金代码 (如 161725)", key="search_box")
    if search_query and len(search_query) >= 6:
        # 执行搜索
        with st.spinner("查找中..."):
            res = get_fund_realtime(search_query)
            if res:
                st.session_state.selected_fund_detail = res
                st.rerun() # 立即跳转详情
            else:
                st.error("未找到该基金，请检查代码")

    # 3. 页面内容
    if st.session_state.view == 'PORTFOLIO':
        view_portfolio()
    elif st.session_state.view == 'WATCHLIST':
        view_watchlist()
    elif st.session_state.view == 'MARKET':
        view_market()
        
    # 4. 底部导航栏 (Bottom Nav)
    st.markdown("<div class='bottom-spacer'></div>", unsafe_allow_html=True)
    
    # 这是一个稍微 Hacky 的底部导航写法，为了模拟 App 体验
    cols = st.columns(3)
    if cols[0].button("💼 资产", use_container_width=True, type="primary" if st.session_state.view=='PORTFOLIO' else "secondary"):
        st.session_state.view = 'PORTFOLIO'
        st.rerun()
    if cols[1].button("⭐ 自选", use_container_width=True, type="primary" if st.session_state.view=='WATCHLIST' else "secondary"):
        st.session_state.view = 'WATCHLIST'
        st.rerun()
    if cols[2].button("📊 行情", use_container_width=True, type="primary" if st.session_state.view=='MARKET' else "secondary"):
        st.session_state.view = 'MARKET'
        st.rerun()

if __name__ == "__main__":
    main()