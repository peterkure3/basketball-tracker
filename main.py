import streamlit as st
import pandas as pd
import sqlite3
import os
import altair as alt

# --- Database Setup ---
conn = sqlite3.connect('basketball_data.db')
cursor = conn.cursor()

# --- Create Tables (if they don't exist) ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS Players (
    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    team_id INTEGER
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Teams (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Games (
    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    team1_id INTEGER,
    team2_id INTEGER
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Stats (
    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER,
    player_id INTEGER,
    points INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    turnovers INTEGER,
    FOREIGN KEY (game_id) REFERENCES Games(game_id),
    FOREIGN KEY (player_id) REFERENCES Players(player_id)
);
""")

conn.commit()


# --- Functions for CRUD Operations ---
def add_player(player_name, team_id):
    cursor.execute("INSERT INTO Players (name, team_id) VALUES (?, ?)",
                   (player_name, team_id))
    conn.commit()


def get_players():
    cursor.execute("SELECT * FROM Players")
    return cursor.fetchall()


def add_team(team_name):
    cursor.execute("INSERT INTO Teams (name) VALUES (?)", (team_name, ))
    conn.commit()


def get_teams():
    cursor.execute("SELECT * FROM Teams")
    return cursor.fetchall()


def add_game(date, team1_id, team2_id):
    cursor.execute(
        "INSERT INTO Games (date, team1_id, team2_id) VALUES (?, ?, ?)",
        (date, team1_id, team2_id))
    conn.commit()


def add_stats(game_id, player_id, points, rebounds, assists, steals, blocks,
              turnovers):
    cursor.execute(
        """
    INSERT INTO Stats (game_id, player_id, points, rebounds, assists, steals, blocks, turnovers) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (game_id, player_id, points, rebounds, assists, steals, blocks,
          turnovers))
    conn.commit()

def delete_stats(stat_id):
    cursor.execute("DELETE FROM Stats WHERE stat_id = ?", (stat_id,))
    conn.commit()

# --- Function to Export Stats to CSV ---
def export_stats_csv():
    cursor.execute("""
    SELECT
        p.name AS Player,
        g.date AS Date,
        t.name AS Team,
        s.points,
        s.rebounds,
        s.assists,
        s.steals,
        s.blocks,
        s.turnovers
    FROM Stats AS s
    JOIN Players AS p ON s.player_id = p.player_id
    JOIN Games AS g ON s.game_id = g.game_id
    LEFT JOIN Teams AS t ON p.team_id = t.team_id
    """)
    stats_data = cursor.fetchall()
    stats_df = pd.DataFrame(stats_data, columns=['Player', 'Date', 'Team', 'Points', 'Rebounds', 'Assists', 'Steals', 'Blocks', 'Turnovers'])
    csv = stats_df.to_csv(index=False)
    return csv


# --- Streamlit App ---
st.title("Basketball Stat Tracker")

# --- Team Management ---
st.header("Team Management")
team_name = st.text_input("Team Name:")
if st.button("Add Team"):
    add_team(team_name)
    st.success("Team Added!")

# --- Player Management ---
st.header("Player Management")

player_name = st.text_input("Player Name:")
team_selected = st.selectbox("Team", [team[1] for team in get_teams()],
                             key="team_select_player")
if st.button("Add Player"):
    # Get team_id from team name
    cursor.execute("SELECT team_id FROM Teams WHERE name = ?",
                   (team_selected, ))
    team_id = cursor.fetchone()
    if team_id:
        team_id = team_id[0]
        add_player(player_name, team_id)
        st.success("Player Added!")
    else:
        st.error("Team not found. Please add the team first.")

# --- Game Data ---
st.header("Game Data")
selected_player = st.selectbox("Select Player",
                               [player[1] for player in get_players()],
                               key="player_select")
# --- Function to get stats for a player ---
def get_player_stats(player_name, date):
    cursor.execute("""
    SELECT 
        s.stat_id, s.points, s.rebounds, s.assists, s.steals, s.blocks, s.turnovers
    FROM Stats AS s
    JOIN Players AS p ON s.player_id = p.player_id
    JOIN Games AS g ON s.game_id = g.game_id
    WHERE p.name = ? AND g.date = ?
    """, (player_name, date))
    stats = cursor.fetchone()
    if stats:
        return stats
    else:
        return (None, 0, 0, 0, 0, 0, 0)  # Return None for stat_id if no stats found


date = st.date_input("Date")
points = st.number_input("Points", min_value=0)
rebounds = st.number_input("Rebounds", min_value=0)
assists = st.number_input("Assists", min_value=0)
steals = st.number_input("Steals", min_value=0)
blocks = st.number_input("Blocks", min_value=0)
turnovers = st.number_input("Turnovers", min_value=0)

if st.button("Add Stats"):
    # Get player_id
    cursor.execute("SELECT player_id FROM Players WHERE name = ?",
                   (selected_player, ))
    player_id = cursor.fetchone()
    if player_id:
        player_id = player_id[0]

        # --- Create a new game if one doesn't exist yet ---
        cursor.execute("SELECT game_id FROM Games WHERE date = ?", (date, ))
        game_id = cursor.fetchone()
        if game_id:
            game_id = game_id[0]
        else:
            # --- Add a new game
            cursor.execute("INSERT INTO Games (date) VALUES (?)", (date, ))
            conn.commit()
            cursor.execute("SELECT game_id FROM Games WHERE date = ?",
                           (date, ))
            game_id = cursor.fetchone()[0]  # Get the newly created game_id

        add_stats(game_id, player_id, points, rebounds, assists, steals,
                  blocks, turnovers)
        st.success("Stats Added!")
    else:
        st.error("Player not found.")

# --- Display Stats Table ---
st.header("Game Stats")
cursor.execute("""
SELECT
    p.name AS Player,
    g.date AS Date,
    t.name AS Team,
    s.points,
    s.rebounds,
    s.assists,
    s.steals,
    s.blocks,
    s.turnovers,
    s.stat_id
FROM Stats AS s
JOIN Players AS p ON s.player_id = p.player_id
JOIN Games AS g ON s.game_id = g.game_id
LEFT JOIN Teams AS t ON p.team_id = t.team_id
""")
stats_data = cursor.fetchall()
stats_df = pd.DataFrame(stats_data,
                        columns=[
                            'Player', 'Date', 'Team', 'Points', 'Rebounds',
                            'Assists', 'Steals', 'Blocks', 'Turnovers',
                            'stat_id'
                        ])
st.dataframe(stats_df)

# --- Data Visualisation ---
st.header("Visualization")
stats_df['Date'] = pd.to_datetime(
    stats_df['Date'])  # Convert to datetime objects for better plotting

# --- Melt the DataFrame for easier visualization
stats_df_melted = stats_df.melt(id_vars=['Player', 'Date', 'Team', 'stat_id'],
                                value_vars=[
                                    'Points', 'Rebounds', 'Assists', 'Steals',
                                    'Blocks', 'Turnovers'
                                ],
                                var_name='Stat',
                                value_name='Value')

# --- Get unique players
players = stats_df_melted['Player'].unique()

# --- Create separate charts for each player with colors
color_map = {}
if len(players) > 0:
    color_map = {
        players[0]: 'skyblue',
        # Add more colors for additional players as needed
    }
    if len(players) > 1:
        color_map[players[1]] = 'green'

# --- Create separate charts for each player
for player in players:
    st.subheader(player)
    player_df = stats_df_melted[stats_df_melted['Player'] == player]
    chart = alt.Chart(player_df).mark_bar().encode(
        x='Stat',
        y='Value',
        color=alt.Color(
            'Player', scale=alt.Scale(range=list(
                color_map.values())))  # Assign colors based on Player
    )
    st.altair_chart(chart, use_container_width=True)

# --- Display Total Stats Table
st.header("Total Stats")
st.dataframe(
    stats_df.groupby('Player')[[
        'Points', 'Rebounds', 'Assists', 'Steals', 'Blocks', 'Turnovers'
    ]].sum())

# --- Leaderboard ---
st.header("Leaderboard")

leaderboard_stat = st.selectbox("Select Stat for Leaderboard", ['Points', 'Rebounds', 'Assists', 'Steals', 'Blocks', 'Turnovers'])

cursor.execute(f"""
SELECT 
    p.name AS Player, 
    SUM(s.{leaderboard_stat.lower()}) AS Total_{leaderboard_stat}
FROM Stats AS s
JOIN Players AS p ON s.player_id = p.player_id
GROUP BY Player
ORDER BY Total_{leaderboard_stat} DESC
""")
leaderboard_data = cursor.fetchall()
leaderboard_df = pd.DataFrame(leaderboard_data, columns=['Player', f'Total {leaderboard_stat}'])
st.dataframe(leaderboard_df)

# --- Delete Stats ---
st.header("Delete Stats")
selected_stat_id = st.number_input("Enter Stat ID to Delete:", min_value=1)
if st.button("Delete Stat"):
    delete_stats(selected_stat_id)
    st.success("Stat Deleted!")

# --- Export Stats ---
if st.button("Export Stats (CSV)"):
    csv = export_stats_csv()
    st.download_button(label="Download CSV",
                       data=csv,
                       file_name="basketball_stats.csv",
                       mime="text/csv")

# --- Close Database Connection ---
conn.close()
