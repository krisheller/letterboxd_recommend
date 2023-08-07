import re
from requests import session
from bs4 import BeautifulSoup

#Update to eventually take in any given # of pages? 
kris_url = "https://letterboxd.com/krisheller/watchlist"
chelsea_url = "https://letterboxd.com/clombardo331/watchlist"


def get_watchlist(user_wl_url):
    MATCH_TOTAL_MOVIES = re.compile(r"to see (\d+)")
    s = session()
    r = s.get(user_wl_url)

    soup = BeautifulSoup(r.text, "html.parser")

    watchlist_title = soup.find("meta", attrs={"property": "og:title"})

    ul = soup.find("ul", attrs={"class": "poster-list"})
    movies = ul.find_all("div")

    title_list = [movie.find('img').get('alt') for movie in movies]

    return title_list

print(get_watchlist(kris_url))