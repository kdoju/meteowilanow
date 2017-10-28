from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter, SingleIntervalTicker, LinearAxis
from bokeh.models import Range1d, Label, BoxAnnotation, Grid
#import sun_info

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
    tools = ['pan','xwheel_zoom','box_zoom','ywheel_zoom','resize','reset'],
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
    
    
