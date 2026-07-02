import streamlit as st
import pandas as pd

# Set up page config for mobile views
st.set_page_config(page_title="Race Tournament Leaderboard", layout="wide")

st.title("🏆 Race Tournament Dashboard")
st.caption("Web-based tracker — Safe from background app crashes")

# --- Helper Functions ---
def clean_and_split(text):
    cleaned = text.replace(',', ' ').replace('.', ' ').replace('/', ' ')
    return cleaned.split()

# Initialize background memory states inside the web browser
if 'competitors' not in st.session_state:
    st.session_state.competitors = {}
if 'races_schedule' not in st.session_state:
    st.session_state.races_schedule = []
if 'history_submitted' not in st.session_state:
    st.session_state.history_submitted = False
if 'results_log' not in st.session_state:
    st.session_state.results_log = {}

# --- STEP 1: Paste Competitor Tips ---
st.header("Step 1: Paste Competitor Tips")
raw_tips = st.text_area(
    "Paste all your lines below at the same time:", 
    height=200, 
    placeholder="Mope 3 4 3 10...\nTissot 4 10 3 4..."
)

if st.button("Load Competitors", type="primary"):
    new_competitors = {}
    lines = raw_tips.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            name = parts[0]
            if name.replace(',','').replace('.','').replace('/','').isdigit():
                continue
            selections = clean_and_split(parts[1])
            new_competitors[name] = {'selections': selections, 'score': 0}
            
    if new_competitors:
        st.session_state.competitors = new_competitors
        st.success(f"Successfully loaded {len(new_competitors)} competitors!")
    else:
        st.error("No valid competitors found. Check your text format.")

if st.session_state.competitors:
    # --- STEP 2: Venue Configuration ---
    st.header("Step 2: Venue Configuration")
    num_venues = st.radio("How many venues tonight?", [1, 2], horizontal=True)
    
    schedule = []
    if num_venues == 2:
        col1, col2 = st.columns(2)
        with col1:
            v1_name = st.text_input("Venue 1 Name:", "Flemington")
            v1_count = st.number_input(f"Races at {v1_name}:", min_value=1, max_value=20, value=8)
        with col2:
            v2_name = st.text_input("Venue 2 Name:", "Randwick")
            v2_count = st.number_input(f"Races at {v2_name}:", min_value=1, max_value=20, value=7)
            
        max_races = max(v1_count, v2_count)
        for i in range(1, max_races + 1):
            if i <= v1_count: schedule.append((v1_name, i))
            if i <= v2_count: schedule.append((v2_name, i))
    else:
        v_name = st.text_input("Venue Name:", "Local")
        start_race = st.number_input("Starting race number:", min_value=1, value=1)
        total_races = st.number_input("How many total races?", min_value=1, value=8)
        for i in range(total_races):
            schedule.append((v_name, start_race + i))
            
    st.session_state.races_schedule = schedule

    # --- STEP 3: Live Race Entry Dashboard ---
    st.header("Step 3: Score Live Races")
    st.info("Input results below. The table recalculates automatically and won't vanish if you lock your phone.")
    
    POINTS = {'1st': 5, '2nd': 3, '3rd': 2}
    
    # Reset base scores before recalculation
    for name in st.session_state.competitors:
        st.session_state.competitors[name]['score'] = 0

    # Build input layout dynamically for every race in the schedule
    for idx, (venue, r_num) in enumerate(st.session_state.races_schedule):
        key_id = f"results_{venue}_{r_num}_{idx}"
        
        # Display current tip matrix inline
        tips_list = []
        for c_name, c_data in st.session_state.competitors.items():
            tip = c_data['selections'][idx] if idx < len(c_data['selections']) else "None"
            tips_list.append(f"{c_name}: #{tip}")
            
        with st.expander(f"🏁 {venue.upper()} - RACE {r_num} (View Tips / Enter Winners)"):
            st.caption(", ".join(tips_list))
            res_in = st.text_input(f"Enter 1st, 2nd, 3rd place for {venue} Race {r_num}:", key=key_id, placeholder="e.g. 3 7 10")
            
            parsed_res = clean_and_split(res_in)
            if len(parsed_res) >= 1:
                st.session_state.results_log[idx] = parsed_res

    # Calculate global runtime scores dynamically from what the user filled out
    max_completed_index = -1
    for idx, results in st.session_state.results_log.items():
        if not results: continue
        max_completed_index = max(max_completed_index, idx)
        
        first = results[0] if len(results) > 0 else ""
        second = results[1] if len(results) > 1 else ""
        third = results[2] if len(results) > 2 else ""
        
        for name, data in st.session_state.competitors.items():
            if idx < len(data['selections']):
                user_tip = data['selections'][idx]
                if user_tip == first: data['score'] += POINTS['1st']
                elif user_tip == second: data['score'] += POINTS['2nd']
                elif user_tip == third: data['score'] += POINTS['3rd']

    # --- STEP 4: Live Rendered Leaderboard ---
    st.header("📊 Live Standings Table")
    
    total_total_races = len(st.session_state.races_schedule)
    remaining_races = total_total_races - (max_completed_index + 1)
    
    leaderboard_data = []
    sorted_comps = sorted(st.session_state.competitors.items(), key=lambda x: x[1]['score'], reverse=True)
    
    for rank, (target_name, target_data) in enumerate(sorted_comps, start=1):
        sim_scores = {name: data['score'] for name, data in st.session_state.competitors.items()}
        
        for r_idx in range(max_completed_index + 1, total_total_races):
            if r_idx < len(target_data['selections']):
                target_winning_tip = target_data['selections'][r_idx]
                for name, data in st.session_state.competitors.items():
                    if r_idx < len(data['selections']) and data['selections'][r_idx] == target_winning_tip:
                        sim_scores[name] += 5
                        
        target_max_score = sim_scores[target_name]
        highest_opp = max(sim_scores[name] for name in sim_scores if name != target_name) if len(sim_scores) > 1 else target_max_score
        status = "LOCK" if target_max_score < highest_opp else "CHANCE"
        
        leaderboard_data.append({
            "Rank": rank,
            "Competitor": target_name,
            "Current Points": target_data['score'],
            "Max Potential": target_max_score,
            "Status": status
        })
        
    if leaderboard_data:
        df = pd.DataFrame(leaderboard_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.write(f"ℹ️ *{remaining_races} races left to score across all tracks.*")
        
    if st.button("Wipe & Clear Tournament Data"):
        st.session_state.clear()
        st.rerun()
