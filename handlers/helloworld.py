"""
    helloworld.py
    ~~~~~~~~~~~~~

    Provides a simple Tornado handler that hits the BV Data API.
    It's simply a small example of how to consume the API in tornado.

    It has been editted by Suharsh Sivakumar for practice purposes.
"""


import logging
import tornado.gen
import tornado.web

import bvapi.client

#import the math library (this wasn't already in the code)
from math import sqrt

log = logging.getLogger(__name__)


API_KEY = '2loajckmwyjaz1umx6ej0ebwl'  #'kuy3zj9pr3n7i0wxajrzj04xo'
API_HOST = 'cabelas.ugc.bazaarvoice.com'  #'reviews.apitestcustomer.bazaarvoice.com'


class HelloWorldHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        """Retrieves reviews from the API and renders info about them."""
        api = bvapi.client.BvApi(API_KEY, API_HOST, staging=False)

        api_params = {
            'include': 'products',
            'stats':   'reviews'  # to get product average overall rating
        }

        response = yield tornado.gen.Task(api.get_products, **api_params)
        results = response.Results
        sum_ratings = 0
        sum_var = 0
        count = 0
        
        #for element in results:
         #   print element.Name
          #  print element.Stats.AverageOverallRating
           # sum_ratings = sum_ratings + element.Stats.AverageOverallRating
            #count = count + 1

        # the following was down the wrong path as it considered each review as a danger situation, but what we really care about is the average of the product
        #calculate the mean
        #mean_rating = float(sum_ratings) / float(count)
        #for element in results:
         #   sum_var = sum_var + (element.Stats.Rating - mean_rating)*(element.Stats.Rating - mean_rating)
        #calculate the variance
        #variance_rating = float(sum_var) / float(count)
        #sd_rating = sqrt(variance_rating)
        for element in results:
            if str(element.ReviewStatistics.TotalReviewCount) != 'None':
                print 'The mean rating of ' + str(element.Name) + ' is ' + str(element.ReviewStatistics.AverageOverallRating) 
        #print 'The variance of the ratings is ' + str(variance_rating)
       # print 'The standard deviation of the ratings is ' + str(sd_rating)
        #Now print two sds aways in either direction
#
 #       min_value = mean_rating - sd_rating
  #      max_value = mean_rating + sd_rating
   #     really_min_value = min_value - sd_rating
     #   really_max_value = max_value + sd_rating
    #    for element in results:
#            if element.Rating < really_min_value:
 #               print (element.Product.Name).encode("utf-8") + ' is a horrible product!'
  #          elif element.Rating < min_value:
   #             print (element.Product.Name).encode("utf-8") + ' is a bad product!'
    #        if element.Rating > really_max_value:
     #           print (element.Product.Name).encode("utf-8") + ' is a great product!'
      #      elif element.Rating > max_value:
       #         print (element.Product.Name).encode("utf-8") + ' is a good product!'
        total_reviews = response.TotalResults
        self.render('helloworld.html', total_reviews=total_reviews, review=response.Results[0])


