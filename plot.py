from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter, SingleIntervalTicker, LinearAxis
from bokeh.models import Range1d, Label, BoxAnnotation, Grid
from datetime import datetime, date, time, timedelta

def plot_comp(
#general
    title = '',
    plot_width = '',
    plot_height = '',
    x_axis_type = '',
    x_axis_format = '',
    xmin = '',
    xmax = '',
    #ytick_interval = '',
    tools = ['pan','xwheel_zoom','box_zoom','ywheel_zoom','reset'],
#    tools = ['pan','xwheel_zoom','box_zoom','ywheel_zoom','crosshair','resize','reset'],
    sunrise = 0,
    sunset = 0,
#plot1
    type_1 = '',
    d1_index = '',
    d1_data = '',
    color_1 = '',
    line_1_width = '',
    line_1_type = '',
#plot2
    type_2 = '',
    d2_index = '',
    d2_data = '',
    color_2 = '',
    line_2_width = '',
    line_2_type = ''
    ):
    
    "Function info"
    
    plot = figure(title=title, plot_width = plot_width, plot_height = plot_height, x_axis_type = x_axis_type, tools = tools)
    plot.line(d1_index, d1_data, line_width = line_1_width, color = color_1, line_dash = line_1_type)
    plot.line(d2_index, d2_data, line_width = line_2_width, color = color_2, line_dash = line_2_type)
    plot.toolbar.logo = None
    plot.toolbar_location = "above"
    plot.x_range = Range1d(xmin, xmax)
    plot.xaxis[0].formatter = x_axis_format
    
    #Day and night
    for i in range(len(sunrise)):
        if i > 0:
            left_box = BoxAnnotation(left=sunset[i-1], right=sunrise[i], fill_alpha=0.2, fill_color='blue')
            plot.add_layout(left_box)
        mid_box = BoxAnnotation(left=sunrise[i], right=sunset[i], fill_alpha=0.2, fill_color='yellow')
        plot.add_layout(mid_box)
    left_outer_box = BoxAnnotation(right=sunrise[0], fill_alpha=0.2, fill_color='blue')
    plot.add_layout(left_outer_box)
    right_outer_box = BoxAnnotation(left=sunset[len(sunrise)-1], fill_alpha=0.2, fill_color='blue')
    plot.add_layout(right_outer_box)

    #plot.yaxis.visible = False
    #ticker = SingleIntervalTicker(interval=ytick_interval)
    #yaxis = LinearAxis(ticker=ticker)
    #plot.add_layout(yaxis, 'left')
    
    plot_script, plot_div = components(plot)
    
    return plot_script, plot_div
    
    
def plot_pollution(df, mobile, title, plot_width, plot_height, tools, pollution_type, locations, colors, plot_start, plot_end, ranges, y_hist):
    fig = figure(
                    title=title, \
                    plot_width=plot_width, \
                    plot_height=plot_height, \
                    x_axis_type="datetime", \
                    tools=tools
                )

    max = ranges[3]
    for location, color in zip(locations, colors):
        fig.line(df.index, df[('value', location, pollution_type)], line_width=1.5, color=color, muted_line_alpha=0.2, legend=(location if not mobile else None))
        df1 = df[df.index >= datetime.combine(date.today(), time()) - timedelta(y_hist)]
        temp_max = df1[('value', location, pollution_type)].max()
        max = (temp_max if temp_max > max else max)


    fig.y_range = Range1d(0, max)
    fig.x_range = Range1d(plot_start, plot_end)
    fig.toolbar.logo=None
    fig.toolbar_location=("above")
    fig.legend.location = "top_left"
    fig.legend.click_policy="mute"

    # Add color scale
    colors = ['green','lightgreen','yellow','orange','orangered','red']
    for bottom, top, color in zip(ranges[1:], ranges[:-1], colors):
        box = BoxAnnotation(bottom=bottom, top=top, fill_alpha=0.3, fill_color=color)
        fig.add_layout(box)

    script, div = components(fig)
    return script, div
    
