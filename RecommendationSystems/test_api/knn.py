import datetime
import numpy as np
import pandas as pd
from scipy.spatial.distance import hamming

def file_to_df(path, usecols, delimiter=','):
    '''
    Import text file data to a pandas dataframe object

    param path: path of text file containing data to import
    param usecols: list of columns to take
    param delimiter: character used to separate data elements in a line

    return: DataFrame object of data frm text file
    '''
    # Read file line-by-line into a list
    with open(path, errors='replace') as file:
        data = file.readlines()

    # Clean data
    for i in range(len(data)):
        data[i] = data[i].replace('\n', '')  # Remove newline chars

    # Convert array of strings into 2D list of strings
    data = [line.split(delimiter) for line in data]

    # Convert 2D list to a DataFrame object
    df = pd.DataFrame(data)

    # Set column names to values in first row
    df.columns = list(df.iloc[0])

    # Take specified columns only
    df = df[usecols]

    # Delete first row since it contains column names and not values
    df = df.drop(0)

    # Reset to 0-based index
    df.index = range(len(df.index))

    return df


class Knn:
    # Set data file paths
    movies_path = 'data/movielens_2k/movies.dat'
    movie_actors_path = 'data/movielens_2k/movie_actors.dat'
    movie_directors_path = 'data/movielens_2k/movie_directors.dat'
    movie_genres_path = 'data/movielens_2k/movie_genres.dat'
    user_rated_movies_path = 'data/movielens_2k/user_ratedmovies.dat'

    def __init__(self):
        #############
        # Load data #
        #############
        self.df_movies = file_to_df(self.movies_path, delimiter='\t',
                               usecols=['id', 'title', 'imdbID', 'rtID', 'rtAllCriticsRating', 'rtAllCriticsNumReviews',
                                        'rtAllCriticsScore', 'rtTopCriticsRating', 'rtTopCriticsNumReviews',
                                        'rtTopCriticsNumFresh', 'rtTopCriticsNumRotten', 'rtTopCriticsScore',
                                        'rtAudienceRating', 'rtAudienceNumRatings', 'rtAudienceScore'])
        self.df_movie_actors = file_to_df(self.movie_actors_path, delimiter='\t',
                                     usecols=['movieID', 'actorID', 'actorName', 'ranking'])
        self.df_movie_directors = file_to_df(self.movie_directors_path, delimiter='\t',
                                        usecols=['movieID', 'directorID', 'directorName'])
        self.df_movie_genres = file_to_df(self.movie_genres_path, delimiter='\t', usecols=['movieID', 'genre'])
        self.df_user_rated_movies = file_to_df(self.user_rated_movies_path, delimiter='\t', usecols=['userID', 'movieID', 'rating'])

        # Create User/Movie ratings matrix
        self.df_user_movie_ratings = self.df_user_rated_movies.pivot(index='userID', columns='movieID', values='rating')

        # Replace null values with a numerical equivalent, then cast all data types in table to float
        self.df_user_movie_ratings.fillna(value=np.nan, inplace=True)
        self.df_user_movie_ratings = pd.DataFrame(self.df_user_movie_ratings, dtype=np.float32)


    def hamming_distance(self, userID_1, userID_2):
        '''
        Finds hamming distance between two users.
        Hamming distance is the number of features that differ between the two users.

        '''
        distance = hamming(self.df_user_movie_ratings.loc[userID_1], self.df_user_movie_ratings.loc[userID_2])
        return distance


    def find_knn(self, userID, k=3):
        '''
        Finds k nearest neighbors of userID based on hamming distance

        param userID: userID to get neighbors for
        param k: number of neighbors
        '''
        # Get data for all other users except specified user
        df_other_user_movie_ratings = self.df_user_movie_ratings.loc[self.df_user_movie_ratings.index != userID]

        # Calculate distance between specified user and all other users
        df_other_user_movie_ratings['distance'] = df_other_user_movie_ratings.apply(
            lambda row: self.hamming_distance(userID, row.name), axis=1)

        # Sort users by distance (closest first)
        df_other_user_movie_ratings.sort_values(['distance'], axis=0, inplace=True)

        # Take top k users (k nearest users)
        df_other_user_movie_ratings = df_other_user_movie_ratings.iloc[0:k]

        return df_other_user_movie_ratings

    def get_unrated_movies_for_user(self, userID):
        '''
        Gets unrated movies from user/movie ratings matrix by finding row of userID,
        then finding any column (movieID) with a null value

        param userID: userID to get unrated movies for

        return: list of movieID's that the specified user has not rated yet
        '''

        # n = single user's movie ratings
        n = self.df_user_movie_ratings.loc[self.df_user_movie_ratings.index == userID]
        cols = list(n.columns)
        unrated_movies = [cols[i] for i in range(len(cols)) if pd.isnull(n[str(cols[i])][0])]

        return unrated_movies

    def get_movie_details(self, movie_id):
        movie_details = {}
        movie_details['title'] = [self.df_movies.loc[self.df_movies.id == movie_id].iloc[0].title]
        movie_details['actors'] = list(self.df_movie_actors.loc[self.df_movie_actors.movieID == movie_id].actorName)
        movie_details['director'] = [
            self.df_movie_directors.loc[self.df_movie_directors.movieID == movie_id].iloc[0].directorName]
        movie_details['genres'] = list(self.df_movie_genres.loc[self.df_movie_genres.movieID == movie_id].genre)

        return movie_details

    def movie_details_to_df(self, movie_details):
        data = [movie_details['title'],
                movie_details['director'],
                movie_details['actors'],
                movie_details['genres']]

        df = pd.DataFrame(data).transpose().fillna(value='')
        df.columns = ['title', 'director', 'actors', 'genres']

        return df

    def getRecommendations(self, userID, k=10, num_recs=10):
        df_knn = self.find_knn(userID, k)

        # Get mean of movie ratings for nearest neighbors
        avg = df_knn.agg(['mean'], numeric_only=True)

        # Place avg movie ratings into a column, then remove any movies rated by the user
        unrated_movies = self.get_unrated_movies_for_user(userID)
        avg_filtered = avg.transpose().loc[unrated_movies]

        # Sort movies based on mean average (descending)
        avg_sorted = avg_filtered.sort_values(['mean'], axis=0, ascending=False)

        # Get top recommendations
        top_recommendations = avg_sorted[0:num_recs]

        # Get list of all movie details after converting each set of movie details to a dataframe
        movie_details_df_list = [self.movie_details_to_df(self.get_movie_details(movieID)) for movieID in
                                 list(top_recommendations.index)]

        # Concatenate all movies into a single dataframe for futher analysis
        df_movie_details = pd.concat(movie_details_df_list)

        # Create an ID column
        df_movie_details['id'] = range(df_movie_details.shape[0])

        # Look for unique titles
        titles = pd.Series(df_movie_details['title'].unique())
        titles = [value for index, value in titles.iteritems() if value != '']

        # Look for favorite genres
        genres = df_movie_details.groupby('genres')['title'].count().drop('').sort_values(ascending=False)
        genres = [index + ', ' + str(value) for index, value in genres.iteritems()]

        # look for favorite actors
        actors = df_movie_details.groupby('actors')['id'].count().sort_values(ascending=False).iloc[0:10]
        actors = [index + ', ' + str(value) for index, value in actors.iteritems()]

        # look for favorite directors
        directors = df_movie_details.groupby('director')['id'].count().drop('').sort_values(ascending=False)
        directors = [index + ', ' + str(value) for index, value in directors.iteritems()]

        results = {
            "titles": titles,
            "stats": {
                "genres": genres,
                "actors": actors,
                "directors": directors
            }
        }

        return results
