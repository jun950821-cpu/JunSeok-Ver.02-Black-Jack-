import streamlit as st
import random

# --- 🎮 Web Page Configuration ---
st.set_page_config(page_title="Casino Blackjack", page_icon="🃏", layout="centered")

# ==========================================
# 🎨 UI Style Sheet (리얼 카지노 테이블 테마)
# ==========================================
st.markdown("""
    <style>
        @import url('https://cdn.jsdelivr.net/gh/neodgm/neodgm-webfont@1.530/neodgm/style.css');

        /* 카지노 배경 */
        [data-testid="stAppViewContainer"] { 
            background: radial-gradient(circle at 50% 30%, #0f5132 0%, #022c18 80%, #000000 100%) !important; 
        }
        
        /* 전체 글자색 하얀색으로 지정 */
        h1, h2, h3, p, span, div, label { font-family: 'NeoDunggeunmo', sans-serif !important; color: white; }
        
        h1 { color: #facc15 !important; text-align: center !important; text-shadow: 0 4px 6px rgba(0,0,0,0.5); font-size: 3.5rem !important; margin-bottom: 0 !important;}
        
        .coin-box { 
            background-color: rgba(0, 0, 0, 0.6); border: 2px solid #facc15; padding: 15px; 
            border-radius: 10px; text-align: center; color: #facc15; 
            font-size: 1.8rem; box-shadow: 0 4px 10px rgba(0,0,0,0.5); 
            margin: 10px 0; 
        }
        .debt-box { border-color: #f43f5e !important; color: #f43f5e !important; }
        .combo-box { border-color: #34d399 !important; color: #34d399 !important; }

        /* 트럼프 카드 디자인 */
        .real-card { 
            background-color: white !important; border-radius: 8px !important; 
            width: 90px !important; height: 130px !important; margin: 0 8px !important; 
            box-shadow: 2px 5px 15px rgba(0,0,0,0.6) !important; 
            display: inline-block !important; position: relative !important;
            font-family: 'Arial', sans-serif !important; 
        }
        .card-top { 
            position: absolute !important; top: 8px !important; left: 8px !important; 
            font-size: 1.2rem !important; font-weight: bold !important; line-height: 1 !important; text-align: left !important;
        }
        .card-center { 
            position: absolute !important; top: 50% !important; left: 50% !important; 
            transform: translate(-50%, -50%) !important; font-size: 3rem !important;
        }
        
        /* 🚨 카드 안의 텍스트가 하얀색이 되는 것을 막고 강제로 색상 부여 */
        .card-red, .card-red div { color: #dc2626 !important; }
        .card-black, .card-black div { color: #171717 !important; }
        
        .card-hidden { 
            background: repeating-linear-gradient(45deg, #b91c1c, #b91c1c 10px, #7f1d1d 10px, #7f1d1d 20px) !important;
            border: 3px solid white !important; border-radius: 8px !important; 
            width: 90px !important; height: 130px !important; margin: 0 8px !important; 
            box-shadow: 2px 5px 15px rgba(0,0,0,0.6) !important; 
            display: inline-block !important;
        }

        /* 버튼 및 인풋박스 */
        .stButton>button { 
            background-color: rgba(0, 0, 0, 0.7) !important; color: white !important; 
            border: 2px solid #ffffff !important; border-radius: 30px !important; 
            font-size: 1.2rem !important; transition: 0.2s; width: 100%; height: 55px;
        }
        .stButton>button:hover { 
            background-color: white !important; color: #022c18 !important; 
            transform: scale(1.05); box-shadow: 0 0 15px rgba(255,255,255,0.5) !important;
        }
        
        .btn-red>button { border-color: #f43f5e !important; color: #f43f5e !important; }
        .btn-red>button:hover { background-color: #f43f5e !important; color: white !important; box-shadow: 0 0 15px #f43f5e !important;}
        .btn-yellow>button { border-color: #facc15 !important; color: #facc15 !important; }
        .btn-yellow>button:hover { background-color: #facc15 !important; color: black !important; box-shadow: 0 0 15px #facc15 !important;}
        
        .stNumberInput input { 
            background-color: rgba(0,0,0,0.5) !important; color: #facc15 !important; 
            border: 1px solid #facc15 !important; font-size: 1.5rem !important; text-align: center !important; 
        }
    </style>
""", unsafe_allow_html=True)

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
            
        suit = card[0]
        rank = card[1:]
        color_class = "card-red" if suit in ['♥', '♦'] else "card-black"
        
        html += f'<div class="real-card {color_class}"><div class="card-top">{rank}<br>{suit}</div><div class="card-center">{suit}</div></div>'
        
    return f'<div style="text-align:center; margin: 20px 0; display:flex; justify-content:center; flex-wrap:wrap;">{html}</div>'

# ==========================================
# 🧠 세션 상태 (메모리)
# ==========================================
if 'coins' not in st.session_state:
    st.session_state.coins = 1000
    st.session_state.debt = 0       
    st.session_state.combo = 0      
    st.session_state.deck = create_deck()
    st.session_state.player_hand = []
    st.session_state.dealer_hand = []
    st.session_state.game_phase = 'BETTING'
    st.session_state.current_bet = 0
    st.session_state.msg = ""

# ==========================================
# 🎮 게임 로직
# ==========================================
def get_combo_multiplier():
    if st.session_state.combo >= 4: return 2.0
    elif st.session_state.combo >= 3: return 1.5
    return 1.0

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

def hit():
    st.session_state.player_hand.append(st.session_state.deck.pop())
    if calculate_score(st.session_state.player
