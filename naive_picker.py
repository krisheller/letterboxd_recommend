from scrub_letterboxd import get_watchlist, get_movie_details
import pandas as pd
from random import randint

#Take in a number of watchlists and choose randomly which to watch with an even split
user_list = ['krisheller','clombardo331']

def select_movie(user_list = []):

    wl_list = []

    #If usernames not passed in as args, ask for via keyboard
    stop_loop = False
    if len(user_list) == 0:
        while not stop_loop:
            username = input("Please enter a letterboxd username.\n(type 'quit' to continue)\n")
            if username != 'quit':
                user_list.append(username)
            else:
                stop_loop = True
                if len(user_list) == 0:
                    return False

    #Get the watchlists for each user specified
    for i, username in enumerate(user_list):
        wl = get_watchlist('https://letterboxd.com/'+username+'/watchlist')

        if isinstance(wl, pd.DataFrame):
            wl['i'] = i+1
            wl_list.append(wl)

    #Combine them with labels assigned for possible use in random selections 
    combined_df = pd.DataFrame(columns=wl_list[0].columns)
    for wl in wl_list:
        combined_df = pd.concat([combined_df, wl])

    #Count for any crossover between multiple users
    combined_counts = pd.DataFrame(combined_df['Title'].value_counts())
    max_crossover = max(combined_counts['Title'])

    #If there are any movies all users want to watch, randomly select from among those
    if(max_crossover == len(user_list)):
        possible_selections = combined_counts[combined_counts['Title'] == max(combined_counts['Title'])].reset_index()
        movie = possible_selections.iloc[randint(0,len(possible_selections)-1),0]

    #Otherwise, choose randomly where movies wanted by multiple are weighted more heavily by being listed more than 1x
    else:
        user_selection = randint(1,len(user_list))
        temp_df = combined_df[combined_df['i']==user_selection]
        movie = temp_df.iloc[randint(0,len(temp_df)-1),2]

    return movie