import re
from requests import session
from bs4 import BeautifulSoup

import pandas as pd
import numpy as np

import os

s = session()

def get_imdb_details(link):

    r = s.get(link, headers={'User-Agent': 'Mozzila/5.0'})
    soup = BeautifulSoup(r.text, "html.parser" )
    
    #Get the content rating and average review score / metascore
    try:
        for substring in link.split("/"):
            if 'tt' in substring:
                imdb_id = substring
        rating_link = '/title/'+imdb_id+'/parentalguide/certificates?ref_=tt_ov_pg'
        parental_rating = soup.find('a',attrs={'href':rating_link}).get_text()
    except:
        parental_rating = None

    try:
        avg_review = soup.find('span',attrs={'class':'sc-bde20123-1 iZlgcd'}).get_text()
    except:
        avg_review = None

    try:
        metascore = int(soup.find('span',attrs={'class':'score-meta'}).get_text())
    except:
        metascore = None
    
    #Get the # of reviews (users / critics) and the # of ratings
    try:
        rate_count = soup.find('div',attrs={'class':'sc-bde20123-3 bjjENQ'}).get_text()
        rate_count = convert_str_to_number(rate_count)

    except:
        rate_count = None

    try:
        user_review_link = '/title/'+imdb_id+'/reviews/?ref_=tt_ov_rt'
        user_review_count = soup.find('a',attrs={'href':user_review_link}).findChildren('span',attrs={'class':'score'})[0].get_text()
        user_review_count = convert_str_to_number(user_review_count)
    except:
        user_review_count = None

    try:
        critic_review_link = '/title/'+imdb_id+'/externalreviews/?ref_=tt_ov_rt'
        critic_review_count = soup.find('a',attrs={'href':critic_review_link}).findChildren('span',attrs={'class':'score'})[0].get_text()
        critic_review_count = convert_str_to_number(critic_review_count)
    except:
        critic_review_count = None
    
    #Get the genres, stars & writers
    try:
        genre_list = soup.find_all('a',attrs={'class':'ipc-chip ipc-chip--on-baseAlt'})
        genre_list = [tag.get_text() for tag in genre_list]
    except:
        genre_list = []

    star_list = []
    name_list = soup.find_all('li',attrs={'class':'ipc-metadata-list__item'})
    for name in name_list:
        if 'Star' in name.get_text():
            for child in name.findChildren('li'):
                star_list.extend([child.get_text()])
            break

    writer_list = []
    name_list = soup.find_all('li',attrs={'class':'ipc-metadata-list__item'})
    for name in name_list:
        if 'Writer' in name.get_text():
            for child in name.findChildren('li'):
                writer_list.extend([child.get_text()])
            break

    #Get the country the movie is from and the language it is in
    country = None
    language_list = []

    try:
        details = soup.find('section',attrs={'data-testid':'Details'})
        detail_rows = details.findChildren('li')

        for row in detail_rows:
            if 'Countries of origin' in row.get_text():
                country = row.findChildren('li')[0].get_text()
            
            if 'Language' in row.get_text():
                for language in row.findChildren('li'):
                    language_list.extend([language.get_text()])
    except:
        pass

    #Box office & gross revenue
    box_office = soup.find('section',attrs={'data-testid':'BoxOffice'})

    budget = None
    rev = None

    try:
        bo_rows = box_office.findChildren('li')
        for row in bo_rows:      
            if 'Budget' in row.get_text():
                budget = int(row.findChildren('div')[0].get_text().split(' ')[0].strip("$").strip("€").replace(',',''))
        for row in bo_rows:
            if 'Gross worldwide' in row.get_text():
                rev = int(row.findChildren('div')[0].get_text().split(' ')[0].strip("$").strip("€").replace(',','')) 
    except:
        pass

    #Plot keyword tags
    keyword_link = link.replace('maindetails','') + 'keywords/?ref_=tt_stry_kw'
    r = s.get(keyword_link, headers={'User-Agent': 'Mozzila/5.0'})
    soup = BeautifulSoup(r.text, "html.parser" )
    
    #Check for error
    error = soup.find_all('div', attrs={'id':'error'})
    if len(error) > 0:
        keyword_list = []
    else:
        keyword_list = []
        keywords = soup.find_all('li',attrs={'class':'ipc-metadata-list-summary-item sc-705bad28-0 cVlGnk'})
        
        for word in keywords:
            keyword_list.extend([word.get_text()])

    #User reviews
    user_review_link = link.replace('maindetails','') + 'reviews/?ref_=tt_ov_rt'
    r = s.get(user_review_link, headers={'User-Agent': 'Mozzila/5.0'})
    soup = BeautifulSoup(r.text, "html.parser" )
    
    #Check for error
    error = soup.find_all('div', attrs={'id':'error'})
    if len(error) > 0:
        review_list = []
    else:
        review_list = []
        reviews = soup.find_all('div',attrs={'class':'content'})
        for review in reviews:
            review_list.extend([review.findChildren('div')[0].get_text()])
    
    #Plot summaries
    summary_link = link.replace('maindetails','') + 'plotsummary/?ref_=tt_stry_pl'
    r = s.get(summary_link, headers={'User-Agent': 'Mozzila/5.0'})
    soup = BeautifulSoup(r.text, "html.parser" )
    
    #Check for error
    error = soup.find_all('div', attrs={'id':'error'})
    if len(error) > 0:
        summary_list = []
    else:
        summary_list = []
        summaries = soup.find_all('div',attrs={'class':'ipc-html-content-inner-div'})
        for summary in summaries:
            summary_list.extend([summary.get_text().split("—")[0]])

    #Put together return value!
    df = pd.DataFrame({'IMDbLink':link,
                        'Rating':parental_rating,
                        'AvgReview':avg_review,
                        'RateCount':rate_count,
                        'UserReviewCount':user_review_count,
                        'CriticReviewCount':critic_review_count,
                        'Metascore':metascore,
                        'Genres':None,
                        'Stars':None,
                        'Writers':None,
                        'Country':country,
                        'Languages':None,
                        'Budget':budget,
                        'Revenue':rev,
                        'Tags':None,
                        'Reviews':None,
                        'Summaries':None,}, index=[0])
    
    list_dict = {'Genres':genre_list,
                 'Stars':star_list,
                 'Writers':writer_list,
                 'Languages':language_list,
                 'Tags':keyword_list,
                 'Reviews':review_list,
                 'Summaries':summary_list}
    
    for key,value in list_dict.items():
        df.at[0,key] = value

    df.set_index('IMDbLink',inplace=True)

    return df

def scrub_movies(max_scrub=None):
    #Run get_imdb_details through the movies.csv database
    path = os.path.join(os.getcwd(),'data\details.csv')

    movies = pd.read_csv('data\movies.csv')

    if max_scrub == None:
        max_scrub = len(movies)

    #Check if details file already exists, only get new details each time this is run
    try:
        details = pd.read_csv(path, index_col='IMDbLink')
    except:
        details = pd.DataFrame({})

    count=0
    print("Beginning to scrub IMDb data...")

    for i, movie in movies.iterrows():
        if isinstance(movie['IMDbLink'], str):
            if 'http' in movie['IMDbLink']:
                if movie['IMDbLink'] not in details.index:
                    details = pd.concat([details,get_imdb_details(movie['IMDbLink'])])
                    count+=1

        #Save it every 100 movies just in case
        if count%20==0 and count>0:
            details.to_csv(path)
            print("Scrubbed IMDb data for "+str(count)+"/"+str(max_scrub)+" new movies..."+str(len(details))+" in total catalogued.")

        #Break it off if exceeding max
        if count == max_scrub:
            break

    #Final save
    details.to_csv(path)

#Credit: gajeshbhat via GitHub
def convert_str_to_number(x):
    total_stars = 0
    num_map = {'K':1000, 'M':1000000, 'B':1000000000}
    if x.isdigit():
        total_stars = int(x)
    else:
        if len(x) > 1:
            total_stars = float(x[:-1]) * num_map.get(x[-1].upper(), 1)
    return int(total_stars)

    return details