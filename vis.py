# /usr/bin/env python3

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
#   Containerized Amazon Recommender System (CARS) Project
#
#   Authors: Brianna Blain-Castelli, Nikkolas Irwin, Adam Cassell, and Andrew Munoz
#   Date: 04/01/2020
#   Purpose: Build a Big Data application using a Conda environment and Docker.
#   Course: CS 636 Big Data Systems
#   Project: CARS is an application that builds a recommender system from datasets provided by
#            UCSD (see citation below). 
#
#   Dataset URL: https://nijianmo.github.io/amazon/index.html
#
#   ***IMPORTANT*** You must download the dataset files for a particular category to your local machine yourself due
#                   to their size. As long as your dataset files are in the same directory as the Dockerfile, then
#                   they will be added to the volume and usable by the container as expected.
#
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
#   Citation: Justifying recommendations using distantly-labeled reviews and fined-grained aspects
#             Jianmo Ni, Jiacheng Li, Julian McAuley
#             Empirical Methods in Natural Language Processing (EMNLP), 2019
#             PDF: http://cseweb.ucsd.edu/~jmcauley/pdfs/emnlp19a.pdf
#
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
#   Python Vis Module: Python module containing Vis class. To be used for all visualization types.
#
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------


import pandas
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.style as sty
from plotly.subplots import make_subplots
from IPython.display import display

class Vis:

    vis_dict = {}

    def __init__(self, type, data, spark=None):
        self.type = type    # instance variable unique to each instance
        self.data = data
        if (self.type == "summary"):
            self.vis_summary(self.data)
        elif (self.type == "helpful"):
            self.vis_helpful_review(self.data,spark)
        elif (self.type == "prediction"):
            self.vis_prediction(self.data)
        elif (self.type == "time"):
            self.vis_timeseries(self.data,spark)
        else:
            raise Exception("Invalid visualization type")

    def vis_summary(self, data):
        # fig1, ax1 = plt.subplots()
        # data.boxplot(ax=ax1)
        # ax1.set_title('Ratings Summary')
        fig1, ax1 = plt.subplots()
        num_bins = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
        data.hist(ax=ax1,bins=num_bins, edgecolor='white')
        ax1.set_title('Ratings Distribution')
        plt.ylabel('Review Count')
        plt.xlabel('Ratings')
        ax1.grid(False)
        plt.show()

    def vis_helpful_review(self,data,spark):

        data.createOrReplaceTempView('TBL_HELPFUL_REVIEWS')
        result = spark.sql('''SELECT reviewerID, overall, vote FROM TBL_HELPFUL_REVIEWS WHERE asin = 
        (SELECT asin AS `itemID`
                FROM TBL_HELPFUL_REVIEWS
                GROUP BY ASIN
                ORDER BY count(ASIN) DESC LIMIT 1) ''')

        #print(f'\n\nShowing the popularity over time of the most-reviewed item of the dataset...', '\n')


        df = result.toPandas()

        fig0 = make_subplots(rows=1, cols=2)

        fig0.add_trace(
            go.Scattergl(x=df['overall'], y=df['vote'], mode='markers', name="Rating/Vote Correlation"),
            row=1, col=1
        )

        fig0.add_trace(
            go.Bar(x=df['overall'], y=df['vote'], name= "Vote Disbrution Across Ratings"),
            row=1, col=2
        )

        fig0.update_layout(width=900,height=450,title_text="Ratings vs. Votes for Most Popular Item")

        fig0.update_xaxes(title_text="Ratings")
        fig0.update_yaxes(title_text="Votes")

        fig0.show()

        # fig0 = px.scatter(df, x="overall", y="vote", title="Rating/Vote Correlation" ,width=400,height=400, render_mode="webgl")
        # fig0.show()

        # fig_bar = px.bar(df, x="overall", y="vote", title="Vote Disbrution Across Ratings", width=400,height=400)
        # fig_bar.show()

        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add traces
        fig.add_trace(
            go.Scattergl(x=df['reviewerID'], y=df['overall'], name="Ratings", mode='markers'),
            secondary_y=False,
        )

        fig.add_trace(
            go.Scattergl(x=df['reviewerID'], y=df['vote'], name="Votes", mode='markers'),
            secondary_y=True,
        )

        # Add figure title
        fig.update_layout(
            title_text="Ratings/Votes Correlation"
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Reviews")

        # Set y-axes titles
        fig.update_yaxes(title_text="<b>Ratings</b>", secondary_y=False)
        fig.update_yaxes(title_text="<b>Votes</b>", secondary_y=True)

        fig.show()
        
    def vis_prediction(self, data):
        df = data.select(data['overall'], data['prediction']).toPandas()
        print("\nPlotting visualizations...")
        fig = px.scatter(df, x="overall", y="prediction", width=400, height=400,render_mode='webgl')
        fig.show()

        df['error'] = df['prediction'] - df['overall']
        fig2 = px.histogram(df, x="error")
        fig2.update_layout(
            bargap=0.1,
            title={
                'text': "ALS Prediction Error Distribution",
                'y':0.98,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'})
        fig2.show()

    def vis_timeseries(self, data, spark):
        k = 10
        data.createOrReplaceTempView('TBL_RATING_TIMESERIES')
        top_items = spark.sql('''SELECT count(ASIN) AS `Review Count`,
                                    asin AS `ASIN`
                             FROM TBL_RATING_TIMESERIES
                             GROUP BY ASIN
                             ORDER BY `Review Count` DESC''')

        print(f'\n\nShowing the {k} most reviewed items for the dataset.', '\n')
        #top_items.show(n=k)
        ti = top_items.toPandas()
        display(ti[0:k])

        # Note: 'Most Popular Item' in the below query really refers to the 'Review Count' of the most popular item.
        #       Using 'Most Popular Item' alias for simplicity for plot labeling purposes
        data.createOrReplaceTempView('TBL_RATING_TIMESERIES')
        df = spark.sql('''SELECT count(ASIN) as `Most Popular Item`, unixReviewTime AS `Review Date`  FROM TBL_RATING_TIMESERIES WHERE asin = 
        (SELECT asin AS `itemID`
                FROM TBL_RATING_TIMESERIES
                GROUP BY ASIN
                ORDER BY count(ASIN) DESC LIMIT 1) 
        GROUP BY `Review Date` ORDER BY `Review Date` ''')

        print(f'\n\nShowing the popularity over time of the most-reviewed item of the dataset...', '\n')
        #df.show(n=k)

        # Convert milliseconds to date

        df_pandas = df.toPandas()

        # Convert date string to pyspark date type
        df_pandas['Review Date'] = pandas.to_datetime(df_pandas['Review Date'], unit='s')
        # display(df_pandas)

        # gca stands for 'get current axis'
        ax = plt.gca()
        df_pandas.plot(kind='line',x='Review Date',y='Most Popular Item',figsize=(16, 4),ax=ax)
        plt.ylabel('Review Count')
        #df.plot(kind='line',x='RT',y='num_pets', color='red', ax=ax)
        plt.show()
