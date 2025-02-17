import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Calculates how many pa and bf every player had per year
def compute_player_pa_and_bf(df_players, at_bat_ids, df_savant):

    # Count total plate appearances for each batter per year
    pa_counts = at_bat_ids.groupby(['batter', 'year'])['at_bat_id'].nunique().reset_index(name='total_pa')
    df_players = df_players.merge(pa_counts, left_on=['player_mlb_id', 'year'], right_on=['batter', 'year'], how='left').drop(columns='batter')
    df_players['total_pa'] = df_players['total_pa'].fillna(0).astype(int)

    # Count total batters faced for each pitcher per year
    bf_counts = at_bat_ids.groupby(['pitcher', 'year'])['at_bat_id'].nunique().reset_index(name='total_bf')
    df_players = df_players.merge(bf_counts, left_on=['player_mlb_id', 'year'], right_on=['pitcher', 'year'], how='left').drop(columns='pitcher')
    df_players['total_bf'] = df_players['total_bf'].fillna(0).astype(int)
    
    # Define basepath outs that result in an out
    basepath_outs = [
        'caught_stealing_3b', 'caught_stealing_2b', 'pickoff_caught_stealing_2b', 'pickoff_2b',
        'pickoff_caught_stealing_3b', 'pickoff_1b', 'caught_stealing_home', 'pickoff_3b', 'pickoff_caught_stealing_home'
    ]

    # Filter for basepath events that ended an inning (2 outs when the event occurred)
    df_basepath_ends_inning = df_savant[(df_savant['outs_when_up'] == 2) & (df_savant['events'].isin(basepath_outs))]
    count_basepath_ended_ab = df_basepath_ends_inning.groupby(['batter', 'year'])['at_bat_id'].nunique().reset_index(name='base_ended_inn')

    # Merge basepath-ended inning counts and adjust plate appearances
    df_players = df_players.merge(count_basepath_ended_ab, left_on=['player_mlb_id', 'year'], right_on=['batter', 'year'], how='left').drop(columns='batter')
    df_players['base_ended_inn'] = df_players['base_ended_inn'].fillna(0).astype(int)
    df_players['total_pa'] = df_players['total_pa'] - df_players['base_ended_inn']

    return df_players

#counts how many times a player played at every fielding position
def get_fielding_counts(df_players, df_savant):
    #get the fielders for every at bat
    df_savant_fielding = df_savant[['at_bat_id','year','pitcher_1',
        'fielder_2_1', 'fielder_3', 'fielder_4', 'fielder_5', 'fielder_6',
        'fielder_7', 'fielder_8', 'fielder_9']].drop_duplicates()

    #list of each position column name
    fielding_columns = ['pitcher_1', 'fielder_2_1', 'fielder_3', 
                        'fielder_4', 'fielder_5', 'fielder_6',
                        'fielder_7', 'fielder_8', 'fielder_9']
    
    #dictionary to change position column to more recognizable name
    fielding_dict = {'pitcher_1':'p', 'fielder_2_1':'c', 'fielder_3':'1b', 
                     'fielder_4':'2b', 'fielder_5':'3b', 'fielder_6':'ss',
                     'fielder_7':'lf', 'fielder_8':'cf', 'fielder_9':'rf'}
    
    #get count for every player at every position
    for col in fielding_columns:
        col_name = 'field_' + fielding_dict[col]
        count_df = df_savant_fielding.groupby([col, 'year']).size().reset_index(name=col_name)
        
        #add count to main dataframe
        df_players = df_players.merge(count_df, how='left', left_on=['player_mlb_id', 'year'], right_on=[col, 'year']).drop(columns=col)
        
        #fill NaN with 0
        df_players[col_name] = df_players[col_name].fillna(0).astype(int)

    return df_players

#calculate the percent of pitching appearances that were as a starter vs as a reliever
def add_sp_percentage(df_players, df_savant):
    grouped_df = df_savant.groupby(['pitcher', 'game_pk'])['role_key'].first().reset_index()

    sp_count = grouped_df.groupby('pitcher')['role_key'].apply(lambda x: (x == 'SP').sum())
    total_count = grouped_df.groupby('pitcher')['role_key'].count()
    sp_percentage = (sp_count / total_count) * 100

    df_players = df_players.merge(sp_percentage.rename('sp_pct'), left_on='player_mlb_id', right_index=True, how='left')

    #categorize pitchers
    df_players['starter'] = (df_players['sp_pct'] > 75).astype(int)
    df_players['reliever'] = (df_players['sp_pct'] < 25).astype(int)
    df_players['both_starter_reliever'] = ((df_players['sp_pct'] > 25) & (df_players['sp_pct'] < 75)).astype(int)
                                                                       
    return df_players

#average how many batters a picther faced in an outing
def calculate_batters_faced_in_game(df_players,df_savant):
    df_bf_per_app = df_savant.groupby(['pitcher', 'year','at_bat_id'])['pitcher_at_bat_number'].max().reset_index().groupby(['pitcher', 'year'])['pitcher_at_bat_number'].mean().reset_index(name='avg_bf_per_outing')
    df_players = df_players.merge(df_bf_per_app, how='left', left_on=['player_mlb_id', 'year'], right_on=['pitcher', 'year']).drop(columns='pitcher')
    
    return df_players

#calculate a player's expected batting average using speedangle on a season
def calculate_average_exp_ba(df_players,df_savant,player_type):
    df_savant_exp_ba = df_savant[df_savant['estimated_ba_using_speedangle'].notna()]
    df_savant_avg = df_savant_exp_ba.groupby([player_type,'year'])['estimated_ba_using_speedangle'].mean().reset_index(name=f'{player_type}_avg_exp_ba')
    df_players = df_players.merge(df_savant_avg, how='left', left_on=['player_mlb_id', 'year'], right_on=[player_type, 'year']).drop(columns=player_type)
    return df_players

#get the player's average lineup position on the year
def calculate_lineup_position(df_players, df_savant):
    # Find the first plate appearance of each batter per game
    first_pa = df_savant.groupby(['game_pk', 'batter', 'year', 'inning_topbot'])['at_bat_number'].min().reset_index()
    
    # Assign lineup positions based on order of first at-bat, separately for top (away) and bottom (home) halves
    first_pa['lineup_position'] = first_pa.groupby(['game_pk', 'year', 'inning_topbot'])['at_bat_number'].rank(method='first').astype(int)
    
    # Compute the average lineup position for each batter across the season
    average_lineup_position = first_pa.groupby(['batter','year'])['lineup_position'].mean().reset_index()
    average_lineup_position.rename(columns={'lineup_position': 'avg_lineup_position'}, inplace=True)

    #merge with df_players
    df_players = df_players.merge(average_lineup_position, left_on=['player_mlb_id', 'year'], right_on=['batter', 'year'], how='left').drop(columns='batter')

    return df_players

#calculate rbis on a season
def calculate_rbis(df_players, df_savant):
    rbis_list = df_savant.groupby(['batter','year'])['runs_on_play'].sum().reset_index(name='total_runs')
    #need to account for baserunning steals

    df_players = df_players.merge(rbis_list, left_on=['player_mlb_id', 'year'], right_on=['batter', 'year'], how='left').drop(columns='batter')

    return df_players

#count the number of occurrences of a specific baseball event for each player in a given year and add it as a column
def get_count_for_play_event(df_player, df_sav, col_name, event, player_type):
    #filter to specified event
    df_filter = df_sav[df_sav[col_name] == event]

    #get event count for every batter/year combo
    col_name = player_type + '_' + event
    count_df = df_filter.groupby([player_type, 'year']).size().reset_index(name=col_name)

    #add column to main dataframe
    df_player = df_player.merge(count_df, how='left', left_on=['player_mlb_id', 'year'], right_on=[player_type, 'year']).drop(columns=player_type)
    df_player[col_name] = df_player[col_name].fillna(0).astype(int)

    return df_player

#get columns for number of savant events occurrences for batters and pitchers
def calculate_all_play_event_counts(df_players,df_savant):
    """
    Calculates the count of various baseball play events for each player, 
    both as a batter and as a pitcher, and adds these counts to the player DataFrame.

    This function iterates over a predefined list of play events, computes the number 
    of times each event occurred for every player per season, and appends these counts 
    to df_players. Counts are calculated separately for when the player is batting and pitching.

    Parameters:
    -----------
    df_players : pandas.DataFrame
        DataFrame containing player information, including player IDs and years.
    df_savant : pandas.DataFrame
        Baseball Savant dataset containing detailed event data for each play.

    Returns:
    --------
    pandas.DataFrame
        Updated df_players with additional columns for each play event. 
        Columns follow the format:
        - 'batter_<event>': Count of event occurrences when the player is batting.
        - 'pitcher_<event>': Count of event occurrences when the player is pitching.
    """
    
    #list of all non NaN df_savant events
    play_events = ['strikeout', 'caught_stealing_3b', 'field_out', 'walk',
           'force_out', 'sac_fly', 'single', 'hit_by_pitch', 'double',
           'grounded_into_double_play', 'sac_bunt', 'home_run',
           'fielders_choice', 'field_error', 'other_out',
           'caught_stealing_2b', 'triple', 'strikeout_double_play',
           'fielders_choice_out', 'double_play', 'sac_fly_double_play',
           'catcher_interf', 'pickoff_caught_stealing_2b', 'pickoff_2b',
           'pickoff_caught_stealing_3b', 'triple_play', 'pickoff_1b',
           'sac_bunt_double_play', 'wild_pitch', 'game_advisory',
           'caught_stealing_home', 'pickoff_3b', 'stolen_base_2b',
           'passed_ball', 'pickoff_caught_stealing_home', 'pickoff_error_3b',
           'stolen_base_3b']    
    
    #get the counts per season for every player
    for event in play_events:
        #calculate the count when player batting
        df_players = get_count_for_play_event(df_players, df_savant, 'events', event, 'batter')
        #calculate the count when player pitching
        df_players = get_count_for_play_event(df_players, df_savant, 'events', event, 'pitcher')

    #get the counts for hit ball types
    types_of_contact = ['line_drive', 'fly_ball', 'ground_ball', 'popup']
    
    for contact in types_of_contact:
        #calculate the count when player batting
        df_players = get_count_for_play_event(df_players, df_savant, 'bb_type', contact, 'batter')
        #calculate the count when player pitching
        df_players = get_count_for_play_event(df_players, df_savant, 'bb_type', contact, 'pitcher') 
    
    return df_players

#generate basic batting stats
def calculate_batting_stats(df_players, df_savant):
    # Hits
    df_players['hits'] = df_players['batter_single'] + df_players['batter_double'] + df_players['batter_triple'] + df_players['batter_home_run']
    
    # Eligible plate appearances
    df_players['elig_pa'] = df_players['total_pa'] - df_players['batter_sac_fly'] - df_players['batter_sac_bunt'] - df_players['batter_walk'] - df_players['batter_catcher_interf']
    
    # Batting Average (AVG)
    df_players['avg'] = df_players['hits'] / df_players['elig_pa']
    
    # Total Bases (TB)
    df_players['tb'] = df_players['batter_single'] + 2 * df_players['batter_double'] + 3 * df_players['batter_triple'] + 4 * df_players['batter_home_run']
    
    # Slugging Percentage (SLG)
    df_players['slg'] = df_players['tb'] / df_players['elig_pa']
    
    # On-Base Percentage (OBP)
    df_players['obp'] = (df_players['hits'] + df_players['batter_walk'] + df_players['batter_hit_by_pitch']) / (df_players['elig_pa'] + df_players['batter_walk'] + df_players['batter_hit_by_pitch'])
                                                                                                                
    # On-Base Plus Slugging (OPS)
    df_players['ops'] = df_players['obp'] + df_players['slg']

    #calculate type of hit rates
    df_players = hit_ball_type_rates(df_players, df_savant,'batter')
    df_players = hit_ball_type_rates(df_players, df_savant,'pitcher')

    #get ball/strike/inplay ratios
    df_players = strike_ball_inplay_counts(df_players, df_savant, 'batter')
    df_players = strike_ball_inplay_counts(df_players, df_savant, 'pitcher')
    
    # Batting Average on Balls in Play (BABIP)
    df_players['babip_batter'] = (
        df_players['hits'] - df_players['batter_home_run']
    ) / (
        df_players['batter_inplay'] - df_players['batter_home_run']
    )
    
    # Strikeout Rate (K%)
    df_players['k_rate_batter'] = df_players['batter_strikeout'] / df_players['total_pa']
    
    # Walk Rate (BB%)
    df_players['bb_rate_batter'] = df_players['batter_walk'] / df_players['total_pa']
    
    # Home Run Rate (HR%)
    df_players['hr_rate'] = df_players['batter_home_run'] / df_players['total_pa']

    # Total Stolen Bases
    df_players['stolen_bases'] = df_players['batter_stolen_base_2b'] + df_players['batter_stolen_base_3b']
    
    # Isolated Power (ISO)
    df_players['iso'] = df_players['slg'] - df_players['avg']
    
    # Extra Base Hits (XBH)
    df_players['xbh'] = df_players['batter_double'] + df_players['batter_triple'] + df_players['batter_home_run']
    
    # Runs Created (RC) - simplified
    df_players['rc'] = (df_players['hits'] + df_players['batter_walk']) * df_players['tb'] / df_players['total_pa']
    
    # Defensive Versatility (Number of Positions Played)
    df_players['positions_played'] = df_players[['field_p', 'field_c', 'field_1b', 'field_2b', 'field_3b', 
                                                 'field_ss', 'field_lf', 'field_cf', 'field_rf']].gt(0).sum(axis=1)

    # Strikeout-to-Walk Ratio (K/BB)
    df_players['k_bb_ratio_batter'] = df_players['batter_strikeout'] / df_players['batter_walk']

    return df_players

#calculate basic pitching stats
def calculate_pitching_stats(df_players):
    """
    Computes key pitching statistics for each player based on event counts from play-by-play data.

    This function calculates various advanced and traditional pitching metrics using player-level 
    event data, adding them as new columns to the df_players DataFrame.

    Parameters:
    -----------
    df_players : pandas.DataFrame
        DataFrame containing pitcher event counts, including batters faced, strikeouts, walks, 
        and various pitching outcomes.

    Returns:
    --------
    pandas.DataFrame
        Updated df_players with additional columns for pitching statistics.
    """

    # Hits allowed (singles, doubles, triples, home runs)
    df_players['pitcher_hits_allowed'] = (df_players['pitcher_single'] + 
                                          df_players['pitcher_double'] + 
                                          df_players['pitcher_triple'] + 
                                          df_players['pitcher_home_run'])

    # Walks and Hits per Inning Pitched (WHIP) - using batters faced as a proxy for innings
    df_players['whip'] = (df_players['pitcher_walk'] + df_players['pitcher_hits_allowed']) / df_players['innings_pitched']

    # Strikeouts per Batter Faced (K%)
    df_players['k_rate_pitcher'] = df_players['pitcher_strikeout'] / df_players['total_bf']

    # Walk Rate (BB%)
    df_players['bb_rate_pitcher'] = df_players['pitcher_walk'] / df_players['total_bf']

    # Batting Average on Balls in Play (BABIP)
    df_players['babip_pitcher'] = (
        df_players['pitcher_hits_allowed'] - df_players['pitcher_home_run']
    ) / (
        df_players['pitcher_inplay'] - df_players['pitcher_home_run']
    )

    # Home Run Rate (HR%)
    df_players['hr_rate'] = df_players['pitcher_home_run'] / df_players['total_bf']

    # Batting Average Against (BAA)
    df_players['baa'] = df_players['pitcher_hits_allowed'] / df_players['total_bf']

    # Strikeout-to-Walk Ratio (K/BB)
    df_players['k_bb_ratio_pitcher'] = df_players['pitcher_strikeout'] / df_players['pitcher_walk']

    return df_players

#calculate in_zone or batter chased % for pitchers
def calculate_zone_chase_pct(df_players, df_savant):
    # Create a copy to avoid modifying original df_savant
    df_savant_copy = df_savant.copy()

    # Determine if a pitch is in the strike zone
    df_savant_copy['in_zone'] = df_savant_copy['zone'] < 10

    # Determine if a pitch outside the zone was chased (swung at and a strike)
    df_savant_copy['chase'] = (~df_savant_copy['in_zone']) & (df_savant_copy['type'] == 'S')

    # Combine in-zone and chase events (logical OR)
    df_savant_copy['in_zone_chase'] = df_savant_copy['in_zone'] | df_savant_copy['chase']

    # Compute the in-zone + chase rate per pitcher per year
    inzone_chase_rate = df_savant_copy.groupby(['year', 'pitcher'])['in_zone_chase'].mean().reset_index()
    
    # Merge with df_players
    df_players = df_players.merge(inzone_chase_rate.rename(columns={'in_zone_chase': 'zone_chase_pct'}), 
                                  left_on=['player_mlb_id', 'year'], 
                                  right_on=['pitcher', 'year'], 
                                  how='left')

    # Drop 'pitcher' column if it exists after merge
    if 'pitcher' in df_players.columns:
        df_players.drop(columns='pitcher', inplace=True)

    return df_players

#get average fastball velocity for pitchers
def fastball_velocity(df_players, df_savant):
    fastballs = ['FF', 'FC', 'FT']
    
    # Filter for fastballs
    df_savant_fb = df_savant[df_savant['pitch_type'].isin(fastballs)]    
    
    # Compute average fastball velocity per pitcher per year
    avg_fb_vel = df_savant_fb.groupby(['pitcher', 'year'])['release_speed'].mean().reset_index()
    avg_fb_vel.rename(columns={'release_speed': 'avg_fb_vel'}, inplace=True)

    # Merge with df_players and drop redundant 'pitcher' column
    df_players = df_players.merge(avg_fb_vel, left_on=['player_mlb_id', 'year'], right_on=['pitcher', 'year'], how='left').drop(columns='pitcher')

    return df_players

#this code is likely not accurate, but closest I could get

#calculate ip/outs recorded
def calculate_innings_pitched(df_players, df_savant):
    
    out_events = {"strikeout", "field_out", "force_out", "double_play", "triple_play", 
                  "grounded_into_double_play", "sac_bunt", "strikeout_double_play", 
                  "sac_bunt_double_play", "other_out"}
    
    # Vectorized calculation for outs recorded
    df_savant['outs_recorded'] = df_savant['events'].isin(out_events).astype(int)

    # Groupby pitcher and year
    pitcher_stats = df_savant.groupby(['pitcher', 'year'])['outs_recorded'].sum().reset_index()

    # Convert outs to innings pitched
    pitcher_stats['innings_pitched'] = pitcher_stats['outs_recorded'] / 3

    # Merge the calculated stats into df_players
    df_players = df_players.merge(
        pitcher_stats, 
        left_on=['player_mlb_id', 'year'], 
        right_on=['pitcher', 'year'], 
        how='left'
    ).drop(columns='pitcher')

    # Fill NaN values for pitchers who didn't pitch
    df_players[['outs_recorded', 'innings_pitched']] = df_players[['outs_recorded', 'innings_pitched']].fillna(0)

    return df_players


#find percentages of pitches that were strikes/balls/hit into play
def strike_ball_inplay_counts(df_players, df_savant, player_type):
    strike_counts = df_savant[df_savant['type'] == 'S'].groupby([player_type, 'year'])['type'].count().reset_index(name=f'{player_type}_strikes')
    ball_counts = df_savant[df_savant['type'] == 'B'].groupby([player_type, 'year'])['type'].count().reset_index(name=f'{player_type}_balls')
    inplay_counts = df_savant[df_savant['type'] == 'X'].groupby([player_type, 'year'])['type'].count().reset_index(name=f'{player_type}_inplay')
    total_pitch_counts = df_savant.groupby([player_type, 'year'])['type'].count().reset_index(name=f'{player_type}_total_pitches')

    #add counts to dataframe
    df_players = df_players.merge(strike_counts, left_on=['player_mlb_id', 'year'], right_on=[player_type, 'year'], how='left').drop(columns=player_type)
    df_players = df_players.merge(ball_counts, left_on=['player_mlb_id', 'year'], right_on=[player_type, 'year'], how='left').drop(columns=player_type)
    df_players = df_players.merge(inplay_counts, left_on=['player_mlb_id', 'year'], right_on=[player_type, 'year'], how='left').drop(columns=player_type)
    df_players = df_players.merge(total_pitch_counts, left_on=['player_mlb_id', 'year'], right_on=[player_type, 'year'], how='left').drop(columns=player_type)

    #get ratios
    df_players[f'strike_ratio_{player_type}'] = df_players[f'{player_type}_strikes'] / df_players[f'{player_type}_total_pitches']
    df_players[f'ball_ratio_{player_type}'] = df_players[f'{player_type}_balls'] / df_players[f'{player_type}_total_pitches']
    df_players[f'inplay_ratio_{player_type}'] = df_players[f'{player_type}_inplay'] / df_players[f'{player_type}_total_pitches']

    return df_players

# Get percentages for rates of different contact types
def hit_ball_type_rates(df_players, df_savant, player_type):
    ground_ball_counts = df_savant[df_savant['bb_type'] == 'ground_ball'].groupby([player_type,'year'])['type'].count().reset_index(name=f'{player_type}_ground_balls')
    fly_ball_counts = df_savant[df_savant['bb_type'] == 'fly_ball'].groupby([player_type,'year'])['type'].count().reset_index(name=f'{player_type}_fly_balls')
    line_drive_counts = df_savant[df_savant['bb_type'] == 'line_drive'].groupby([player_type,'year'])['type'].count().reset_index(name=f'{player_type}_line_drives')
    popup_counts = df_savant[df_savant['bb_type'] == 'popup'].groupby([player_type,'year'])['type'].count().reset_index(name=f'{player_type}_popups')
    
    # Aggregate counts for each batted ball type
    df_players = df_players.merge(ground_ball_counts, left_on=['player_mlb_id', 'year'], right_on=[player_type, 'year'], how='left').drop(columns=player_type)
    df_players = df_players.merge(fly_ball_counts, left_on=['player_mlb_id', 'year'], right_on=[player_type, 'year'], how='left').drop(columns=player_type)
    df_players = df_players.merge(line_drive_counts, left_on=['player_mlb_id', 'year'], right_on=[player_type, 'year'], how='left').drop(columns=player_type)
    df_players = df_players.merge(popup_counts, left_on=['player_mlb_id', 'year'], right_on=[player_type, 'year'], how='left').drop(columns=player_type)

    ball_types = ['fly_balls', 'ground_balls', 'line_drives', 'popups']
    # Compute ratios
    for ball_type in ball_types:
        df_players[f'{ball_type}_ratio_{player_type}'] = df_players[f'{player_type}_{ball_type}'] / df_players['elig_pa']

    df_players[f'gb_fb_ratio_{player_type}'] = df_players[f'{player_type}_ground_ball'] / df_players[f'{player_type}_fly_ball']    
    df_players[f'hr_fb_pct_{player_type}'] = df_players[f'{player_type}_home_run'] / df_players[f'{player_type}_fly_ball']
    
    return df_players

#calculate a player's expected woba on a season
def calculate_average_xwoba(df_players,df_savant,player_type):
    df_savant_xwoba = df_savant[df_savant['estimated_woba_using_speedangle'].notna()]
    df_savant_avg = df_savant_xwoba.groupby([player_type,'year'])['estimated_woba_using_speedangle'].mean().reset_index(name=f'{player_type}_avg_xwoba')
    df_players = df_players.merge(df_savant_avg, how='left', left_on=['player_mlb_id', 'year'], right_on=[player_type, 'year']).drop(columns=player_type)
    return df_players

def calculate_woba(df_players, df_savant, player_type):
    df_woba = df_savant[df_savant['woba_denom'] == 1]
    df_woba_avg = df_woba.groupby([player_type,'year'])['woba_value'].mean().reset_index(name=f'{player_type}_avg_woba')
    df_players = df_players.merge(df_woba_avg, how='left', left_on=['player_mlb_id', 'year'], right_on=[player_type, 'year']).drop(columns=player_type)
    return df_players

#calculate a player's primary position
def primary_position(df_players):
    field_counts = ['field_p', 'field_c', 'field_1b', 'field_2b', 'field_3b', 'field_ss', 'field_lf', 'field_cf', 'field_rf']
    df_field = df_players.groupby('player_mlb_id')[field_counts].sum().reset_index()
    df_field['primary_position'] = df_field[field_counts].apply(lambda row: row.idxmax().replace('field_', '') if row.max() > 0 else 'Unknown', axis=1)
    df_field = df_field[['player_mlb_id','primary_position']]
    
    df_players = df_players.merge(df_field, on = 'player_mlb_id', how = 'left')

    return df_players

#clean the provided savant data
def clean_savant_data(df_savant_raw):
    #convert game date to datetime column
    df_savant_raw['game_date'] = pd.to_datetime(df_savant_raw['game_date'])
    
    #create column for year
    df_savant_raw['year'] = df_savant_raw['game_date'].dt.year
    
    #create column for runs scored on a play
    df_savant_raw['runs_on_play'] = df_savant_raw['post_bat_score'] - df_savant_raw['bat_score']
    
    #find pythagorean distance of run
    df_savant_raw['dist_pitch_run'] = (df_savant_raw['pfx_x']**2 + df_savant_raw['pfx_z']**2)**.5
    
    #create dataframe for each at bat
    at_bat_ids = df_savant_raw[['batter','pitcher','game_date','year','times_faced']].drop_duplicates()
    
    #assign a unique id to each at bat
    at_bat_ids['at_bat_id'] = range(1, len(at_bat_ids) + 1)
    
    #add unique ids to original savant data
    df_savant = df_savant_raw.merge(at_bat_ids, on=['batter','pitcher','game_date','year','times_faced'],how='inner')

    return df_savant, at_bat_ids