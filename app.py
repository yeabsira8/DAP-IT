from flask import Flask, render_template, request, Response
from entsoe import EntsoePandasClient
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
from plotly.subplots import make_subplots
from dateutil.relativedelta import relativedelta


app = Flask(__name__)

# create a client object for the ENTSO-E API
client = EntsoePandasClient(api_key='e5be7b41-9794-4b06-9cdf-e8e38e22b97e')

def calculate_statistics(prices):
    average = prices.mean()
    # format average value to two decimal places
    average = "{:.2f}".format(average)
    minimum = prices.min()
    maximum = prices.max()
    negative_count = (prices < 0).sum()
    return average, minimum, maximum, negative_count

@app.route('/', methods=['GET', 'POST'])



def index():
    if request.method == 'POST':
        start_date = pd.Timestamp(request.form['start'], tz='Europe/Amsterdam')
        end_date = pd.Timestamp(request.form['end'], tz='Europe/Amsterdam')


        # query the ENTSO-E API for day-ahead prices for the Netherlands
        country_code = 'NL'
        ts = client.query_day_ahead_prices(country_code, start=start_date, end=end_date)

        def download():
    
          csv_data = ts.to_csv(index=False)    

        # calculate statistics
        average, minimum, maximum, negative_count = calculate_statistics(ts)

       # create a plot of the day-ahead prices using Plotly
        fig = make_subplots(specs=[[{"secondary_y": True}]])

       # Add the day-ahead prices scatter trace
        fig.add_trace(go.Scatter(x=ts.index, y=ts.values, name='Day-ahead Prices (EUR/MWh)'), secondary_y=False)
        fig.add_trace(go.Scatter(x=ts.index, y=[average]*len(ts.index), name='Average price', mode='lines', line=dict(color='red', dash='dash')))



       # Add a horizontal line representing the average value
        average_value = ts.mean()
        fig.add_shape(
           type='line',
           x0=ts.index.min(), y0=average_value, x1=ts.index.max(), y1=average_value,
           line=dict(color='red', width=2, dash='dash'), xref='x1', yref='y1'
           )

       # Add annotations for the minimum and maximum values
        min_value = ts.min()
        max_value = ts.max()
        fig.add_annotation(
        x=ts.idxmin(), y=min_value, text=f'Min: {min_value:.2f}<br> {ts.idxmin().strftime("%d %b %H:%M")}',
        showarrow=True, arrowhead=1, arrowsize=1, arrowwidth=2, ax=0, ay=30,
         bgcolor='rgba(255, 255, 255, 30)',
        font=dict(family='Arial', size=12),
        textangle=0
         )
        
        fig.add_annotation(
        x=ts.idxmax(), y=max_value, text=f'Max: {max_value:.2f}<br> {ts.idxmax().strftime("%d %b %H:%M")}',
        showarrow=True, arrowhead=1, arrowsize=1, arrowwidth=2, ax=0, ay=-30,
         bgcolor='rgba(255, 255, 255, 30)',
        font=dict(family='Arial', size=12),
        textangle=0
         )
        

        # Add a separate scatter trace for the legend with custom text
        legend_trace = go.Scatter(
        x=[None], y=[None], mode='markers', marker=dict(color='rgba(0, 0, 0, 0)'),
        showlegend=True, name=f"<b>Avg:</b> {average_value:.2f} | <b>Min:</b> {min_value:.2f} | <b>Max:</b> {max_value:.2f} <br><b>Hours of negative electricity price:</b> {negative_count} "
        )
        fig.add_trace(legend_trace)

        fig.update_layout(
    title="", xaxis_title="", yaxis_title="EUR/MWh",
    legend=dict(x=0, y=1.3, xanchor='left', yanchor='top'),
 

)

        # Adjust the margin to accommodate the legend outside the graph area
        fig.update_layout(
          margin=dict(t=50, r=150)
)

        # convert the plot to HTML and pass it to the template
        plot = fig.to_html(full_html=False)



        return render_template('index.html', plot=plot, average=average, minimum=minimum,
                               maximum=maximum, negative_count=negative_count,
                               start=start_date, end=end_date, show_stats=True)

    else:
        start_date = pd.Timestamp('2023-01-01', tz='Europe/Amsterdam')
        end_date = pd.Timestamp('2023-01-02', tz='Europe/Amsterdam')
        return render_template('index.html', start=start_date, end=end_date, show_stats=False)
    
    # define a route for downloading the CSV file
@app.route('/download')
def download_csv():
    # get the start and end dates from the query parameters
    start = pd.Timestamp(request.args.get('start'), tz='Europe/Amsterdam')
    end = pd.Timestamp(request.args.get('end'), tz='Europe/Amsterdam')

    # query the ENTSO-E API for day-ahead prices for the Netherlands
    country_code = 'NL'
    type_market_agreement_type = 'A01'
    contract_market_agreement_type = "A01"
    ts = client.query_day_ahead_prices(country_code, start=start, end=end)

   

    # create a Pandas dataframe from the API data
    df = ts.to_frame(name='Day-ahead Prices (EUR/MWh)')

    # add a title to the first row column
    df.index.name = 'Time/Date'

    # change the time index format
    df.index = df.index.strftime('%d-%b-%Y %H:%M')

    # convert the dataframe to a CSV string and add the title to the first row
    output = df.to_csv(header=True, line_terminator='\n')

    # send the CSV file to the user for download
    return Response(
       output,
       mimetype="text/csv",
       headers={"Content-disposition":
                 f"attachment; filename=day_ahead_prices_{start.strftime('%Y-%m-%d')}_{end.strftime('%Y-%m-%d')}.csv"})


if __name__ == '__main__':
    app.run()
