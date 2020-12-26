import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import io
import base64


mpl.use('Agg')
plt.style.use('ggplot')


def plot_graphs(fd_output, dd_output, ss_output, sss_output, inv_output, inf_output, sd_output, cola_output, p0_output, sd):
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
    plot_url.append(plot_p0(p0_output))
    plot_url.append(plot_confidence_bands(sd, year, fd_output,
                          'Year',
                          'Portfolio value($1,000)',
                          'Outcome percentiles by year'))
    plot_url.append(plot_confidence_bands(sd, year, dd_output,
                          'Year',
                          'Drawdown',
                          'Drawdown percentiles by year'))
    plot_url.append(plot_confidence_bands(sd, year, ss_output,
                          'Year',
                          'Primary user social security',
                          'Social security percentiles by year (primary user)'))
    plot_url.append(plot_confidence_bands(sd, year, sss_output,
                          'Year',
                          'Spouse social security',
                          'Social security percentiles by year (spouse)'))

    if sd.debug:
        plot_url.append(plot_confidence_bands(sd, year, inv_output,
                          'Year',
                          'Investment returns',
                          'Investment returns percentiles by year'))
        plot_url.append(plot_confidence_bands(sd, year, inf_output,
                              'Year',
                              'Inflation',
                              'Inflation percentiles by year'))
        plot_url.append(plot_confidence_bands(sd, year, sd_output,
                              'Year',
                              'Spend decay',
                              'Spend decay percentiles by year'))
        plot_url.append(plot_confidence_bands(sd, year, cola_output,
                              'Year',
                              'Cola',
                              'Cola percentiles by year'))
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

    markevery = int(n_yrs/6)  # Label 6 points, equally spaced horizontally
    ax.plot(p0_output, marker='o', markerfacecolor='black', color='black', markersize=1, linewidth=1, markevery=markevery)
    x = np.arange(0, n_yrs, 1)
#    ax.fill_between(x, 0, p0_output, color='blue')
    xy = tuple(zip(x, p0_output))
    i = 0
    while i < len(p0_output):
        ax.annotate('%.2f' % xy[i][1], xy=xy[i], xytext=(0, 7), textcoords='offset pixels')
        i += markevery
    if i != len(p0_output) - 1 + markevery:
        i = len(p0_output) - 1
        ax.annotate('%.2f' % xy[i][1], xy=xy[i], xytext=(5, -4), textcoords='offset pixels')

    plt.xlabel("Year")
    plt.ylabel('Percent over 0')
    ax.set_title('Probability of NOT running out of money, by year')

    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
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


def plot_confidence_bands(sd, year, output, x_label, y_label, title):
    img = io.BytesIO()
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
    if ymax > 10:
        ymin = 0
    else:
        if sd.debug:
            ymin = min(tsdlow_pct.min(), fiv_pct.min(), ten_pct.min(), t5_pct.min(), fif_pct.min(), s5_pct.min(),
                          nt_pct.min(), n77_pct.min(), tsdhigh.min())
        else:
            ymin = min(fiv_pct.min(), ten_pct.min(), t5_pct.min(), fif_pct.min(), s5_pct.min(),
                       nt_pct.min(), n77_pct.min())
    plt.ylim(ymin, ymax)
    plt.xlim(0, year)

    # Format the x axis so it shows normal number format with commas (not scientific notation)
    ax = plt.gca()
    if ymax > 10:
        ax.get_xaxis().set_major_formatter(
            mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

        ax.get_yaxis().set_major_formatter(
            mpl.ticker.FuncFormatter(lambda y, p: format(int(y), ',')))

    if sd.debug:
        line0 = ax.plot(tsdlow_pct, marker='o', markerfacecolor='black', color='black', markersize=1, linewidth=1, label="2sd")
    line1 = ax.plot(fiv_pct, marker='o', markerfacecolor='brown', color='brown', markersize=1, linewidth=1, label="5%")
    line2 = ax.plot(ten_pct, marker='o', markerfacecolor='purple', color='purple', markersize=1, linewidth=1, label="10%")
    line3 = ax.plot(t5_pct, marker='o', markerfacecolor='blue', color='blue', markersize=1, linewidth=1, label="25%")
    line4 = ax.plot(fif_pct, marker='o', markerfacecolor='green', color='green', markersize=1, linewidth=1, label="50%")
    line5 = ax.plot(s5_pct, marker='o', markerfacecolor='olive', color='olive', markersize=1, linewidth=1, label="25%")
    line6 = ax.plot(nt_pct, marker='o', markerfacecolor='pink', color='pink', markersize=1, linewidth=1, label="10%")
    line7 = ax.plot(n77_pct, marker='o', markerfacecolor='orange', color='orange', markersize=1, linewidth=1, label="5%")
    if sd.debug:
        line8 = ax.plot(tsdhigh, marker='o', markerfacecolor='red', color='red', markersize=1, linewidth=1, label="2sd")

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
        funcstr = '${0:,.3f}'
    else:
        funcstr = '${0:,.0f}'

    # Plot the final fd_outputs next to the legend entries
    n = 0
    if sd.debug:
        plt.text((year / 6.9), y_start - n * yinc, funcstr.format(tsdlow_pct[year]), color='black')
        n += 1
    plt.text((year / 6.9), y_start - n * yinc, funcstr.format(fiv_pct[year]), color='brown')
    n += 1
    plt.text((year / 6.9), y_start - n * yinc, funcstr.format(ten_pct[year]), color='purple')
    n += 1
    plt.text((year / 6.9), y_start - n * yinc, funcstr.format(t5_pct[year]), color='blue')
    n += 1
    plt.text((year / 6.9), y_start - n * yinc, funcstr.format(fif_pct[year]), color='green')
    n += 1
    plt.text((year / 6.9), y_start - n * yinc, funcstr.format(s5_pct[year]), color='olive')
    n += 1
    plt.text((year / 6.9), y_start - n * yinc, funcstr.format(nt_pct[year]), color='pink')
    n += 1
    plt.text((year / 6.9), y_start - n * yinc, funcstr.format(n77_pct[year]), color='orange')
    n += 1
    if sd.debug:
        plt.text((year / 6.9), y_start - n * yinc, funcstr.format(tsdhigh[year]), color='red')

    plt.xlabel(x_label)
    plt.ylabel(y_label)

    ax.set_title(title)

    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    return plot_url
