from flask import Flask, request, send_from_directory
from flask_restful import Resource, Api
import json
import datetime
from knn import Knn
#https://impythonist.wordpress.com/2015/07/12/build-an-api-under-30-lines-of-code-with-python-and-flask/


print('Preparing application...')
# Create flask app
app = Flask(__name__)
api = Api(app)

# Create KNN learner and import data
knn = Knn()
print('App is ready')


# Create api
class Movie_Recs(Resource):
    def get(self, userID, k, num_recs):
        start = datetime.datetime.now()
        recommendations = knn.getRecommendations(userID, k, num_recs)
        end = datetime.datetime.now()

        print('Time to process request: ' + str(end-start))
        return json.dumps(recommendations)


# Host static html page
@app.route('/home/<path:path>')
def send_html(path):
    return send_from_directory('', path)

api.add_resource(Movie_Recs, '/recommend/<string:userID>/<int:k>/<int:num_recs>')

if __name__ == '__main__':
    app.run()

