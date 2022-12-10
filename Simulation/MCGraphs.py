import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import io
import base64
from Simulation.models import SimData


mpl.use('Agg')
plt.style.use('ggplot')


def plot_graphs(fd_output, rs_output, ss_output, sss_output,
                inv_output, inf_output, sd_output, cola_output, p0_output, has_spouse):

    sd = SimData.query.first()
    # The number of years in the simulation
    years = fd_output.shape[0]
    for year in range(years):
        fd_output[year].sort()
        rs_output[year].sort()
        ss_output[year].sort()
        sss_output[year].sort()

    if sd.debug:
        # These arrays have one less year than the primary output arrays
        for year in range(years-1):
            inv_output[year].sort()
            inf_output[year].sort()
            sd_output[year].sort()
            cola_output[year].sort()
    plot_url = []
    plot_url.append(plot_final_value_histogram(fd_output))
    plot_url.append(plot_p0(p0_output))
    plot_url.append(plot_confidence_bands(years-1, fd_output,
                          'Year',
                          'Portfolio value($1,000)',
                          'Outcome percentiles by year',
                          '$'))
    plot_url.append(plot_confidence_bands(years-1, rs_output,
                          'Year',
                          'Retirement spend',
                          'Retirement spend percentiles by year',
                          '$'))
    plot_url.append(plot_confidence_bands(years-1, ss_output,
                          'Year',
                          'Primary user social security',
                          'Social security percentiles by year (primary user)',
                          '$'))
    if has_spouse:
        plot_url.append(plot_confidence_bands(years-1, sss_output,
                          'Year',
                          'Spouse social security',
                          'Social security percentiles by year (spouse)',
                          '$'))

    if sd.debug:
        plot_url.append(plot_confidence_bands(years-2, inv_output*100,
                          'Year',
                          'Investment returns(%)',
                          'Investment returns percentiles by year',
                          '%'))
        plot_url.append(plot_confidence_bands(years-2, inf_output*100,
                              'Year',
                              'Inflation (%)',
                              'Inflation percentiles by year',
                              '%'))
        plot_url.append(plot_confidence_bands(years-2, sd_output*100,
                              'Year',
                              'Spend decay (%)',
                              'Spend decay percentiles by year',
                              '%'))
        plot_url.append(plot_confidence_bands(years-2, cola_output*100,
                              'Year',
                              'Cola (%)',
                              'Cola percentiles by year',
                              '%'))
    return plot_url

def plot_p0(p0_output):
    img = io.BytesIO()

    plt.figure(figsize=(8, 6.5))
    plt.tight_layout()

    n_yrs = p0_output.shape[0]

    ax = plt.gca()

    ax.get_xaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax.get_xaxis().set_major_locator(plt.MaxNLocator(5))

    plt.ylim(0, 105)

    markevery = int(n_yrs/6)  # Label 6 points, equally spaced horizontally
    ax.plot(p0_output, marker='o', markerfacecolor='black', color='black', markersize=1, linewidth=1, markevery=markevery)

    x = np.arange(0, n_yrs, 1)
    ax.fill_between(x, 0, p0_output, color='blue')

    xy = tuple(zip(x, p0_output))
    i = 0
    while i < len(p0_output):
        ax.annotate('%.2f' % xy[i][1], xy=xy[i], xytext=(0, 7), textcoords='offset pixels')
        i += markevery

    # If the last annotation does not happen to be the last point, annotate the last point
    if i != len(p0_output) - 1 + markevery:
        i = len(p0_output) - 1
        ax.annotate('%.2f' % xy[i][1], xy=xy[i], xytext=(5, -4), textcoords='offset pixels')

    plt.xlabel("Year")
    plt.ylabel('Percent over 0')
    ax.set_title('Probability of outliving your money, by year')

    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    return plot_url


def plot_final_value_histogram(fd_output):
    img = io.BytesIO()

    sd = SimData.query.first()

    plt.figure(figsize=(8, 6.5))
    plt.tight_layout()

    year = fd_output.shape[0] - 1  # index of the year to graph, i.e. the final year of the simulation

    # fd_last contains the data for the last year of the simulation. It will contain num_exp data points
    fd_last = fd_output[year]

    # Don't display the top 2% because they are part of a "long tail" and mess up the visuals; Leave min at 0
    max_index = int(0.98 * sd.num_exp) - 1
    min_index = 0

    # Now create figure 1 - the  distribution of the results for the final year of the simulation.
    # NB: The x axis has the final dollar amount of the simulations and the y axis has the experiment count
    xmin = fd_last[min_index]  # This is the min that we will graph
    xmax = fd_last[max_index]  # This is the max that we will graph
    xlen = xmax - xmin

    # This is to keep np.arange from crashing if xmax is too small. It also causes the mode/mean/median labels to
    # be positioned correctly relative to their vertical lines
    if xmax < sd.num_sim_bins:
        xmax = sd.num_sim_bins
        xlen = xmax-xmin
    binsize = (xmax - xmin) / sd.num_sim_bins
    bins = np.arange(xmin, xmax, binsize)

    plt.xlim(xmin, xmax)

    # Format the x axis so it shows normal number format with commas (not scientific notation)
    ax = plt.gca()

    ax.get_xaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax.get_xaxis().set_major_locator(plt.MaxNLocator(5))

    plt.xlabel('Final portfolio value')
    plt.ylabel('Experiment count')

    # Count zeros. We will throw out the zero results when plotting the histogram
    z_count = 0
    for i in np.arange(len(fd_last)):
        if fd_last[i] == 0:
            z_count += 1

    # Since we don't plot the top 2% of results, we will consider the
    # results to be "all zero" if > 95% of the results are zero
    all_zeros = False
    if z_count > 0.98*len(fd_last):
        all_zeros = True

    if not all_zeros:
        n, arr, patches = plt.hist(fd_last, bins=bins)
    else:
        # Clean up the few, remaining non-zero results
        for i in np.arange(len(fd_last)):
            fd_last[i] = 0
        n, arr, patches = plt.hist(fd_last, bins=bins)

    ax.set_title('Year {year:.0f}'.format(year=year))

    ypos = n[np.argmax(n)]  # Y position of the bin with the maximum count

    # These are the logical coordinates of the y axis - the count of the number of experiments in a single bin
    ymin = 0
    ymax = n[np.argmax(n)]
    ylen = ymax - ymin

    yinc = ylen / 32  # Determined empirically, based on font and graph size

    # Put a line for the mode and label it.
    mode = arr[np.argmax(n)]
    plt.axvline(mode + binsize / 2, color='k', linestyle='solid', linewidth=1)  # Mode
    plt.text(mode + xlen / 50, ypos, 'Mode: ${0:,.0f}'.format(mode), color='k')

    # Put a line for the median and label it
    med = fd_last[int(sd.num_exp / 2)]
    plt.axvline(med + binsize / 2, color='g', linestyle='solid', linewidth=1)
    plt.text(med + xlen / 50, ypos - yinc, 'Median: ${0:,.0f}'.format(med), color='g')

    # Put a line for the average and label it
    avg = sum(fd_last) / sd.num_exp
    plt.axvline(avg + binsize / 2, color='b', linestyle='solid', linewidth=1)  # Mean
    plt.text(avg + xlen / 50, ypos - 2 * yinc, 'Average: ${0:,.0f}'.format(avg), color='b')

    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    return plot_url


def plot_confidence_bands(year, output, x_label, y_label, title, unit):
    img = io.BytesIO()
    sd = SimData.query.first()
    plt.figure(figsize=(8, 6.5))
    plt.gcf().subplots_adjust(left=0.15)  # Prevents the cut off of the y axis label (mfm)

    if sd.debug:
        tsdlow_pct = output[:, int(0.977 * sd.num_exp)]
    fiv_pct = output[:, int(0.95 * sd.num_exp)]
    ten_pct = output[:, int(0.9 * sd.num_exp)]
    t5_pct = output[:, int(0.75 * sd.num_exp)]
    fif_pct = output[:, int(0.5 * sd.num_exp)]
    s5_pct = output[:, int(0.25 * sd.num_exp)]
    nt_pct = output[:, int(0.1 * sd.num_exp)]
    n77_pct = output[:, int(0.05 * sd.num_exp)]
    if sd.debug:
        tsdhigh = output[:, int(0.023 * sd.num_exp)]

    if sd.debug:
        ymax = 1.02 * max(tsdlow_pct.max(), fiv_pct.max(), ten_pct.max(), t5_pct.max(), fif_pct.max(), s5_pct.max(),
                      nt_pct.max(), n77_pct.max(), tsdhigh.max())
    else:
        ymax = 1.02 * max(fiv_pct.max(), ten_pct.max(), t5_pct.max(), fif_pct.max(), s5_pct.max(),
                          nt_pct.max(), n77_pct.max())
    if sd.debug:
        ymin = min(tsdlow_pct.min(), fiv_pct.min(), ten_pct.min(), t5_pct.min(), fif_pct.min(), s5_pct.min(),
                      nt_pct.min(), n77_pct.min(), tsdhigh.min())
    else:
        ymin = min(fiv_pct.min(), ten_pct.min(), t5_pct.min(), fif_pct.min(), s5_pct.min(),
                   nt_pct.min(), n77_pct.min())
    if ymin > 0:
        ymin *= 0.95
    else:
        ymin *= 1.05
    if ymin == ymax:
        ymax = ymin + 100
    plt.ylim(ymin, ymax)
    plt.xlim(0, year)

    # Format the x axis so it shows normal number format with commas (not scientific notation)
    ax = plt.gca()
    if ymax > 10:
        ax.get_xaxis().set_major_formatter(
            mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

        ax.get_yaxis().set_major_formatter(
            mpl.ticker.FuncFormatter(lambda y, p: format(int(y), ',')))

    # NB: The commas after each line assignment are required because ax.plot returns a tuple of line objects
    # Without the commas, a lot of warnings are generated
    # Explanation here: https://stackoverflow.com/questions/11983024/matplotlib-legends-not-working
    if sd.debug:
        line0, = ax.plot(tsdlow_pct, marker='o', markerfacecolor='black', color='black', markersize=1, linewidth=1, label="2sd")
    line1, = ax.plot(fiv_pct, marker='o', markerfacecolor='brown', color='brown', markersize=1, linewidth=1, label="5%")
    line2, = ax.plot(ten_pct, marker='o', markerfacecolor='purple', color='purple', markersize=1, linewidth=1, label="10%")
    line3, = ax.plot(t5_pct, marker='o', markerfacecolor='blue', color='blue', markersize=1, linewidth=1, label="25%")
    line4, = ax.plot(fif_pct, marker='o', markerfacecolor='green', color='green', markersize=1, linewidth=1, label="50%")
    line5, = ax.plot(s5_pct, marker='o', markerfacecolor='olive', color='olive', markersize=1, linewidth=1, label="25%")
    line6, = ax.plot(nt_pct, marker='o', markerfacecolor='pink', color='pink', markersize=1, linewidth=1, label="10%")
    line7, = ax.plot(n77_pct, marker='o', markerfacecolor='orange', color='orange', markersize=1, linewidth=1, label="5%")
    if sd.debug:
        line8, = ax.plot(tsdhigh, marker='o', markerfacecolor='red', color='red', markersize=1, linewidth=1, label="2sd")

    if sd.debug:
        ax.legend((line0, line1, line2, line3, line4, line5, line6, line7, line8), ('2sd', '5%', '10%', '25%', '50%', '75%', '90%', '95%', '2sd'))
    else:
        ax.legend((line1, line2, line3, line4, line5, line6, line7),
                  ('5%', '10%', '25%', '50%', '75%', '90%', '95%'))
    vert_range = ymax - ymin  # Y axis range
    yinc = vert_range / 24  # space between legend entries, determined empirically
    fudge_factor = .003*vert_range
    if fiv_pct[3] > (ymax - 0.5 * ymax):
        #  Plotted lines emanate from the upper left, so place the legend in the lower left
        ax.legend(loc='lower left')
        if sd.debug:
            y_start = (ymin + 9 * yinc) - 3*fudge_factor
        else:
            y_start = (ymin + 7 * yinc) - 3 * fudge_factor
    else:
        ax.legend(loc='upper left')
        y_start = ymin + vert_range - yinc - 2*fudge_factor
    if ymax < 10:
        if unit == '$':
            funcstr = '{0}{1:,.2f}'
        else:
            funcstr = '{1:,.2f}{0}'
    else:
        if unit == '$':
            funcstr = '{0}{1:,.0f}'
        else:
            funcstr = '{1:,.2f}{0}'

    # Plot the final fd_outputs next to the legend entries
    n = 0
    if sd.debug:
        plt.text((year / 6.9), y_start - n * yinc, funcstr.format(unit, tsdlow_pct[year]), color='black')
        n += 1
    plt.text((year / 6.9), y_start - n * yinc, funcstr.format(unit, fiv_pct[year]), color='brown')
    n += 1
    plt.text((year / 6.9), y_start - n * yinc, funcstr.format(unit, ten_pct[year]), color='purple')
    n += 1
    plt.text((year / 6.9), y_start - n * yinc, funcstr.format(unit, t5_pct[year]), color='blue')
    n += 1
    plt.text((year / 6.9), y_start - n * yinc, funcstr.format(unit, fif_pct[year]), color='green')
    n += 1
    plt.text((year / 6.9), y_start - n * yinc, funcstr.format(unit, s5_pct[year]), color='olive')
    n += 1
    plt.text((year / 6.9), y_start - n * yinc, funcstr.format(unit, nt_pct[year]), color='pink')
    n += 1
    plt.text((year / 6.9), y_start - n * yinc, funcstr.format(unit, n77_pct[year]), color='orange')
    n += 1
    if sd.debug:
        plt.text((year / 6.9), y_start - n * yinc, funcstr.format(unit, tsdhigh[year]), color='red')

    plt.xlabel(x_label)
    plt.ylabel(y_label)

    ax.set_title(title)

    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    return plot_url
