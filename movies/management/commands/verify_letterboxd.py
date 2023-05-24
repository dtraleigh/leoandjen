import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from movies.models import Movie

base_url = "https://letterboxd.com/film/"


class Command(BaseCommand):
    def handle(self, *args, **options):
        movies = Movie.objects.all().order_by('title')
        # movies = Movie.objects.filter(title__icontains="alien vs")
        # movies = Movie.objects.filter(title__istartswith="a")
        self.check_that_all_urls_are_valid(movies)
        self.check_that_all_movie_years_match_urls(movies)

    def get_page_content(self, page_link):
        try:
            letterboxd_page = requests.get(page_link, timeout=10)
        except requests.exceptions.RequestException as e:
            print(f"Connection problem to {page_link}")
            print(e)
            letterboxd_page = None

        return letterboxd_page

    def get_letterboxd_page_movie_title(self, soup):
        try:
            return soup.find("h1", {"class": "headline-1 js-widont prettify"}).get_text()
        except AttributeError:
            print("Couldn't find a movie_title")
            print(soup.find("h1", {"class": "headline-1 js-widont prettify"}))
            return None

    def get_letterboxd_page_movie_year(self, soup):
        letterboxd_page_movie_year = None
        letterboxd_page_links = soup.find_all("a")
        for link in letterboxd_page_links:
            try:
                if "/films/year/" in link["href"]:
                    letterboxd_page_movie_year = link.get_text()
            except KeyError:
                pass
        return letterboxd_page_movie_year

    def strip_down_title(self, title):
        # let's try and make the title more generic so we can compare it
        new_title = ""
        for char in title:
            if char == " ":
                new_title += "-"
            elif not char.isalnum():
                new_title += ""
            else:
                new_title += char.lower()
        return new_title

    def check_that_all_urls_are_valid(self, movies):
        # Take the url slug in the database and validate that a legit letterbox page opens
        # Scrape the pages title and year
        # the page movie may not match the DB movie but that's ok for now
        completed_movies = []
        for movie in movies:
            page_link = f"{base_url}{movie.letterboxd_url_slug}/"

            letterboxd_page = self.get_page_content(page_link)
            soup = BeautifulSoup(letterboxd_page.content, "html.parser")

            letterboxd_page_movie_title = self.get_letterboxd_page_movie_title(soup)
            letterboxd_page_movie_year = self.get_letterboxd_page_movie_year(soup)

            try:
                if letterboxd_page_movie_title and letterboxd_page_movie_year:
                    completed_movies.append((letterboxd_page_movie_title, letterboxd_page_movie_year))
                # print(f"{letterboxd_page_movie_title.get_text()} - {letterboxd_page_movie_year}")
            except Exception:
                print(f"check {movie}")

    def check_that_all_movie_years_match_urls(self, movies):
        # Confirm that the scraped movie title and year match the title and year in the DB
        # titles will probably not be exact
        matching_movies = []
        not_matching_movies = []
        for movie in movies:
            page_link = f"{base_url}{movie.letterboxd_url_slug}/"

            letterboxd_page = self.get_page_content(page_link)
            soup = BeautifulSoup(letterboxd_page.content, "html.parser")

            db_movie_title = self.strip_down_title(movie.title)
            db_movie_year = movie.primary_release_year
            letterboxd_page_movie_title = self.get_letterboxd_page_movie_title(soup)
            letterboxd_page_movie_year = self.get_letterboxd_page_movie_year(soup)

            my_movie = (db_movie_title, str(db_movie_year))
            lb_movie = (letterboxd_page_movie_title, letterboxd_page_movie_year)

            if my_movie[1] == lb_movie[1]:
                matching_movies.append(my_movie)
            else:
                # movie.letterboxd_url_slug = f"{movie.letterboxd_url_slug}-{movie.primary_release_year}"
                # movie.save()
                not_matching_movies.append(my_movie)

        print("not_matching_movies")
        for no_match in not_matching_movies:
            print(no_match)
        # print("matching_movies")
        # print(matching_movies)
