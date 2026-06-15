import streamlit as st
import random
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# --- 🎮 Web Page Configuration ---
st.set_page_config(page_title="JS Casino Blackjack", page_icon="🃏", layout="centered")

# --- 🔗 데이터베이스 연결 (방어형 코드로 강화!) ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception:
        return None

def get_supabase():
    # 필요할 때마다 연결 상태를 확인하고 가져옵니다.
    return init_connection()

# ==========================================
# 🧠 세션 상태 (메모리) 초기화
# ==========================================
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
    st.session_state.player_hands = []
    st.session_state.hand_bets = []
    st.session_state.active_hand = 0
    st.session_state.current_theme = 'Classic'

# ==========================================
# 🎨 UI Style Sheet (동적 테마 반영)
# ==========================================
theme_bg = {
    'Classic': 'radial-gradient(circle at 50% 30%, #0f5132 0%, #022c18 80%, #000000 100%)',
    'Blood': 'radial-gradient(circle at 50% 30%, #4a0e17 0%, #2b050a 80%, #000000 100%)',
    'Gold': 'radial-gradient(circle at 50% 30%, #3a2f0f 0%, #1a1405 80%, #000000 100%)'
}
current_bg = theme_bg.get(st.session_state.get('current_theme', 'Classic'), theme_bg['Classic'])

st.markdown(f"""
    <style>
        @import url('https://cdn.jsdelivr.net/gh/neodgm/neodgm-webfont@1.530/neodgm/style.css');
        [data-testid="stAppViewContainer"] {{ background: {current_bg} !important; }}
        h1, h2, h3, p, span, div, label {{ font-family: 'NeoDunggeunmo', sans-serif !important; color: white; }}
        h1 {{ color: #facc15 !important; text-align: center !important; text-shadow: 0 4px 6px rgba(0,0,0,0.5); font-size: 3.5rem !important; margin-bottom: 0 !important;}}
        
        .coin-box {{ background-color: rgba(0, 0, 0, 0.6); border: 2px solid #facc15; padding: 15px; border-radius: 10px; text-align: center; color: #facc15; font-size: 1.5rem; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin: 10px 0; }}
        .timer-box {{ border-color: #3b82f6 !important; color: #3b82f6 !important; }}
        .debt-box {{ border-color: #f43f5e !important; color: #f43f5e !important; }}
        .combo-box {{ border-color: #34d399 !important; color: #34d399 !important; }}
        
        .real-card {{ background-color: white !important; border-radius: 8px !important; width: 90px !important; height: 130px !important; margin: 0 8px !important; box-shadow: 2px 5px 15px rgba(0,0,0,0.6) !important; display: inline-block !important; position: relative !important; font-family: 'Arial', sans-serif !important; }}
        .card-top {{ position: absolute !important; top: 8px !important; left: 8px !important; font-size: 1.2rem !important; font-weight: bold !important; line-height: 1 !important; text-align: left !important; }}
        .card-center {{ position: absolute !important; top: 50% !important; left: 50% !important; transform: translate(-50%, -50%) !important; font-size: 3rem !important; }}
        .card-red, .card-red div {{ color: #dc2626 !important; }}
        .card-black, .card-black div {{ color: #171717 !important; }}
        .card-hidden {{ background: repeating-linear-gradient(45deg, #b91c1c, #b91c1c 10px, #7f1d1d 10px, #7f1d1d 20px) !important; border: 3px solid white !important; border-radius: 8px !important; width: 90px !important; height: 130px !important; margin: 0 8px !important; box-shadow: 2px 5px 15px rgba(0,0,0,0.6) !important; display: inline-block !important; }}

        .stButton>button {{ background-color: rgba(0, 0, 0, 0.7) !important; color: white !important; border: 2px solid #ffffff !important; border-radius: 30px !important; font-size: 1.2rem !important; transition: 0.2s; width: 100%; height: 55px; }}
        .stButton>button:hover {{ background-color: white !important; color: #022c18 !important; transform: scale(1.05); box-shadow: 0 0 15px rgba(255,255,255,0.5) !important; }}
        .btn-red>button {{ border-color: #f43f5e !important; color: #f43f5e !important; }}
        .btn-red>button:hover {{ background-color: #f43f5e !important; color: white !important; box-shadow: 0 0 15px #f43f5e !important;}}
        .btn-yellow>button {{ border-color: #facc15 !important; color: #facc15 !important; }}
        .btn-yellow>button:hover {{ background-color: #facc15 !important; color: black !important; box-shadow: 0 0 15px #facc15 !important;}}
        .btn-blue>button {{ border-color: #3b82f6 !important; color: #3b82f6 !important; }}
        .btn-blue>button:hover {{ background-color: #3b82f6 !important; color: white !important; box-shadow: 0 0 15px #3b82f6 !important;}}
        .stNumberInput input {{ background-color: rgba(0,0,0,0.5) !important; color: #facc15 !important; border: 1px solid #facc15 !important; font-size: 1.5rem !important; text-align: center !important; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 💾 데이터베이스 & 시스템 함수
# ==========================================
def load_user(username):
    try:
        db = get_supabase()
        if not db: return None
        response = db.table("casino_players").select("*").eq("username", username).execute()
        if len(response.data) > 0:
            return response.data[0]
        else:
            new_user = {
                "username": username, "coins": 1000, "debt": 0, "combo": 0, "last_rescue": None, "loan_count": 0,
                "current_title": "새내기", "current_theme": "Classic", "purchased_titles": "새내기", "purchased_themes": "Classic"
            }
            res = db.table("casino_players").insert(new_user).execute()
            return res.data[0]
    except Exception:
        return None

def save_user_data():
    if 'username' in st.session_state:
        try:
            db = get_supabase()
            if db:
                db.table("casino_players").update({
                    "coins": st.session_state.coins,
                    "debt": st.session_state.debt,
                    "combo": st.session_state.combo,
                    "loan_count": st.session_state.loan_count,
                    "current_title": st.session_state.current_title,
                    "current_theme": st.session_state.current_theme,
                    "purchased_titles": st.session_state.purchased_titles,
                    "purchased_themes": st.session_state.purchased_themes
                }).eq("username", st.session_state.username).execute()
        except Exception:
            pass

def get_rescue_time_left():
    if not st.session_state.get('last_rescue'): return 0
    last = datetime.fromisoformat(st.session_state.last_rescue)
    now = datetime.now(timezone.utc)
    diff = now - last
    if diff > timedelta(minutes=3): return 0
    return (timedelta(minutes=3) - diff).seconds

def claim_rescue():
    try:
        db = get_supabase()
        if db:
            now_iso = datetime.now(timezone.utc).isoformat()
            db.table("casino_players").update({
                "coins": 500, "last_rescue": now_iso
            }).eq("username", st.session_state.username).execute()
            st.session_state.coins = 500
            st.session_state.last_rescue = now_iso
    except Exception:
        pass

def reset_game_completely():
    st.session_state.coins = 1000
    st.session_state.debt = 0
    st.session_state.combo = 0
    st.session_state.loan_count = 0
    st.session_state.current_title = "새내기"
    st.session_state.current_theme = "Classic"
    st.session_state.purchased_titles = "새내기"
    st.session_state.purchased_themes = "Classic"
    st.session_state.game_phase = 'BETTING'
    st.session_state.player_hands = []
    st.session_state.dealer_hand = []
    save_user_data()

# ==========================================
# 🃏 엔진 및 시각화 함수
# ==========================================
def create_deck():
    suits, ranks = ['♠', '♥', '♦', '♣'], ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    deck = [f"{suit}{rank}" for suit in suits for rank in ranks]
    random.shuffle(deck)
    return deck

def calculate_score(hand):
    score, aces = 0, 0
    for card in hand:
        rank = card[1:]
        if rank in ['J', 'Q', 'K']: score += 10
        elif rank == 'A': aces += 1; score += 11
        else: score += int(rank)
    while score > 21 and aces > 0: score -= 10; aces -= 1
    return score

def render_cards(hand, hide_second=False):
    html = ""
    for i, card in enumerate(hand):
        if hide_second and i == 1:
            html += '<div class="card-hidden"></div>'
            continue
        suit, rank = card[0], card[1:]
        color_class = "card-red" if suit in ['♥', '♦'] else "card-black"
        html += f'<div class="real-card {color_class}"><div class="card-top">{rank}<br>{suit}</div><div class="card-center">{suit}</div></div>'
    return f'<div style="text-align:center; margin: 10px 0; display:flex; justify-content:center; flex-wrap:wrap;">{html}</div>'

# ==========================================
# 🎮 게임 로직
# ==========================================
def start_game(bet):
    st.session_state.hand_bets = [bet]
    st.session_state.coins -= bet
    if len(st.session_state.deck) < 15: st.session_state.deck = create_deck()
    st.session_state.player_hands = [[st.session_state.deck.pop(), st.session_state.deck.pop()]]
    st.session_state.dealer_hand = [st.session_state.deck.pop(), st.session_state.deck.pop()]
    st.session_state.active_hand = 0
    st.session_state.game_phase = 'PLAYING'
    st.session_state.msg = ""
    
    if calculate_score(st.session_state.player_hands[0]) == 21:
        st.session_state.game_phase = 'GAME_OVER'
        st.session_state.combo += 1
        st.session_state.msg = "🎉 대박! 첫 판에 블랙잭!! (배팅액의 2.5배 획득)"
        st.session_state.coins += int(bet * 2.5)
        save_user_data()

def split():
    bet = st.session_state.hand_bets[0]
    st.session_state.coins -= bet
    st.session_state.hand_bets.append(bet)
    c1, c2 = st.session_state.player_hands[0][0], st.session_state.player_hands[0][1]
    st.session_state.player_hands = [[c1, st.session_state.deck.pop()], [c2, st.session_state.deck.pop()]]

def next_hand_or_dealer():
    st.session_state.active_hand += 1
    if st.session_state.active_hand >= len(st.session_state.player_hands):
        st.session_state.game_phase = 'DEALER_TURN'

def hit():
    idx = st.session_state.active_hand
    st.session_state.player_hands[idx].append(st.session_state.deck.pop())
    if calculate_score(st.session_state.player_hands[idx]) > 21: next_hand_or_dealer()

def double_down():
    idx = st.session_state.active_hand
    st.session_state.coins -= st.session_state.hand_bets[idx]
    st.session_state.hand_bets[idx] *= 2
    st.session_state.player_hands[idx].append(st.session_state.deck.pop())
    next_hand_or_dealer()

def reveal_dealer():
    st.session_state.game_phase = 'GAME_OVER'
    all_busted = all(calculate_score(h) > 21 for h in st.session_state.player_hands)
    dealer_score = calculate_score(st.session_state.dealer_hand)
    if not all_busted:
        while dealer_score < 17:
            st.session_state.dealer_hand.append(st.session_state.deck.pop())
            dealer_score = calculate_score(st.session_state.dealer_hand)
    msgs, earned, combo_won = [], 0, False
    for i, hand in enumerate(st.session_state.player_hands):
        p_score = calculate_score(hand)
        bet = st.session_state.hand_bets[i]
        prefix = f"[핸드 {i+1}] " if len(st.session_state.player_hands) > 1 else ""
        if p_score > 21: msgs.append(f"{prefix}💥 BUST! (21 초과)")
        elif dealer_score > 21: msgs.append(f"{prefix}🎉 딜러 BUST! 승리!"); earned += bet * 2; combo_won = True
        elif p_score > dealer_score: msgs.append(f"{prefix}🎉 승리! ({p_score} vs {dealer_score})"); earned += bet * 2; combo_won = True
        elif p_score < dealer_score: msgs.append(f"{prefix}😢 패배... ({p_score} vs {dealer_score})")
        else: msgs.append(f"{prefix}🤝 무승부"); earned += bet
    st.session_state.coins += earned
    if combo_won: st.session_state.combo += 1
    else: st.session_state.combo = 0
    st.session_state.msg = "<br>".join(msgs)
    save_user_data()

# ==========================================
# 🖥️ 게임 화면 (UI)
# ==========================================
st.markdown("<h1>♣️ JS 블랙잭 카지노 ♠️</h1>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    # --- 로그인 화면 ---
    st.markdown("<br><h3 style='text-align:center; color:#e0e7ff;'>VIP 라운지 입장</h3>", unsafe_allow_html=True)
    username_input = st.text_input("닉네임을 입력하세요", max_chars=12, placeholder="예: JunSeok99")
    if st.button("🚪 카지노 입장하기"):
        if username_input.strip():
            user_data = load_user(username_input.strip())
            if user_data:
                st.session_state.username = user_data['username']
                st.session_state.coins = user_data['coins']
                st.session_state.debt = user_data['debt']
                st.session_state.combo = user_data['combo']
                st.session_state.loan_count = user_data.get('loan_count', 0)
                st.session_state.current_title = user_data.get('current_title', '새내기')
                st.session_state.current_theme = user_data.get('current_theme', 'Classic')
                st.session_state.purchased_titles = user_data.get('purchased_titles', '새내기')
                st.session_state.purchased_themes = user_data.get('purchased_themes', 'Classic')
                st.session_state.last_rescue = user_data.get('last_rescue')
                st.session_state.deck = create_deck()
                st.session_state.game_phase = 'BETTING'
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("⚠️ 서버 연결이 지연되고 있습니다. 잠시 후 다시 시도해주세요!")
        else:
            st.warning("닉네임을 입력해야 입장할 수 있습니다!")

    st.divider()
    st.markdown("<h3 style='text-align:center; color:#facc15;'>🏆 카지노 명예의 전당 (Top 5 갑부)</h3>", unsafe_allow_html=True)
    try:
        db = get_supabase()
        if db:
            top_players = db.table("casino_players").select("username, coins, current_title").order("coins", desc=True).limit(5).execute()
            for idx, player in enumerate(top_players.data):
                medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "🏅"
                t_title = f"[{player['current_title']}] " if player.get('current_title') else ""
                st.markdown(f"<p style='text-align:center; font-size:1.3rem;'>{medal} {t_title}<b>{player['username']}</b> : 💰 {player['coins']}</p>", unsafe_allow_html=True)
    except: pass

else:
    # --- 상단 탭 나누기 ---
    tab_game, tab_shop = st.tabs(["🃏 게임 테이블", "🛒 VIP 상점"])

    with tab_game:
        st.markdown(f"<p style='text-align:right; color:#94a3b8;'>👤 [{st.session_state.current_title}] {st.session_state.username}</p>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a: st.markdown(f'<div class="coin-box">💰 내 지갑: {st.session_state.coins}</div>', unsafe_allow_html=True)
        with col_b:
            if st.session_state.coins <= 0 and st.session_state.debt > 0: st.markdown(f'<div class="coin-box debt-box">🚨 DIE 예정</div>', unsafe_allow_html=True)
            elif st.session_state.debt > 0: st.markdown(f'<div class="coin-box debt-box">💀 사채 빚: {st.session_state.debt}</div>', unsafe_allow_html=True)
            elif st.session_state.combo >= 2: st.markdown(f'<div class="coin-box combo-box">🔥 {st.session_state.combo} 연승 중!</div>', unsafe_allow_html=True)
            else: st.markdown(f'<div class="coin-box" style="color:#aaa; border-color:#aaa;">🎲 대기 중</div>', unsafe_allow_html=True)

        if st.session_state.game_phase == 'BETTING':
            if st.session_state.coins > 0:
                max_bet = st.session_state.coins
                bet_amount = st.number_input("BET AMOUNT", min_value=10, max_value=max_bet, value=min(100, max_bet), step=10, label_visibility="collapsed")
                if st.button("🚀 게임 시작 (DEAL)"): start_game(bet_amount); st.rerun()
                if st.session_state.debt > 0 and st.session_state.coins >= st.session_state.debt:
                    if st.button(f"👼 사채 {st.session_state.debt} 코인 전액 상환하기"):
                        st.session_state.coins -= st.session_state.debt; st.session_state.debt = 0; save_user_data(); st.rerun()
            else:
                if st.session_state.debt > 0:
                    st.markdown("<h2 style='text-align:center; color:#f43f5e;'>💀 DIE 💀</h2>", unsafe_allow_html=True)
                    st.error("사채를 갚지 못하고 파산했습니다! 신분 세탁(강제 초기화)을 당합니다.")
                    if st.button("🔄 새로운 인생 세탁하기"): reset_game_completely(); st.rerun()
                else:
                    time_left = get_rescue_time_left()
                    if time_left <= 0:
                        if st.button("👼 구제금융 500 코인 받기"): claim_rescue(); st.rerun()
                    else:
                        st.error(f"💸 파산! 구제금융 대기: {time_left // 60}분 {time_left % 60}초")
                        if st.button("🔄 남은 시간 확인"): st.rerun()
                    st.markdown("<p style='text-align:center; color:#aaa;'>--- OR ---</p>", unsafe_allow_html=True)
                    if st.session_state.loan_count < 3:
                        if st.button(f"💀 사채 1000 코인 대출 (남은 기회: {3 - st.session_state.loan_count}번)"):
                            st.session_state.coins = 1000; st.session_state.debt = 1500; st.session_state.loan_count += 1; save_user_data(); st.rerun()
                    else:
                        if st.button("💀 대출 한도 초과! 억지로 빌리기 (누르면 즉시 DIE)"): reset_game_completely(); st.rerun()

        elif st.session_state.game_phase in ['PLAYING', 'DEALER_TURN', 'GAME_OVER']:
            st.markdown("<h3 style='text-align:center; color:#e0e7ff;'>🤖 딜러</h3>", unsafe_allow_html=True)
            hide_dealer_card = (st.session_state.game_phase in ['PLAYING', 'DEALER_TURN'])
            st.markdown(render_cards(st.session_state.dealer_hand, hide_second=hide_dealer_card), unsafe_allow_html=True)
            
            # --- 💡 딜러 점수 추가 부분 ---
            if hide_dealer_card:
                visible_score = calculate_score([st.session_state.dealer_hand[0]])
                st.markdown(f"<p style='text-align:center; color:#94a3b8; font-size:1.1rem; margin-top:-10px;'>오픈된 점수: <b>{visible_score}</b></p>", unsafe_allow_html=True)
            else:
                final_score = calculate_score(st.session_state.dealer_hand)
                st.markdown(f"<p style='text-align:center; color:#facc15; font-size:1.1rem; margin-top:-10px;'>최종 점수: <b>{final_score}</b></p>", unsafe_allow_html=True)
            # -----------------------------
            
            st.divider()
            st.markdown("<h3 style='text-align:center; color:#e0e7ff;'>🙋‍♂️ 플레이어</h3>", unsafe_allow_html=True)
            for i, hand in enumerate(st.session_state.player_hands):
                is_active = (i == st.session_state.active_hand and st.session_state.game_phase == 'PLAYING')
                style = "border: 2px solid #facc15; border-radius: 15px;" if is_active else ""
                st.markdown(f"<div style='{style}'>", unsafe_allow_html=True)
                st.markdown(render_cards(hand), unsafe_allow_html=True)
                st.markdown(f"<p style='text-align:center; font-size:1.1rem;'>점수: <b>{calculate_score(hand)}</b> (배팅: {st.session_state.hand_bets[i]})</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.game_phase == 'PLAYING':
                idx = st.session_state.active_hand
                hand = st.session_state.player_hands[idx]
                can_split = (len(hand) == 2 and len(st.session_state.player_hands) == 1 and hand[0][1:] == hand[1][1:] and st.session_state.coins >= st.session_state.hand_bets[0])
                cols = st.columns(4 if can_split else 3)
                with cols[0]:
                    if st.button("🃏 HIT"): hit(); st.rerun()
                with cols[1]:
                    if st.button("🛑 STAND"): next_hand_or_dealer(); st.rerun()
                with cols[2]:
                    if len(hand) == 2 and st.session_state.coins >= st.session_state.hand_bets[idx]:
                        if st.button("🔥 DOUBLE"): double_down(); st.rerun()
                if can_split:
                    with cols[3]:
                        if st.button("✂️ SPLIT"): split(); st.rerun()
            elif st.session_state.game_phase == 'DEALER_TURN':
                if st.button("🚨 딜러 카드 오픈"): reveal_dealer(); st.rerun()
            elif st.session_state.game_phase == 'GAME_OVER':
                st.markdown(f"<div style='text-align:center; font-size:1.3rem;'>{st.session_state.msg}</div>", unsafe_allow_html=True)
                if st.button("🔄 다음 판 가기 (NEXT)"): st.session_state.game_phase = 'BETTING'; st.rerun()

    with tab_shop:
        # --- 🛒 VIP 상점 화면 ---
        st.markdown("<h2 style='text-align:center; color:#facc15;'>🛒 VIP 카지노 상점</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>현재 보유 코인: 💰 {st.session_state.coins}</p>", unsafe_allow_html=True)
        st.divider()
        
        # 1. 칭호 판매 리스트
        st.markdown("### 💎 명예 칭호 구매/착용")
        titles = [
            ("동네 호구", 1000),
            ("강원랜드 VIP", 10000),
            ("라스베이거스 타짜", 50000),
            ("👑 카지노 오너", 100000)
        ]
        purchased_titles_list = st.session_state.purchased_titles.split(",")
        
        for name, price in titles:
            col1, col2 = st.columns([3, 2])
            with col1: st.write(f"**{name}** (가격: 💰 {price:,} 코인)")
            with col2:
                if name in purchased_titles_list:
                    if st.session_state.current_title == name:
                        st.write("✨ 착용 중")
                    else:
                        if st.button(f"착용하기", key=f"eq_t_{name}"):
                            st.session_state.current_title = name; save_user_data(); st.rerun()
                else:
                    if st.button(f"구매 (💰 {price:,})", key=f"buy_t_{name}"):
                        if st.session_state.coins >= price:
                            st.session_state.coins -= price
                            st.session_state.purchased_titles += f",{name}"
                            st.session_state.current_title = name
                            save_user_data(); st.rerun()
                        else: st.error("코인이 부족합니다!")
        st.divider()

        # 2. 테마 판매 리스트
        st.markdown("### 🎨 카지노 테이블 인테리어")
        themes = [
            ("Classic", "기본 초록 테이블", 0),
            ("Blood", "🩸 핏빛 블러드 레드 테이블", 5000),
            ("Gold", "👑 황금 VIP 럭셔리 테이블", 20000)
        ]
        purchased_themes_list = st.session_state.purchased_themes.split(",")
        
        for code, disp_name, price in themes:
            col1, col2 = st.columns([3, 2])
            with col1: st.write(f"**{disp_name}** (가격: 💰 {price:,} 코인)")
            with col2:
                if code in purchased_themes_list:
                    if st.session_state.current_theme == code:
                        st.write("✨ 인테리어 적용 중")
                    else:
                        if st.button(f"변경하기", key=f"eq_th_{code}"):
                            st.session_state.current_theme = code; save_user_data(); st.rerun()
                else:
                    if st.button(f"인테리어 시공 (💰 {price:,})", key=f"buy_th_{code}"):
                        if st.session_state.coins >= price:
                            st.session_state.coins -= price
                            st.session_state.purchased_themes += f",{code}"
                            st.session_state.current_theme = code
                            save_user_data(); st.rerun()
                        else: st.error("코인이 부족합니다!")
