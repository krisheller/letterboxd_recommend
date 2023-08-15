import re
from requests import session
from bs4 import BeautifulSoup
import pandas as pd
import os

#Update to eventually take in any given # of pages? 
kris_url = "https://letterboxd.com/krisheller/watchlist"
chelsea_url = "https://letterboxd.com/clombardo331/watchlist"
m_url = "https://letterboxd.com/mitchell/watchlist"
k_url = 'https://letterboxd.com/kurstboy/watchlist'
t_watchlist = 'https://letterboxd.com/mistat/watchlist/'


def get_watchlist(user_wl_url, verbose=0):
    s = session()
    r = s.get(user_wl_url)
    
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
        if(i==1):
            new_link = user_wl_url
        else:
            new_link = user_wl_url+'page/'+str(i)+'/'
        r = s.get(new_link)

        soup = BeautifulSoup(r.text, "html.parser")

        #select for all movie html elements
        movies = soup.find_all("li", attrs={"class":"poster-container"})

        #add data available in html to appropriate lists
        link_list.extend([movie.find('div').get('data-film-slug') for movie in movies])
        id_list.extend([movie.find('div').get('data-film-id') for movie in movies])
        movie_list.extend([movie.find('img').get('alt') for movie in movies])

    df = pd.DataFrame([link_list, id_list, movie_list]).transpose()
    df.columns=['LinkStub','FilmID','Title']

    return df

def get_movie_details(watchlist, verbose=0):

    #Flesh out the detail present in the movie list 
    #Can either take from existing data frame if already available or
    #Capture more information from the movie's individual page that isn't present from watchlist html

    cwd = os.getcwd()
    path = os.path.join(cwd,'data\movies.csv')

    #pull in movies dataframe that has details saved already if one is available
    try:
        movies = pd.read_csv(path)
    except:
        movies = pd.DataFrame(columns=['LinkStub', 'FilmID', 'Title', 'ReleaseDate', 
                                    'Director', 'Duration','Summary', 'IMDbLink'])
        movies.to_csv(path)

    #create dataframe to hold details for watchlist
    details = pd.DataFrame(columns=['LinkStub', 'FilmID', 'Title', 'ReleaseDate', 
                                    'Director', 'Duration','Summary', 'IMDbLink'])
    
    s = session()

    for i, movie in watchlist.iterrows():
        link = movie['LinkStub']
        id = movie['FilmID']
        title = movie['Title']

        #We already have info on this movie
        if link in set(movies['LinkStub']):
            
           
            movie = movies[movies['LinkStub'] == link]
            details = pd.concat([details, movie])

        #We have to pull from online 
        else:
            movie_link = 'https://letterboxd.com' + link
            r = s.get(movie_link)
            soup = BeautifulSoup(r.text, 'html.parser')

            #target the header of the film's apage
            header = soup.find('section',attrs={'id':'featured-film-header'})

            try:
                date = header.find('small').get_text()
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

            #Finally target the summary of the movie
            summary = soup.find('div', attrs={'class':'truncate'})
            
            try:
                summary = summary.get_text().strip()
            except:
                summary = 'NaN'

            #Add the new data to the csv file
            temp_df = pd.DataFrame({'LinkStub':link,
                                    'FilmID':id,
                                    'Title':title,
                                    'ReleaseDate':date,
                                    'Director':dir,
                                    'Duration':dur,
                                    'IMDbLink':imdb,
                                    'Summary':summary}, index=[0])
            
            movies = pd.concat([movies,temp_df])
            

            #Add it to the df that contains watchlist info
            details = pd.concat([details, temp_df])
            
    #Save out the movies file with the new additions in place
    movies = movies[movies['Duration']!='Adult']
    movies = movies[movies['Duration']!='More']
    movies.to_csv(path, index=False)
        
    #df = pd.DataFrame([link_list, date_list, dir_list, dur_list, summary_list, imdb_list]).transpose()
    #df.columns = ['LinkStub','ReleaseDate','Director','Duration','Summary','IMDbLink']
    return details.reset_index(drop=True)

watch_list = get_watchlist(k_url)

ext_list = get_movie_details(watch_list)
