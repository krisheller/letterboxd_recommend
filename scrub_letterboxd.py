import re
from requests import session
from bs4 import BeautifulSoup

import pandas as pd
import os
import numpy as np

#Update to eventually take in any given # of pages? 
kris_url = "https://letterboxd.com/krisheller/watchlist"
chelsea_url = "https://letterboxd.com/clombardo331/watchlist"
m_url = "https://letterboxd.com/mitchell/watchlist"
k_url = 'https://letterboxd.com/kurstboy/watchlist'
t_watchlist = 'https://letterboxd.com/mistat/watchlist/'

#The session to query within letterboxd.com
s = session()

def get_watchlist(username, verbose=0):
    wl_url = 'https://letterboxd.com/'+username+'/watchlist/'
    r = s.get(wl_url)
    
    soup = BeautifulSoup(r.text, "html.parser")

    #First check to see if username is valid
    error = soup.find('body',attrs={'class':'error message-dark'})
    if error != None:
        print("Error: invalid letterboxd username passed to get_watchlist()")
        return False

    #Determine if there is more than one page of movies on the watchlist
    try:
        page_count = int(soup.find_all("li", attrs={"class": "paginate-page"})[-1].get_text())
        
    except:
        page_count = 1

    #Lists to hold variable values
    movie_list = []
    link_list = []
    id_list = []

    #Find movies on each page
    for i in range(1,page_count+1):
        
        #construct link for watchlist page
        if(i!=1):
            new_link = wl_url+'/page/'+str(i)+'/'
            r = s.get(new_link)
            soup = BeautifulSoup(r.text, "html.parser")            

        if verbose != 0 and (i==1 or i%10 == 0 or i==page_count):
            print("Pulling from Page #"+str(i)+"/"+str(page_count)+" of watch list from "+username+"...")

        #select for all movie html elements
        movies = soup.find_all("li", attrs={"class":"poster-container"})

        #add data available in html to appropriate lists
        link_list.extend([movie.find('div').get('data-film-slug') for movie in movies])
        id_list.extend([int(movie.find('div').get('data-film-id')) for movie in movies])
        movie_list.extend([movie.find('img').get('alt') for movie in movies])

    df = pd.DataFrame([link_list, id_list, movie_list]).transpose()
    df.columns=['LinkStub','FilmID','Title']
    df.set_index('FilmID', inplace=True)

    return df

def get_movie_details(watchlist, verbose=0):

    #Flesh out the detail present in the movie list 
    #Can either take from existing data frame if already available or
    #Capture more information from the movie's individual page that isn't present from watchlist html
    
    cwd = os.getcwd()
    path = os.path.join(cwd,'data\movies.csv')

    #pull in movies dataframe that has details saved already if one is available
    try:
        movies = pd.read_csv(path, index_col='FilmID')
        #movies.index = movies.index.map(int)
    except:
        movies = pd.DataFrame(columns=['LinkStub', 'FilmID', 'Title', 'ReleaseDate', 
                                    'Director', 'Duration','Summary', 'IMDbLink'])
        movies.set_index('FilmID', inplace=True)
        movies.to_csv(path)

    #create dataframe to hold details for watchlist
    details = pd.DataFrame(columns=['LinkStub', 'FilmID', 'Title', 'ReleaseDate', 
                                    'Director', 'Duration','Summary', 'IMDbLink'])
    details.set_index('FilmID', inplace=True)

    #Generate a union between movies.csv and the watchlist to pull from more efficiently
    shared_movies = movies.reset_index().merge(watchlist, how='inner').set_index('FilmID')
    
    try:
        shared_movies.index = shared_movies.index.astype('int64')
    except:
        pass

    new_indices = np.setdiff1d(watchlist.index, shared_movies.index)

    #Start off adding all the movies that we already have stored 
    details = pd.concat([details, shared_movies])

    count = 0

    #Then add the ones we don't have
    for i in new_indices:
        movie = watchlist.loc[i]
        count += 1
        link = movie['LinkStub']
        title = movie['Title']
        
        if verbose!=0 and (count%100 == 0 or count == 1 or count==len(new_indices)):
            print("Getting extra details on new movies, "+str(count)+"/"+str(len(new_indices))+"...")

        #We have to pull from online 
        else:
            movie_link = 'https://letterboxd.com' + link
            r = s.get(movie_link)
            soup = BeautifulSoup(r.text, 'html.parser')

            #target the header of the film's apage
            header = soup.find('section',attrs={'id':'featured-film-header'})

            try:
                date = int(header.find('small').get_text())
            except:
                date = 'NaN'
            
            try:
                dir = header.find('span').get_text()
            except:
                dir = 'NaN'
            
            #Target the footer that contains duration and link to imdb
            footer = soup.find('p', attrs={'class':'text-link'})

            try:
                dur = footer.get_text().split()[0]
            except:
                dur = 'NaN'

            try:
                imdb = footer.find('a',attrs={'data-track-action':'IMDb'}).get('href')
            except:
                imdb = 'NaN'

            #target the summary of the movie
            summary = soup.find('div', attrs={'class':'truncate'})
            
            try:
                summary = summary.get_text().strip()
            except:
                summary = 'NaN'

            #Add the new data to the csv file
            temp_df = pd.DataFrame({'LinkStub':link,
                                    'FilmID':i,
                                    'Title':title,
                                    'ReleaseDate':date,
                                    'Director':dir,
                                    'Duration':dur,
                                    'IMDbLink':imdb,
                                    'Summary':summary}, index=[0])
            temp_df.set_index('FilmID', inplace=True)
            
            movies = pd.concat([movies,temp_df])
            
            #Add it to the df that contains watchlist info
            details = pd.concat([details, temp_df])
            
    #Save out the movies file with the new additions in place
    movies = movies[movies['Duration']!='Adult']
    movies = movies[movies['Duration']!='More']
    movies.to_csv(path)

    print(str(len(new_indices))+" new movies added to database.")

    details = details[details['Duration']!='Adult']
    details = details[details['Duration']!='More']
        
    return details.reset_index(drop=True)

def get_ratings(username, verbose=0, add_to_database=True):
    films_url = 'https://letterboxd.com/'+username+'/films/'
    r = s.get(films_url)
    
    soup = BeautifulSoup(r.text, "html.parser")

    #First check to see if username is valid
    error = soup.find('body',attrs={'class':'error message-dark'})
    if error != None:
        print("Error: invalid letterboxd username passed to get_watchlist()")
        return False

    #Determine if there is more than one page of movies on the watchlist
    try:
        page_count = int(soup.find_all("li", attrs={"class": "paginate-page"})[-1].get_text())
        
    except:
        page_count = 1

    link_list = []
    id_list = []
    movie_list = []
    rating_list = []
    like_list = []

    for i in range(1,page_count+1):

        #construct link for watchlist page
        if(i!=1):
            new_link = films_url+'/page/'+str(i)+'/'
            r = s.get(new_link)
            soup = BeautifulSoup(r.text, "html.parser")

        if verbose != 0 and (i==1 or i%10==0 or i==page_count):
            print("Pulling from Page #"+str(i)+"/"+str(page_count)+" of review list from "+username+"...")

        #parse through the films 
        movies = soup.find_all('li', attrs={'class':'poster-container'})

        #Pull out the links, IDs, and titles
        link_list.extend([movie.find('div').get('data-film-slug') for movie in movies])
        id_list.extend([movie.find('div').get('data-film-id') for movie in movies])
        movie_list.extend([movie.find('img').get('alt') for movie in movies])
        
        #Determine the rating assigned
        rating_list_temp = [movie.find('p',attrs={'poster-viewingdata'}).get_text().strip() for movie in movies]

        #Convert ratings into numerical values
        rating_list.extend(['NaN' if x=='' else len(x) if x[-1]=='★' else len(x)-.5 for x in rating_list_temp])

        #Did the movie receive a like?
        like_list_temp = ([movie.find('span',attrs={'class':'icon'}) for movie in movies])
        like_list.extend([0 if x==None else 1 for x in like_list_temp])

    df = pd.DataFrame([link_list, id_list, movie_list, rating_list, like_list]).transpose()
    df.columns=['LinkStub','FilmID','Title','Rating','Liked']
    df.set_index('FilmID', inplace=True)
    df.index = df.index.astype('int64')

    #Unless told not to add any new movies to movies.csv
    get_movie_details(df.drop(['Rating','Liked'], axis=1), verbose=1)

    return df

def scrub_popular_members(max_pages=10, start_page=1, verbose=0):

    url_base = 'https://letterboxd.com/members/popular/this/all-time/page/'
    user_list = []

    for i in range(start_page, max_pages+1):
        url = url_base + str(i)
        r = s.get(url)

        soup = BeautifulSoup(r.text, "html.parser")

        users = soup.find_all('a', attrs={'class':'name'})
        user_list.extend([user.get('href').replace('/','') for user in users])
    n=1
    for i, user in enumerate(user_list):
        get_movie_details(get_watchlist(user, verbose=n), verbose=n)
        get_ratings(user, verbose=n)

        if (1+i)%1 == 0 and (i+1) > 0 and verbose > 0:
            print("Finished scrubbing user #"+str(i+1)+"/"+str(35*max_pages)+"...")
            

    return