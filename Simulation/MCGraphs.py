import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import io
import base64


mpl.use('Agg')
plt.style.use('ggplot')


def plot_graphs(fd_output, dd_output, ss_output, sss_output, inv_output, inf_output, sd_output, cola_output, sd):
    for year in range(fd_output.shape[0]):
        fd_output[year].sort()
        dd_output[year].sort()
        ss_output[year].sort()
        sss_output[year].sort()
        inv_output[year].sort()
        inf_output[year].sort()
        sd_output[year].sort()
        cola_output[year].sort()
    plot_url = []
    plot_url.append(plot_final_value_histogram(fd_output, sd))
    plot_url.append(plot_confidence_bands(sd.num_exp, year, fd_output,
                          'Year',
                          'Portfolio value($1,000)',
                          'Outcome percentiles by year'))
    plot_url.append(plot_confidence_bands(sd.num_exp, year, dd_output,
                          'Year',
                          'Drawdown',
                          'Drawdown percentiles by year'))
    plot_url.append(plot_confidence_bands(sd.num_exp, year, ss_output,
                          'Year',
                          'Primary user social security',
                          'Social security percentiles by year (primary user)'))
    plot_url.append(plot_confidence_bands(sd.num_exp, year, sss_output,
                          'Year',
                          'Spouse social security',
                          'Social security percentiles by year (spouse)'))
    plot_url.append(plot_confidence_bands(sd.num_exp, year, inv_output,
                          'Year',
                          'Investment returns',
                          'Investment returns percentiles by year'))
    plot_url.append(plot_confidence_bands(sd.num_exp, year, inf_output,
                          'Year',
                          'Inflation',
                          'Inflation percentiles by year'))
    plot_url.append(plot_confidence_bands(sd.num_exp, year, sd_output,
                          'Year',
                          'Spend decay',
                          'Spend decay percentiles by year'))
    plot_url.append(plot_confidence_bands(sd.num_exp, year, cola_output,
                          'Year',
                          'Cola',
                          'Cola percentiles by year'))
    return plot_url


def plot_final_value_histogram(fd_output, sd):
    img = io.BytesIO()

    plt.figure(figsize=(8, 6.5))
    plt.tight_layout()

    # Don't display the top 5% because they are part of a "long tail" and mess up the visuals; Leave min at 0
    min_index = 0
    max_index = int(0.95 * sd.num_exp) - 1

    # Now create figure 1 - the  distribution of all results.
    # NB: The x axis has the final dollar amount of the simulations and the y axis has the experiment count
    year = fd_output.shape[0] - 1  # index of the year to graph, i.e. the final year of the simulation

    xmin = fd_output[year][min_index]  # This is the min that we will graph
    xmax = fd_output[year][max_index]  # This is the max that we will graph
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
    for i in np.arange(len(fd_output[year])):
        if fd_output[year][i] == 0:
            z_count += 1

    # Since we don't plot the top 5% of results, we will consider the
    # results to be "all zero" if > 95% of the results are zero
    all_zeros = False
    if z_count > 0.95*len(fd_output[year]):
        all_zeros = True

    if not all_zeros:
        n, arr, patches = plt.hist(fd_output[year], bins=bins)
    else:
        # Clean up the few, remaining non-zero results
        for i in np.arange(len(fd_output[year])):
            fd_output[year][i] = 0
        n, arr, patches = plt.hist(fd_output[year], bins=bins)

    ax.set_title('Year {year:.0f}'.format(year=year))

    ypos = n[np.argmax(n)]  # Y position of the bin with the maximum count

    # These are the logical coordinates of the y axis - the count of the number of experiments in a single bin
    ymin = 0
    ymax = n[np.argmax(n)]
    ylen = ymax - ymin

    yinc = ylen / 32  # Determined empirically, based on font and graph size

    # Put a line for the mode and label it. Note that we drop the leading bucket, which is frequently zeros
    mode = arr[np.argmax(n)]
    plt.axvline(mode + binsize / 2, color='k', linestyle='solid', linewidth=1)  # Mode
    plt.text(mode + xlen / 50, ypos, 'Mode: ${0:,.0f}'.format(mode), color='k')

    # Put a line for the median and label it
    med = fd_output[year][int(sd.num_exp / 2)]
    plt.axvline(med + binsize / 2, color='g', linestyle='solid', linewidth=1)
    plt.text(med + xlen / 50, ypos - yinc, 'Median: ${0:,.0f}'.format(med), color='g')

    # Put a line for the average and label it
    avg = sum(fd_output[year]) / sd.num_exp
    plt.axvline(avg + binsize / 2, color='b', linestyle='solid', linewidth=1)  # Mean
    plt.text(avg + xlen / 50, ypos - 2 * yinc, 'Average: ${0:,.0f}'.format(avg), color='b')

    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    return plot_url


def plot_confidence_bands(num_exp, year, output, x_label, y_label, title):
    img = io.BytesIO()
    plt.figure(figsize=(8, 6.5))
    plt.gcf().subplots_adjust(left=0.15)  # Prevents the cut off of the y axis label (mfm)

    two_pct = output[:, int(0.98 * num_exp)]
    fiv_pct = output[:, int(0.95 * num_exp)]
    ten_pct = output[:, int(0.9 * num_exp)]
    t5_pct = output[:, int(0.75 * num_exp)]
    fif_pct = output[:, int(0.5 * num_exp)]
    s5_pct = output[:, int(0.25 * num_exp)]
    nt_pct = output[:, int(0.1 * num_exp)]
    n5_pct = output[:, int(0.05 * num_exp)]
    n8_pct = output[:, int(0.02 * num_exp)]

    ymax = 1.02 * max(two_pct.max(), fiv_pct.max(), ten_pct.max(), t5_pct.max(), fif_pct.max(), s5_pct.max(),
                      nt_pct.max(), n5_pct.max(), n8_pct.max())
    if ymax > 10:
        ymin = 0
    else:
        ymin = min(two_pct.min(), fiv_pct.min(), ten_pct.min(), t5_pct.min(), fif_pct.min(), s5_pct.min(),
                          nt_pct.min(), n5_pct.min(), n8_pct.min())
    plt.ylim(ymin, ymax)
    plt.xlim(0, year)

    # Format the x axis so it shows normal number format with commas (not scientific notation)
    ax = plt.gca()
    if ymax > 10:
        ax.get_xaxis().set_major_formatter(
            mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

        ax.get_yaxis().set_major_formatter(
            mpl.ticker.FuncFormatter(lambda y, p: format(int(y), ',')))

    line0 = ax.plot(two_pct, marker='o', markerfacecolor='black', color='black', markersize=1, linewidth=1, label="2%")
    line1 = ax.plot(fiv_pct, marker='o', markerfacecolor='brown', color='brown', markersize=1, linewidth=1, label="5%")
    line2, = ax.plot(ten_pct, marker='o', markerfacecolor='purple', color='purple', markersize=1, linewidth=1, label="10%")
    line3, = ax.plot(t5_pct, marker='o', markerfacecolor='blue', color='blue', markersize=1, linewidth=1, label="25%")
    line4, = ax.plot(fif_pct, marker='o', markerfacecolor='green', color='green', markersize=1, linewidth=1, label="50%")
    line5, = ax.plot(s5_pct, marker='o', markerfacecolor='olive', color='olive', markersize=1, linewidth=1, label="25%")
    line6, = ax.plot(nt_pct, marker='o', markerfacecolor='pink', color='pink', markersize=1, linewidth=1, label="10%")
    line7, = ax.plot(n5_pct, marker='o', markerfacecolor='orange', color='orange', markersize=1, linewidth=1, label="5%")
    line8, = ax.plot(n8_pct, marker='o', markerfacecolor='red', color='red', markersize=1, linewidth=1, label="2%")

    ax.legend((line0, line1, line2, line3, line4, line5, line6, line7, line8), ('2%', '5%', '10%', '25%', '50%', '75%', '90%', '95%', '98%'))

    vert_range = ymax - ymin  # Y axis range
    yinc = vert_range / 24  # space between legend entries, determined empirically
    fudge_factor = .003*vert_range
    if fiv_pct[3] > (ymax - 0.5 * ymax):
        #  Plotted lines emanate from the upper left, so place the legend in the lower left
        leg = ax.legend(loc='lower left')
        y_start = (ymin + 9 * yinc) - 3*fudge_factor
    else:
        leg = ax.legend(loc='upper left')
        y_start = ymin + vert_range - yinc - 2*fudge_factor
    if ymax < 10:
        funcstr = '${0:,.3f}'
    else:
        funcstr = '${0:,.0f}'
#    plt.gcf().canvas.draw()
#    p = leg.get_window_extent()
#    y_start = p.max[0]
    # Plot the final fd_outputs next to the legend entries
    plt.text((year / 6.9), y_start - 0 * yinc, funcstr.format(two_pct[year]), color='black')
    plt.text((year / 6.9), y_start - 1 * yinc, funcstr.format(fiv_pct[year]), color='brown')
    plt.text((year / 6.9), y_start - 2 * yinc, funcstr.format(ten_pct[year]), color='purple')
    plt.text((year / 6.9), y_start - 3 * yinc, funcstr.format(t5_pct[year]), color='blue')
    plt.text((year / 6.9), y_start - 4 * yinc, funcstr.format(fif_pct[year]), color='green')
    plt.text((year / 6.9), y_start - 5 * yinc, funcstr.format(s5_pct[year]), color='olive')
    plt.text((year / 6.9), y_start - 6 * yinc, funcstr.format(nt_pct[year]), color='pink')
    plt.text((year / 6.9), y_start - 7 * yinc, funcstr.format(n5_pct[year]), color='orange')
    plt.text((year / 6.9), y_start - 8 * yinc, funcstr.format(n8_pct[year]), color='red')

    plt.xlabel(x_label)
    plt.ylabel(y_label)

    ax.set_title(title)

    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    return plot_url
