import re
from requests import session
from bs4 import BeautifulSoup

s = session()
departed_link = 'http://www.imdb.com/title/tt0407887/maindetails'
ptp_link = 'https://www.imdb.com/title/tt0029408/'

def get_imdb_details(link):

    r = s.get(link, headers={'User-Agent': 'Mozzila/5.0'})
    soup = BeautifulSoup(r.text, "html.parser" )
    
    #Get the content rating and average review score
    try:
        parental_rating = soup.find('a',attrs={'href':'/title/tt0407887/parentalguide/certificates?ref_=tt_ov_pg'}).get_text()
    except:
        parental_rating = 'NaN'

    try:
        avg_review = soup.find('span',attrs={'class':'sc-bde20123-1 iZlgcd'}).get_text()
    except:
        'NaN'

    
    #Get the genres, stars & writers
    try:
        genre_list = soup.find_all('a',attrs={'class':'ipc-chip ipc-chip--on-baseAlt'})
        genre_list = [tag.get_text() for tag in genre_list]
    except:
        genre_list = []

    star_list = []
    name_list = soup.find_all('li',attrs={'class':'ipc-metadata-list__item'})
    for name in name_list:
        if 'Stars' in name.get_text():
            for child in name.findChildren('li'):
                star_list.extend([child.get_text()])
            break

    writer_list = []
    name_list = soup.find_all('li',attrs={'class':'ipc-metadata-list__item'})
    for name in name_list:
        if 'Writers' in name.get_text():
            for child in name.findChildren('li'):
                writer_list.extend([child.get_text()])
            break

    #Get the country the movie is from and the language it is in
    country = 'NaN'
    language_list = []

    details = soup.find('section',attrs={'data-testid':'Details'})
    detail_rows = details.findChildren('li')

    for row in detail_rows:
        if 'Countries of origin' in row.get_text():
            country = row.findChildren('li')[0].get_text()
        
        if 'Language' in row.get_text():
            for language in row.findChildren('li'):
                language_list.extend([language.get_text()])


    #Next

    #Box office?


    #Plot keyword tags
    keyword_url = link.replace('maindetails/','') + 'keywords/?ref_=tt_stry_kw'

    #User reviews
    user_review_url = link.replace('maindetails/','') + 'reviews/?ref_=tt_ov_rt'

    #Plot summaries
    summary_url = link.replace('maindetails/','') + 'plotsummary/?ref_=tt_stry_pl'


    return


get_imdb_details(ptp_link)