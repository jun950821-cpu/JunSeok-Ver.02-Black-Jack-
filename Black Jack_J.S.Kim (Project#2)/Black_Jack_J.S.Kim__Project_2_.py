import streamlit as st
import random
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

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
        .timer-box { border-color: #3b82f6 !important; color: #3b82f6 !important; }
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
        .btn-blue>button { border-color: #3b82f6 !important; color: #3b82f6 !important; }
        .btn-blue>button:hover { background-color: #3b82f6 !important; color: white !important; box-shadow: 0 0 15px #3b82f6 !important;}
        .stNumberInput input { background-color: rgba(0,0,0,0.5) !important; color: #facc15 !important; border: 1px solid #facc15 !important; font-size: 1.5rem !important; text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 💾 데이터베이스 & 시스템 함수
# ==========================================
def load_user(username):
    response = supabase.table("casino_players").select("*").eq("username", username).execute()
    if len(response.data) > 0:
        return response.data[0]
    else:
        new_user = {"username": username, "coins": 1000, "debt": 0, "combo": 0, "last_rescue": None, "loan_count": 0}
        res = supabase.table("casino_players").insert(new_user).execute()
        return res.data[0]

def save_user_data():
    if 'username' in st.session_state:
        supabase.table("casino_players").update({
            "coins": st.session_state.coins,
            "debt": st.session_state.debt,
            "combo": st.session_state.combo,
            "loan_count": st.session_state.loan_count
        }).eq("username", st.session_state.username).execute()

def get_rescue_time_left():
    if not st.session_state.get('last_rescue'): return 0
    last = datetime.fromisoformat(st.session_state.last_rescue)
    now = datetime.now(timezone.utc)
    diff = now - last
    if diff > timedelta(minutes=3): return 0
    return (timedelta(minutes=3) - diff).seconds

def claim_rescue():
    now_iso = datetime.now(timezone.utc).isoformat()
    supabase.table("casino_players").update({
        "coins": 500, "last_rescue": now_iso
    }).eq("username", st.session_state.username).execute()
    st.session_state.coins = 500
    st.session_state.last_rescue = now_iso

def reset_game_completely():
    # 💀 DIE 발생 시 완전히 처음부터 초기화 (대출 횟수도 리셋)
    st.session_state.coins = 1000
    st.session_state.debt = 0
    st.session_state.combo = 0
    st.session_state.loan_count = 0
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
# 🧠 세션 상태 (메모리) 초기화
# ==========================================
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
    st.session_state.player_hands = []
    st.session_state.hand_bets = []
    st.session_state.active_hand = 0

# ==========================================
# 🎮 게임 로직 (스플릿 포함)
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
    st.session_state.player_hands = [
        [c1, st.session_state.deck.pop()],
        [c2, st.session_state.deck.pop()]
    ]

def next_hand_or_dealer():
    st.session_state.active_hand += 1
    if st.session_state.active_hand >= len(st.session_state.player_hands):
        st.session_state.game_phase = 'DEALER_TURN'

def hit():
    idx = st.session_state.active_hand
    st.session_state.player_hands[idx].append(st.session_state.deck.pop())
    if calculate_score(st.session_state.player_hands[idx]) > 21:
        next_hand_or_dealer()

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

    msgs = []
    earned = 0
    combo_won = False

    for i, hand in enumerate(st.session_state.player_hands):
        p_score = calculate_score(hand)
        bet = st.session_state.hand_bets[i]
        prefix = f"[핸드 {i+1}] " if len(st.session_state.player_hands) > 1 else ""

        if p_score > 21:
            msgs.append(f"{prefix}💥 BUST! (21 초과)")
        elif dealer_score > 21:
            msgs.append(f"{prefix}🎉 딜러 BUST! 승리!")
            earned += bet * 2; combo_won = True
        elif p_score > dealer_score:
            msgs.append(f"{prefix}🎉 승리! ({p_score} vs {dealer_score})")
            earned += bet * 2; combo_won = True
        elif p_score < dealer_score:
            msgs.append(f"{prefix}😢 패배... ({p_score} vs {dealer_score})")
        else:
            msgs.append(f"{prefix}🤝 무승부")
            earned += bet

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
            st.session_state.loan_count = user_data.get('loan_count', 0)
            st.session_state.last_rescue = user_data.get('last_rescue')
            st.session_state.deck = create_deck()
            st.session_state.game_phase = 'BETTING'
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
        pass

else:
    # --- 메인 게임 화면 ---
    st.markdown(f"<p style='text-align:right; color:#94a3b8;'>👤 플레이어: {st.session_state.username}</p>", unsafe_allow_html=True)
    
    # 지갑 전광판
    col_a, col_b = st.columns(2)
    with col_a: st.markdown(f'<div class="coin-box">💰 내 지갑: {st.session_state.coins}</div>', unsafe_allow_html=True)
    with col_b:
        if st.session_state.coins <= 0 and st.session_state.debt > 0:
            st.markdown(f'<div class="coin-box debt-box">🚨 DIE 예정</div>', unsafe_allow_html=True)
        elif st.session_state.debt > 0:
            st.markdown(f'<div class="coin-box debt-box">💀 사채 빚: {st.session_state.debt}</div>', unsafe_allow_html=True)
        elif st.session_state.combo >= 2: 
            st.markdown(f'<div class="coin-box combo-box">🔥 {st.session_state.combo} 연승 중!</div>', unsafe_allow_html=True)
        else: 
            st.markdown(f'<div class="coin-box" style="color:#aaa; border-color:#aaa;">🎲 대기 중</div>', unsafe_allow_html=True)

    # 배팅 화면 & 파산 상태 처리
    if st.session_state.game_phase == 'BETTING':
        if st.session_state.coins > 0:
            max_bet = st.session_state.coins
            bet_amount = st.number_input("BET AMOUNT", min_value=10, max_value=max_bet, value=min(100, max_bet), step=10, label_visibility="collapsed")
            st.write("") 
            if st.button("🚀 게임 시작 (DEAL)"): start_game(bet_amount); st.rerun()
                
            if st.session_state.debt > 0 and st.session_state.coins >= st.session_state.debt:
                st.divider()
                st.markdown('<div class="btn-yellow">', unsafe_allow_html=True)
                if st.button(f"👼 사채 {st.session_state.debt} 코인 전액 상환하기"):
                    st.session_state.coins -= st.session_state.debt
                    st.session_state.debt = 0
                    save_user_data()
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            # 🚨 빚이 있는 상태에서 파산했을 경우 -> 💀 DIE 폭탄!
            if st.session_state.debt > 0:
                st.markdown("<h2 style='text-align:center; color:#f43f5e;'>💀 DIE 💀</h2>", unsafe_allow_html=True)
                st.error("사채업자에게 빌린 돈을 갚지 못하고 파산했습니다! 조폭들에게 잡혀가 장기가 털리고 신분 세탁(계정 초기화)을 당합니다.")
                st.write("")
                if st.button("🔄 새로운 신분으로 인생 세탁하기 (강제 초기화)"):
                    reset_game_completely()
                    st.rerun()
            else:
                # 빚이 없는 순수 파산 상태
                time_left = get_rescue_time_left()
                if time_left <= 0:
                    st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
                    if st.button("👼 구제금융 500 코인 받기"): claim_rescue(); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    m, s = divmod(time_left, 60)
                    st.error(f"💸 코인을 모두 잃었습니다! 다음 구제금융까지: {m}분 {s}초")
                    if st.button("🔄 남은 시간 확인"): st.rerun()
                
                st.markdown("<p style='text-align:center; color:#aaa; margin: 15px 0;'>--- OR ---</p>", unsafe_allow_html=True)
                
                # 👿 사채 대출 로직 (3회 제한)
                if st.session_state.loan_count < 3:
                    st.markdown('<div class="btn-red">', unsafe_allow_html=True)
                    if st.button(f"💀 사채 1000 코인 즉시 대출 (남은 기회: {3 - st.session_state.loan_count}번)"):
                        st.session_state.coins = 1000
                        st.session_state.debt = 1500
                        st.session_state.loan_count += 1
                        save_user_data()
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    # 3회 초과 시 강제 DIE 버튼 활성화
                    st.markdown('<div class="btn-red">', unsafe_allow_html=True)
                    if st.button("💀 대출 한도 초과! 억지로 돈 빌리기 (누르면 즉시 DIE)"):
                        reset_game_completely()
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # 플레이 화면
    elif st.session_state.game_phase in ['PLAYING', 'DEALER_TURN', 'GAME_OVER']:
        st.markdown("<h3 style='text-align:center; color:#e0e7ff; margin-top:10px;'>🤖 딜러</h3>", unsafe_allow_html=True)
        hide_dealer_card = (st.session_state.game_phase in ['PLAYING', 'DEALER_TURN'])
        st.markdown(render_cards(st.session_state.dealer_hand, hide_second=hide_dealer_card), unsafe_allow_html=True)
        if not hide_dealer_card: st.markdown(f"<p style='text-align:center; color:#94a3b8; margin-top:-10px;'>딜러 점수: {calculate_score(st.session_state.dealer_hand)}점</p>", unsafe_allow_html=True)
        st.divider()

        # 여러 핸드(스플릿) 표시
        st.markdown("<h3 style='text-align:center; color:#e0e7ff;'>🙋‍♂️ 플레이어</h3>", unsafe_allow_html=True)
        for i, hand in enumerate(st.session_state.player_hands):
            is_active = (i == st.session_state.active_hand and st.session_state.game_phase == 'PLAYING')
            border_style = "border: 2px solid #facc15; border-radius: 15px; padding-bottom: 10px;" if is_active else ""
            
            st.markdown(f"<div style='{border_style}'>", unsafe_allow_html=True)
            if len(st.session_state.player_hands) > 1:
                st.markdown(f"<p style='text-align:center; color:#facc15; font-size:1.2rem;'>--- 핸드 {i+1} ---</p>", unsafe_allow_html=True)
            st.markdown(render_cards(hand), unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; color:#facc15; font-size:1.2rem; margin-top:-10px;'>점수: <b>{calculate_score(hand)}점</b> (배팅: {st.session_state.hand_bets[i]})</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # 액션 버튼
        if st.session_state.game_phase == 'PLAYING':
            idx = st.session_state.active_hand
            hand = st.session_state.player_hands[idx]
            
            can_split = (len(hand) == 2 and len(st.session_state.player_hands) == 1 and 
                         hand[0][1:] == hand[1][1:] and 
                         st.session_state.coins >= st.session_state.hand_bets[0])

            cols = st.columns(4 if can_split else 3)
            with cols[0]:
                if st.button("🃏 HIT", use_container_width=True): hit(); st.rerun()
            with cols[1]:
                if st.button("🛑 STAND", use_container_width=True): next_hand_or_dealer(); st.rerun()
            with cols[2]:
                if len(hand) == 2 and st.session_state.coins >= st.session_state.hand_bets[idx]:
                    st.markdown('<div class="btn-yellow">', unsafe_allow_html=True)
                    if st.button("🔥 DOUBLE", use_container_width=True): double_down(); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            if can_split:
                with cols[3]:
                    st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
                    if st.button("✂️ SPLIT", use_container_width=True): split(); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state.game_phase == 'DEALER_TURN':
            st.markdown('<div class="btn-red" style="margin-top:20px;">', unsafe_allow_html=True)
            if st.button("🚨 딜러 카드 오픈 (결과 확인)"): reveal_dealer(); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state.game_phase == 'GAME_OVER':
            st.divider()
            st.markdown(f"<div style='text-align:center; font-size:1.5rem; background:rgba(0,0,0,0.5); padding:20px; border-radius:10px;'>{st.session_state.msg}</div>", unsafe_allow_html=True)
            st.write("")
            if st.button("🔄 다음 판 가기 (NEXT)"):
                st.session_state.game_phase = 'BETTING'
                st.rerun()
