import streamlit as st
import random
from supabase import create_client, Client

# --- 🎮 Web Page Configuration ---
st.set_page_config(page_title="JS Casino Blackjack", page_icon="🃏", layout="centered")

# --- 🔗 데이터베이스 연결 ---
@st.cache_resource
def init_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error("데이터베이스 연결에 실패했습니다. 설정을 확인해주세요.")
    st.stop()

# ==========================================
# 🎨 UI Style Sheet
# ==========================================
st.markdown("""
    <style>
        @import url('https://cdn.jsdelivr.net/gh/neodgm/neodgm-webfont@1.530/neodgm/style.css');
        [data-testid="stAppViewContainer"] { background: radial-gradient(circle at 50% 30%, #0f5132 0%, #022c18 80%, #000000 100%) !important; }
        h1, h2, h3, p, span, div, label { font-family: 'NeoDunggeunmo', sans-serif !important; color: white; }
        h1 { color: #facc15 !important; text-align: center !important; text-shadow: 0 4px 6px rgba(0,0,0,0.5); font-size: 3.5rem !important; margin-bottom: 0 !important;}
        
        .coin-box { background-color: rgba(0, 0, 0, 0.6); border: 2px solid #facc15; padding: 15px; border-radius: 10px; text-align: center; color: #facc15; font-size: 1.5rem; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin: 10px 0; }
        .debt-box { border-color: #f43f5e !important; color: #f43f5e !important; }
        .combo-box { border-color: #34d399 !important; color: #34d399 !important; }
        
        .real-card { background-color: white !important; border-radius: 8px !important; width: 90px !important; height: 130px !important; margin: 0 8px !important; box-shadow: 2px 5px 15px rgba(0,0,0,0.6) !important; display: inline-block !important; position: relative !important; font-family: 'Arial', sans-serif !important; }
        .card-top { position: absolute !important; top: 8px !important; left: 8px !important; font-size: 1.2rem !important; font-weight: bold !important; line-height: 1 !important; text-align: left !important; }
        .card-center { position: absolute !important; top: 50% !important; left: 50% !important; transform: translate(-50%, -50%) !important; font-size: 3rem !important; }
        .card-red, .card-red div { color: #dc2626 !important; }
        .card-black, .card-black div { color: #171717 !important; }
        .card-hidden { background: repeating-linear-gradient(45deg, #b91c1c, #b91c1c 10px, #7f1d1d 10px, #7f1d1d 20px) !important; border: 3px solid white !important; border-radius: 8px !important; width: 90px !important; height: 130px !important; margin: 0 8px !important; box-shadow: 2px 5px 15px rgba(0,0,0,0.6) !important; display: inline-block !important; }

        .stButton>button { background-color: rgba(0, 0, 0, 0.7) !important; color: white !important; border: 2px solid #ffffff !important; border-radius: 30px !important; font-size: 1.2rem !important; transition: 0.2s; width: 100%; height: 55px; }
        .stButton>button:hover { background-color: white !important; color: #022c18 !important; transform: scale(1.05); box-shadow: 0 0 15px rgba(255,255,255,0.5) !important; }
        .btn-red>button { border-color: #f43f5e !important; color: #f43f5e !important; }
        .btn-red>button:hover { background-color: #f43f5e !important; color: white !important; box-shadow: 0 0 15px #f43f5e !important;}
        .btn-yellow>button { border-color: #facc15 !important; color: #facc15 !important; }
        .btn-yellow>button:hover { background-color: #facc15 !important; color: black !important; box-shadow: 0 0 15px #facc15 !important;}
        .stNumberInput input { background-color: rgba(0,0,0,0.5) !important; color: #facc15 !important; border: 1px solid #facc15 !important; font-size: 1.5rem !important; text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 💾 데이터베이스 함수
# ==========================================
def load_user(username):
    response = supabase.table("casino_players").select("*").eq("username", username).execute()
    if len(response.data) > 0:
        return response.data[0]
    else:
        new_user = {"username": username, "coins": 1000, "debt": 0, "combo": 0}
        res = supabase.table("casino_players").insert(new_user).execute()
        return res.data[0]

def save_user_data():
    if 'username' in st.session_state:
        supabase.table("casino_players").update({
            "coins": st.session_state.coins,
            "debt": st.session_state.debt,
            "combo": st.session_state.combo
        }).eq("username", st.session_state.username).execute()

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
    return f'<div style="text-align:center; margin: 20px 0; display:flex; justify-content:center; flex-wrap:wrap;">{html}</div>'

def get_combo_multiplier():
    if st.session_state.combo >= 4: return 2.0
    elif st.session_state.combo >= 3: return 1.5
    return 1.0

# ==========================================
# 🧠 세션 상태 (메모리)
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# ==========================================
# 🎮 게임 로직
# ==========================================
def start_game(bet):
    st.session_state.current_bet = bet
    st.session_state.coins -= bet
    if len(st.session_state.deck) < 15: st.session_state.deck = create_deck()
    st.session_state.player_hand = [st.session_state.deck.pop(), st.session_state.deck.pop()]
    st.session_state.dealer_hand = [st.session_state.deck.pop(), st.session_state.deck.pop()]
    st.session_state.game_phase = 'PLAYING'
    st.session_state.msg = ""
    
    if calculate_score(st.session_state.player_hand) == 21:
        st.session_state.game_phase = 'GAME_OVER'
        st.session_state.combo += 1
        st.session_state.msg = "🎉 대박! 첫 판에 블랙잭!! (배팅액의 2.5배 획득)"
        st.session_state.coins += int(bet * 2.5)
        save_user_data() # DB 저장

def hit():
    st.session_state.player_hand.append(st.session_state.deck.pop())
    if calculate_score(st.session_state.player_hand) > 21:
        st.session_state.game_phase = 'GAME_OVER'
        st.session_state.combo = 0
        st.session_state.msg = "💥 BUST! 21점을 초과했습니다. 딜러가 승리했습니다."
        save_user_data() # DB 저장

def double_down():
    st.session_state.coins -= st.session_state.current_bet
    st.session_state.current_bet *= 2
    st.session_state.player_hand.append(st.session_state.deck.pop())
    if calculate_score(st.session_state.player_hand) > 21:
        st.session_state.game_phase = 'GAME_OVER'
        st.session_state.combo = 0
        st.session_state.msg = "💥 BUST! 더블다운 실패... 21점을 초과했습니다."
        save_user_data() # DB 저장
    else:
        st.session_state.game_phase = 'DEALER_TURN'

def reveal_dealer():
    st.session_state.game_phase = 'GAME_OVER'
    dealer_score = calculate_score(st.session_state.dealer_hand)
    while dealer_score < 17:
        st.session_state.dealer_hand.append(st.session_state.deck.pop())
        dealer_score = calculate_score(st.session_state.dealer_hand)
    player_score = calculate_score(st.session_state.player_hand)
    multiplier = get_combo_multiplier()

    if dealer_score > 21:
        st.session_state.combo += 1
        st.session_state.msg = f"🎉 딜러 BUST! 플레이어 승리! (수익 {multiplier}배)"
        st.session_state.coins += st.session_state.current_bet + int(st.session_state.current_bet * multiplier)
    elif dealer_score > player_score:
        st.session_state.combo = 0
        st.session_state.msg = f"😢 딜러 승리... (딜러: {dealer_score}점 / 나: {player_score}점)"
    elif dealer_score < player_score:
        st.session_state.combo += 1
        st.session_state.msg = f"🎉 플레이어 승리!! (딜러: {dealer_score}점 / 나: {player_score}점) (수익 {multiplier}배)"
        st.session_state.coins += st.session_state.current_bet + int(st.session_state.current_bet * multiplier)
    else:
        st.session_state.msg = "🤝 무승부! (배팅액을 돌려받습니다)"
        st.session_state.coins += st.session_state.current_bet
    
    save_user_data() # DB 저장

# ==========================================
# 🖥️ 게임 화면 (UI)
# ==========================================
st.markdown("<h1>♣️ JS 블랙잭 카지노 ♠️</h1>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    # --- 로그인 & 리더보드 화면 ---
    st.markdown("<br><h3 style='text-align:center; color:#e0e7ff;'>VIP 라운지 입장</h3>", unsafe_allow_html=True)
    username_input = st.text_input("닉네임을 입력하세요 (데이터가 영구 저장됩니다!)", max_chars=12, placeholder="예: JunSeok99")
    
    if st.button("🚪 카지노 입장하기"):
        if username_input.strip():
            user_data = load_user(username_input.strip())
            st.session_state.username = user_data['username']
            st.session_state.coins = user_data['coins']
            st.session_state.debt = user_data['debt']
            st.session_state.combo = user_data['combo']
            st.session_state.deck = create_deck()
            st.session_state.player_hand = []
            st.session_state.dealer_hand = []
            st.session_state.game_phase = 'BETTING'
            st.session_state.current_bet = 0
            st.session_state.msg = ""
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.warning("닉네임을 입력해야 입장할 수 있습니다!")

    st.divider()
    st.markdown("<h3 style='text-align:center; color:#facc15;'>🏆 카지노 명예의 전당 (Top 5 갑부)</h3>", unsafe_allow_html=True)
    try:
        top_players = supabase.table("casino_players").select("username, coins").order("coins", desc=True).limit(5).execute()
        for idx, player in enumerate(top_players.data):
            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "🏅"
            st.markdown(f"<p style='text-align:center; font-size:1.3rem;'>{medal} <b>{player['username']}</b> : 💰 {player['coins']} 코인</p>", unsafe_allow_html=True)
    except:
        st.markdown("<p style='text-align:center;'>랭킹을 불러오는 중입니다...</p>", unsafe_allow_html=True)

else:
    # --- 메인 게임 화면 ---
    st.markdown(f"<p style='text-align:right; color:#94a3b8;'>👤 플레이어: {st.session_state.username}</p>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a: st.markdown(f'<div class="coin-box">💰 내 지갑: {st.session_state.coins}</div>', unsafe_allow_html=True)
    with col_b:
        if st.session_state.debt > 0: st.markdown(f'<div class="coin-box debt-box">💀 빚: {st.session_state.debt}</div>', unsafe_allow_html=True)
        elif st.session_state.combo >= 2: st.markdown(f'<div class="coin-box combo-box">🔥 {st.session_state.combo} 연승 중!</div>', unsafe_allow_html=True)
        else: st.markdown(f'<div class="coin-box" style="color:#aaa; border-color:#aaa;">🎲 대기 중</div>', unsafe_allow_html=True)

    if st.session_state.game_phase == 'BETTING':
        if st.session_state.coins > 0:
            max_bet = st.session_state.coins
            bet_amount = st.number_input("BET AMOUNT", min_value=10, max_value=max_bet, value=min(100, max_bet), step=10, label_visibility="collapsed")
            st.write("") 
            if st.button("🚀 게임 시작 (DEAL)"): start_game(bet_amount); st.rerun()
                
            if st.session_state.debt > 0 and st.session_state.coins >= 1500:
                st.divider()
                st.markdown('<div class="btn-yellow">', unsafe_allow_html=True)
                if st.button("👼 1500 코인으로 빚 청산하기"):
                    st.session_state.coins -= 1500
                    st.session_state.debt = 0
                    save_user_data()
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("💸 파산하셨습니다... 돈을 빌려야 합니다.")
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("💀 사채업자에게 1000 코인 빌리기 (빚 1500 증가)"):
                st.session_state.coins += 1000
                st.session_state.debt += 1500
                save_user_data()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.game_phase in ['PLAYING', 'DEALER_TURN', 'GAME_OVER']:
        st.markdown("<h3 style='text-align:center; color:#e0e7ff; margin-top:10px;'>🤖 딜러</h3>", unsafe_allow_html=True)
        hide_dealer_card = (st.session_state.game_phase in ['PLAYING', 'DEALER_TURN'])
        st.markdown(render_cards(st.session_state.dealer_hand, hide_second=hide_dealer_card), unsafe_allow_html=True)
        if not hide_dealer_card: st.markdown(f"<p style='text-align:center; color:#94a3b8; margin-top:-10px;'>딜러 점수: {calculate_score(st.session_state.dealer_hand)}점</p>", unsafe_allow_html=True)

        st.divider()

        st.markdown("<h3 style='text-align:center; color:#e0e7ff;'>🙋‍♂️ 플레이어</h3>", unsafe_allow_html=True)
        st.markdown(render_cards(st.session_state.player_hand), unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:#facc15; font-size:1.4rem; margin-top:-10px;'>현재 점수: <b>{calculate_score(st.session_state.player_hand)}점</b> (배팅: {st.session_state.current_bet})</p>", unsafe_allow_html=True)

        if st.session_state.game_phase == 'PLAYING':
            c1, c2, c3 = st.columns(3)
            with c1: 
                if st.button("🃏 HIT"): hit(); st.rerun()
            with c2: 
                if st.button("🛑 STAND"): st.session_state.game_phase = 'DEALER_TURN'; st.rerun()
            with c3:
                if len(st.session_state.player_hand) == 2 and st.session_state.coins >= st.session_state.current_bet:
                    st.markdown('<div class="btn-yellow">', unsafe_allow_html=True)
                    if st.button("🔥 DOUBLE DOWN"): double_down(); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state.game_phase == 'DEALER_TURN':
            st.markdown('<div class="btn-red" style="margin-top:20px;">', unsafe_allow_html=True)
            if st.button("🚨 딜러 카드 오픈 (결과 확인)"): reveal_dealer(); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state.game_phase == 'GAME_OVER':
            st.divider()
            if "승리" in st.session_state.msg or "대박" in st.session_state.msg: st.success(st.session_state.msg)
            elif "무승부" in st.session_state.msg: st.info(st.session_state.msg)
            else: st.error(st.session_state.msg)
                
            if st.button("🔄 다음 판 가기 (NEXT)"):
                st.session_state.game_phase = 'BETTING'
                st.rerun()
