from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import os
import pandas as pd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go

def read_in_and_concat_commits_history_dfs(foldername = 'commits_history'):

    '''
    reads in all commits history excel files and unionises them, outputting the concatenated table that is completely unaggregated
    '''
    
    # initialise empty array where each element will be one dataframe
    arr_commits_history_dfs = []

    # populate array
    for filename in sorted(os.listdir('./' + foldername)):
        temp_df = pd.read_excel(foldername + '/' + filename)
        arr_commits_history_dfs.append(temp_df)

    # concatenate (i.e., union all) dataframes in the same order the files appear in the directory
    all_commits_history_dfs = pd.concat(arr_commits_history_dfs)

    # output concatenated dataframe
    return(all_commits_history_dfs)

def global_filter(repo_list_file = 'exact_repo_names.txt', past_six_months_file = 'past_six_months.txt'):

    '''
    for sidebar to appear in the app
    outputs selected repo names and selected monthyears
    '''

    # repo_list_file contains list of repo names in ascending alphabetical order
    # past_six_months_file contains list of past six monthyears from current time not including the current monthyear in ascending order

    # sidebar for global filter
    with st.sidebar:

        # header of sidebar
        st.header('Filters')

        # retrieve list of repo names from text file exported from jupyter notebooks
        with open(repo_list_file, 'r') as repo_txt_file:
            repos_arr = [line.rstrip() for line in repo_txt_file]
        # choose first repo name in repos_arr, put in an array (so length is 1), if repos_arr exists, otherwise default_repo stores an empty array
        default_repo = [repos_arr[0]] if repos_arr else []

        # make list of past six monthyears excluding current monthyear in ascending order
        with open(past_six_months_file, 'r') as past_six_months_txt_file:
            monthyears_sorted = [line.rstrip() for line in past_six_months_txt_file]

        # multiselect dropdown for repo names, select from repos_arr and default is default_repo
        selected_repos = st.multiselect('Repo(s)', repos_arr, default = default_repo)
        # single select dropdown for monthyears, select from monthyears_sorted and default is latest month
        selected_month = st.selectbox('Month/Year', monthyears_sorted, index = len(monthyears_sorted) - 1)

    return selected_repos, selected_month

def globally_filtered_commits_history_dfs(ungrouped_df, selected_repos, selected_month):

    '''
    filters unaggregated (raw concatenated/unionised) df by sidebar filter selections
    outputs filtered (unaggregated) df of commit history
    '''

    # ungrouped_df is the output of read_in_and_concat_commits_history_dfs
    # selected_repos is the list of repos selected in the global filter sidebar
    # selected_month is the selected monthyear

    # filtered df by repo name(s) in sidebar
    # global selected_repos
    mask = ungrouped_df['repo'].isin(selected_repos) if selected_repos else True

    # intersection between repo(s)-filtered df and selected month-filtered df
    if selected_month:
        mask = mask & (ungrouped_df['committer_monthyear'] == selected_month)

    # filter input dataframe by mask and then return from this function
    filtered_commits_history_dfs = ungrouped_df.loc[mask].copy()

    return(filtered_commits_history_dfs)

def authors_commits_pie_chart(ungrouped_filtered_df):

    '''
    groups/aggregates the filtered unaggregated dataframe specifically for the pie chart
    creates the pie chart and returns it
    '''
    
    # ungrouped_filtered_df is the output of globally_filtered_commits_history_dfs, meaning it has been filtered by the sidebar options

    # group filtered df by counting each individual commit (node_id) and grouping by repo name, monthyear, and author email
    df_for_pie = (
        ungrouped_filtered_df[['repo', 'committer_monthyear', 'author_email', 'node_id']]
            .groupby(['repo', 'committer_monthyear', 'author_email'])
            .count()
            .rename(columns = {'node_id': 'count_of_commits'})
            .reset_index()
            .sort_values('committer_monthyear')
    )

    # pie chart for number of commits per author email
    fig = px.pie(df_for_pie, values = 'count_of_commits', names = 'author_email')

    return(fig)

def commits_history_pie_chart_visualisation(ungrouped_filtered_df):

    '''
    plots the pie chart in the app
    '''

    # ungrouped_filtered_df is the output of globally_filtered_commits_history_dfs

    # title of commits history pie chart visualisation
    st.write('Number of commits per commit author')

    if ungrouped_filtered_df.empty:
        st.info('No commits data for the current filter selection')
        return None
    
    # pie chart visualisation
    fig = authors_commits_pie_chart(ungrouped_filtered_df)

    # plotting pie chart figure
    st.plotly_chart(fig)

def for_12_kpi(raw_dfs, selected_repos, selected_month, n = 13):

    # outputs two numbers for past 12 months excluding current month KPI
    # outputs delta from the 12 months before the previous 12 months

    # raw_dfs is the table of concatenated dfs for commits history for the past 29 months 
    # raw_dfs = read_in_and_concat_commits_history_dfs(foldername = 'for_12_kpi')
    # selected_repos, selected_month = global_filter()

    # filter raw_dfs
    # create filter for repo(s)
    mask = raw_dfs['repo'].isin(selected_repos) if selected_repos else True

    # determine array of monthyears for filtering
    # ensure selected_month is an array
    clicked_month = [selected_month] if type(selected_month) != list else selected_month

    # initialise array for main kpi monthyears
    selection_for_mask = []
    for selected_monthyear in clicked_month:
        for offset in range(0, n - 1):
            monthyear_in_arr = (parse(selected_monthyear + ' 1') - relativedelta(months = offset)).strftime('%B %Y')
            if monthyear_in_arr not in selection_for_mask:
                selection_for_mask.append(monthyear_in_arr)
    # mask for past 12 months main kpi
    selection_for_mask = sorted(selection_for_mask, key = lambda s: pd.to_datetime(s))

    # get first element of main kpi's monthyears to work backwards for the next array
    start_for_selection_for_mask_delta = [selection_for_mask[0]]
    
    # initialise array for calculating second kpi monthyears
    selection_for_mask_delta = []
    for start_monthyear in start_for_selection_for_mask_delta:
        for offset in range(1, n):
            monthyear_for_delta_in_arr = (parse(start_monthyear + ' 1') - relativedelta(months = offset)).strftime('%B %Y')
            if monthyear_for_delta_in_arr not in selection_for_mask_delta:
                selection_for_mask_delta.append(monthyear_for_delta_in_arr)
    # mask for first 12 months of past 24 months in order to work out the delta which is the second number for YoY diff
    selection_for_mask_delta = sorted(selection_for_mask_delta, key = lambda s: pd.to_datetime(s))
    
    # create mask for filtering for main 12-month kpi
    mask_org = mask & raw_dfs['committer_monthyear'].isin(selection_for_mask)
    # filtered unaggregated raw_dfs for determining main 12-month kpi
    raw_dfs_12_main = raw_dfs.loc[mask_org].copy()
    # aggregate filtered table to work out previous 12-month commit count
    previous_12_main = raw_dfs_12_main['node_id'].count()

    # create mask for filtering for 12-month comparison number
    mask_delta = mask & raw_dfs['committer_monthyear'].isin(selection_for_mask_delta)
    # filtered unaggregated raw_dfs for determining 12-month comparison number
    raw_dfs_12_diff = raw_dfs.loc[mask_delta].copy()
    # aggregate filtered table to work out 12-month commit count prior to above 12 months
    previous_12_diff = raw_dfs_12_diff['node_id'].count()

    if previous_12_diff == 0:
        YoY_percentage = None
    else:
        # determine YoY % as second KPI
        YoY_percentage = ((previous_12_main - previous_12_diff)/previous_12_diff) * 100
        # format 2nd KPI to look appropriate on the dashboard
        YoY_percentage = float('{:.2f}'.format(YoY_percentage))
    
    # output main and YoY KPIs
    return(previous_12_main, YoY_percentage)

def kpi_12_visualisation(raw_dfs, selected_repos, selected_month, n):

    # get both kpi numbers
    main, YoY = for_12_kpi(raw_dfs, selected_repos, selected_month, n)

    # create actual visualisation
    s_or_p = ' month' if n == 2 else ' months'

    st.metric(label = 'Number of commits in past ' + str(n - 1) + s_or_p, value = main, delta = 'N/A' if YoY is None else str(YoY) + '%')

def top_5_authors_additions_table(ungrouped_filtered_df):

    '''
    shows the top 5 author emails by total additions in descending order
    also includes total deletions
    input df should already be filtered by sidebar
    '''

    st.write('Top 5 authors by total additions')

    if ungrouped_filtered_df.empty:
        st.info('No additions/deletions data for the current filter selection')
        return None
    
    df = ungrouped_filtered_df.copy()

    required_cols = ['author_email', 'additions', 'deletions']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Missing required column(s): {', '.join(missing_cols)}")
        return None
    
    df['additions'] = pd.to_numeric(df['additions'], errors = 'coerce').fillna(0)
    df['deletions'] = pd.to_numeric(df['deletions'], errors = 'coerce').fillna(0)

    top_5_df = (
        df.groupby('author_email', as_index = False)[['additions', 'deletions']]
            .sum()
            .sort_values(['additions', 'deletions'], ascending = [False, True])
            .head(5)
            .rename(columns = {
                'author_email': 'Author email',
                'additions': 'Additions',
                'deletions': 'Deletions'
            })
    )

    st.dataframe(top_5_df, use_container_width = True, hide_index = True)

def daily_additions_deletions_bar_chart_visualisation(ungrouped_filtered_df):

    '''
    Creates and plots a daily stacked bar chart of additions and deletions
    For each date:
    - additions stack upwards
    - deletions stack downwards
    - colours represent author_email
    ungrouped_filtered_df is the concatenated additions_and_deletions dfs that has been filtered by the sidebar
    '''

    st.write('Daily additions and deletions by commit author')

    # if the data frame is empty, meaning it has headers and no rows
    if ungrouped_filtered_df.empty:
        st.info('No additions/deletions data for the current filter selection')
        return
    
    # copy input df which is the filtered concatenated additions and deletions table
    df = ungrouped_filtered_df.copy()

    # ensure required columns exist
    # list of required columns
    required_cols = ['committer_date', 'author_email', 'additions', 'deletions']
    # only include columns from required_cols if they aren't in df
    missing_cols = [col for col in required_cols if col not in df.columns]
    # join the missing_cols items into a comma-separated list
    missing_cols_string = ', '.join(missing_cols)
    # if missing_cols isn't empty display an error message, which the function st.error does
    if missing_cols:
        st.error(f'Missing required column(s): {missing_cols_string}')
    
    # clean types
    # convert invalid dates to NaT (Not a Time)
    df['committer_date'] = pd.to_datetime(df['committer_date'], errors = 'coerce')
    # convert invalid numbers to NaN and replace with 0
    df['additions'] = pd.to_numeric(df['additions'], errors = 'coerce').fillna(0)
    df['deletions'] = pd.to_numeric(df['deletions'], errors = 'coerce').fillna(0)

    # remove rows with invalid dates
    df = df.dropna(subset = ['committer_date'])

    # if the previous operations result in df being empty, display info message
    if df.empty:
        st.info('No valid dated additions/deletions data for the current filter selection')
        return
    
    # aggregate to the exact granularity needed for the chart
    # group by committer_date first and then group the subgroups by author_email
    # sum the additions and deletions for each group
    grouped = (
        df.groupby(['committer_date', 'author_email'], as_index = False)[['additions', 'deletions']]
          .sum()
          .sort_values(['committer_date', 'author_email'])
    )

    # order authors by total absolute activity so the legend is more useful
    # activity is the new column which is a list which starts with the author_email with the most additions and deletions a
    author_order = (
        grouped.assign(activity = grouped['additions'].abs() + grouped['deletions'].abs())
               .groupby('author_email', as_index = False)['activity']
               .sum()
               .sort_values('activity', ascending = False)['author_email']
               .tolist()
    )

    # consistent colour per author
    # palette is the colour scheme (set of colours)
    # qualitative means discrete, not continuous
    palette = px.colors.qualitative.Plotly
    author_colours = {
        author: palette[i % len(palette)] for i, author in enumerate(author_order)
    }

    # create empty chart object and later add to it
    # create container
    fig = go.Figure()

    # iterate through authors who created the additions and deletions
    for author in author_order:
        # filter grouped data to just the current author
        author_df = grouped[grouped['author_email'] == author]

        # additions trace
        # add_trace() adds the additions visual layer to the figure
        fig.add_trace(
            # add one set of bars to the chart
            go.Bar(
                x = author_df['committer_date'],
                y = author_df['additions'],
                name = author, # label of the trace
                # legendgroup - create two traces per author (one for additions and one for deletions)
                # both traces are in the same legendgroup, so plotly treats them as belonging to the same author
                # so clicking on the author in the legend affects both traces together
                # legendgroup - groups traces so they behave as a unit in the legend
                legendgroup = author,
                # set bar colour from the author_colours dict
                marker_color = author_colours[author],
                # what the user sees when hovering over a bar
                hovertemplate = (
                    'Date: %{x|%Y-%m-%d}<br>' # show the x-value and the date and <br> means line break
                    f'Author: {author}<br>' # author email
                    'Additions: %{y}<extra></extra>' # shows the number of additions
                    # <extra></extra> removes the default extra plotly box that usually shows the trace name so the hover looks cleaner
                )
            )
        )

        # deletions trace
        fig.add_trace(
            go.Bar(
                x = author_df['committer_date'],
                y = author_df['deletions'],
                name = author,
                legendgroup = author,
                showlegend = False, # so two legends aren't shown, because both traces are part of the same legendgroup, so only the legend for one needs to be shown
                marker_color = author_colours[author],
                hovertemplate = (
                    'Date: %{x|%Y-%m-%d}<br>'
                    f'Author: {author}<br>'
                    'Deletions: %{y}<extra></extra>'
                )
            )
        )

    # change figure-wide settings
    # affects how the chart looks and behaves
    fig.update_layout(
        barmode = 'relative', # stack bar values relative to each other, positive and negative bars stack around the zero line
        xaxis_title = 'Date',
        yaxis_title = 'Lines changed',
        hovermode = 'x unified', # when you hover over a date, plotly shows one combined hover box for all traces
        legend_title = 'Author email',
        bargap = 0.15, # gaps between date groups
        # tells plotly the x-axis contains actual date values
        # so plotly can sort dates correctly
        # so plotly can format them like dates
        xaxis = dict(type = 'date'),
        # draw horizonal line at y = 0 <-- draws x-axis
        # make line 1 pixel thick
        yaxis = dict(zeroline = True, zerolinewidth = 1)
    )

    # render chart in app
    # stretch it to the container side
    st.plotly_chart(fig, use_container_width = True)

def pr_kpis(raw_dfs, selected_repos, selected_month, n):

    # outputs main numbers and deltas for kpis
    # number of prs opened in month range
    # number of prs merged in month range
    # number of prs closed in month range
    # number of prs opened and closed in the same month range
    # number of prs opened and left open in month range

    '''
    raw_dfs is the concatenated dataframe of all the dfs in the pull_requests folder
    selected_repos are the repos the user selects from the sidebar
    selected_month is the month the user selects from the sidebar
    n indicates the number of months to go backwards from the user-selected month to set the month range
    '''

    # create filter for repo(s)
    mask = raw_dfs['pr_target_branch_repo_name'].isin(selected_repos) if selected_repos else True

    # ensure selected_month is an array
    clicked_month = [selected_month] if type(selected_month) != list else selected_month

    # initialise array of monthyears for main kpi
    selection_for_mask = []
    for selected_monthyear in clicked_month:
        for offset in range(0, n - 1):
            # M YYYY format of monthyear offset months less than clicked_month
            monthyear_in_arr = (parse(selected_monthyear + ' 1') - relativedelta(months = offset)).strftime('%B %Y')
            if monthyear_in_arr not in selection_for_mask:
                selection_for_mask.append(monthyear_in_arr)

    # mask for unionised dataframe for main kpi
    selection_for_mask = sorted(selection_for_mask, key = lambda s: pd.to_datetime(s))

    # get first element of main kpi's monthyears to work backwards for array for comparison
    start_for_selection_for_mask_delta = [selection_for_mask[0]]

    # initialise array of monthyears for calculating comparison kpi
    selection_for_comparison_mask = []
    for start_monthyear in start_for_selection_for_mask_delta:
        for offset in range(1, n):
            # M YYYY format of monthyear offset months less than start_monthyear
            monthyear_in_delta_arr = (parse(start_monthyear + ' 1') - relativedelta(months = offset)).strftime('%B %Y')
            if monthyear_in_delta_arr not in selection_for_comparison_mask:
                selection_for_comparison_mask.append(monthyear_in_delta_arr)
    
    # mask for unionised dataframe for comparison
    selection_for_comparison_mask = sorted(selection_for_comparison_mask, key = lambda s: pd.to_datetime(s))

    # main: number of prs created
    # mask for main kpi number which is intersection of repo mask and monthyears mask
    main_mask_created_at = mask & raw_dfs['pr_created_at_monthyear'].isin(selection_for_mask)
    # use mask to filter unionised df
    main_raw_dfs_created_at = raw_dfs.loc[main_mask_created_at].copy()
    # calculate main kpi: number of prs created
    main_no_created_at = main_raw_dfs_created_at['pr_node_id'].count()

    # comparison: number of prs created
    # mask for comparison number which is intersection of repo mask and previous monthyears mask
    comp_mask_created_at = mask & raw_dfs['pr_created_at_monthyear'].isin(selection_for_comparison_mask)
    # use mask to filter unionised df
    comp_raw_dfs_created_at = raw_dfs.loc[comp_mask_created_at].copy()
    # calculate comparison number: number of prs created
    comp_no_created_at = comp_raw_dfs_created_at['pr_node_id'].count()

    if comp_no_created_at == 0:
        YoY_percentage_created_at = None
    else:
        # determine YoY % as second created_at KPI
        YoY_percentage_created_at = ((main_no_created_at - comp_no_created_at) / comp_no_created_at) * 100
        # format 2nd created_at KPI to look appropriate on the dashboard
        YoY_percentage_created_at = float('{:.2f}'.format(YoY_percentage_created_at))

    # main: number of prs merged
    # mask for main kpi number which is intersection of repo mask and monthyears mask
    main_mask_merged_at = mask & raw_dfs['pr_merged_at_monthyear'].isin(selection_for_mask)
    # use mask to filter unionised df
    main_raw_dfs_merged_at = raw_dfs.loc[main_mask_merged_at].copy()
    # calculate main kpi: number of prs merged
    main_no_merged_at = main_raw_dfs_merged_at['pr_node_id'].count()

    # comparison: number of prs merged
    # mask for comparison number which is intersection of repo mask and previous monthyears mask
    comp_mask_merged_at = mask & raw_dfs['pr_merged_at_monthyear'].isin(selection_for_comparison_mask)
    # use mask to filter unionised df
    comp_raw_dfs_merged_at = raw_dfs.loc[comp_mask_merged_at].copy()
    # calculate comparison number: number of prs merged
    comp_no_merged_at = comp_raw_dfs_merged_at['pr_node_id'].count()

    if comp_no_merged_at == 0:
        YoY_percentage_merged_at = None
    else:
        # determine YoY % as second merged_at KPI
        YoY_percentage_merged_at = ((main_no_merged_at - comp_no_merged_at) / comp_no_merged_at) * 100
        # format 2nd merged_at KPI to look appropriate on the dashboard
        YoY_percentage_merged_at = float('{:.2f}'.format(YoY_percentage_merged_at))

    # main: number of prs closed
    # mask for main kpi number which is intersection of repo mask and monthyears mask
    main_mask_closed_at = mask & raw_dfs['pr_closed_at_monthyear'].isin(selection_for_mask)
    # use mask to filter unionised df
    main_raw_dfs_closed_at = raw_dfs.loc[main_mask_closed_at].copy()
    # calculate main kpi: number of prs closed
    main_no_closed_at = main_raw_dfs_closed_at['pr_node_id'].count()

    # comparison: number of prs closed
    # mask for comparison number which is intersection of repo mask and previous monthyears mask
    comp_mask_closed_at = mask & raw_dfs['pr_closed_at_monthyear'].isin(selection_for_comparison_mask)
    # use mask to filter unionised df
    comp_raw_dfs_closed_at = raw_dfs.loc[comp_mask_closed_at].copy()
    # calculate comparison number: number of prs closed
    comp_no_closed_at = comp_raw_dfs_closed_at['pr_node_id'].count()

    if comp_no_closed_at == 0:
        YoY_percentage_closed_at = None
    else:
        # determine YoY % as second closed_at KPI
        YoY_percentage_closed_at = ((main_no_closed_at - comp_no_closed_at) / comp_no_closed_at) * 100
        # format 2nd closed_at KPI to look appropriate on the dashboard
        YoY_percentage_closed_at = float('{:.2f}'.format(YoY_percentage_closed_at))

    # main: number of prs opened and closed in same range
    # mask for main kpi number which is intersection of repo mask and monthyears mask
    main_mask_open_close = mask & raw_dfs['pr_created_at_monthyear'].isin(selection_for_mask) & raw_dfs['pr_closed_at_monthyear'].isin(selection_for_mask)
    # use mask to filter unionised df
    main_raw_dfs_open_close = raw_dfs.loc[main_mask_open_close].copy()
    # calculate main kpi: number of prs opened and closed in same range
    main_no_open_close = main_raw_dfs_open_close['pr_node_id'].count()

    # comparison: number of prs opened and closed in same range
    comp_mask_open_close = mask & raw_dfs['pr_created_at_monthyear'].isin(selection_for_comparison_mask) & raw_dfs['pr_closed_at_monthyear'].isin(selection_for_comparison_mask)
    # use mask to filter unionised df
    comp_raw_dfs_open_close = raw_dfs.loc[comp_mask_open_close].copy()
    # calculate comparison number: number of prs opened and closed in same range
    comp_no_open_close = comp_raw_dfs_open_close['pr_node_id'].count()

    if comp_no_open_close == 0:
        YoY_percentage_open_close = None
    else:
        # determine YoY % as second open and close KPI
        YoY_percentage_open_close = ((main_no_open_close - comp_no_open_close) / comp_no_open_close) * 100
        # format 2nd open and close KPI to look appropriate on the dashboard
        YoY_percentage_open_close = float('{:.2f}'.format(YoY_percentage_open_close))

    # main: number of prs opened and left open in same range
    # mask for main kpi number which is intersection of repo mask and monthyears masks: intersection of prs created in range and either the prs haven't been closed or they haven't been closed in the range
    main_mask_left_open = mask & raw_dfs['pr_created_at_monthyear'].isin(selection_for_mask) & (
        raw_dfs['pr_closed_at'].isna() | (~raw_dfs['pr_closed_at_monthyear'].isin(selection_for_mask))
    )
    # use mask to filter unionised df
    main_raw_dfs_left_open = raw_dfs.loc[main_mask_left_open].copy()
    # calculate main kpi: number of prs opened and left open in the same range
    main_no_left_open = main_raw_dfs_left_open['pr_node_id'].count()

    # comparison: number of prs opened and left open in same range
    comp_mask_left_open = mask & raw_dfs['pr_created_at_monthyear'].isin(selection_for_comparison_mask) & (
        raw_dfs['pr_closed_at'].isna() | (~raw_dfs['pr_closed_at_monthyear'].isin(selection_for_comparison_mask))
    )
    # use mask to filter unionised df
    comp_raw_dfs_left_open = raw_dfs.loc[comp_mask_left_open].copy()
    # calculate comparison number: number of prs opened and left open in same range
    comp_no_left_open = comp_raw_dfs_left_open['pr_node_id'].count()

    if comp_no_left_open == 0:
        YoY_percentage_left_open = None
    else:
        # determines YoY % as second left open KPI
        YoY_percentage_left_open = ((main_no_left_open - comp_no_left_open) / comp_no_left_open) * 100
        # format 2nd left open KPI to look appropriate on the dashboard
        YoY_percentage_left_open = float('{:.2f}'.format(YoY_percentage_left_open))

    return(
        [
            (main_no_created_at, YoY_percentage_created_at, n),
            (main_no_merged_at, YoY_percentage_merged_at, n),
            (main_no_closed_at, YoY_percentage_closed_at, n),
            (main_no_open_close, YoY_percentage_open_close, n),
            (main_no_left_open, YoY_percentage_left_open, n)
        ]
    )

def display_pr_kpis(kpi_arr):

    '''
    code for displaying the kpis from function pr_kpis
    '''

    col1, col2, col3, col4, col5 = st.columns(5)

    s_or_p = ['month' if tup[2] == 2 else 'months' for tup in kpi_arr]

    with col1:
        st.metric(label = 'number of prs created this month', value = kpi_arr[0][0], delta = 'N/A' if kpi_arr[0][1] is None else str(kpi_arr[0][1]) + '%')
    
    with col2:
        st.metric(label = 'number of prs merged this month', value = kpi_arr[1][0], delta = 'N/A' if kpi_arr[1][1] is None else str(kpi_arr[1][1]) + '%')

    with col3:
        st.metric(label = 'number of prs closed this month', value = kpi_arr[2][0], delta = 'N/A' if kpi_arr[2][1] is None else str(kpi_arr[2][1]) + '%')
    
    with col4:
        st.metric(label = 'number of prs opened and closed this month', value = kpi_arr[3][0], delta = 'N/A' if kpi_arr[3][1] is None else str(kpi_arr[3][1]) + '%')

    with col5:
        st.metric(label = 'number of prs opened and left open this month', value = kpi_arr[4][0], delta = 'N/A' if kpi_arr[4][1] is None else str(kpi_arr[4][1]) + '%')

def time_to_conclude_distributions(raw_dfs, selected_repos, selected_month):

    '''
    2 box-plots
    - created to closed
    - created to merged
    '''

    st.write('Time to conclude pull requests')

    df = raw_dfs.copy()

    required_cols = [
        'pr_target_branch_repo_name',
        'pr_created_at',
        'pr_closed_at',
        'pr_merged_at',
        'pr_created_at_monthyear'
    ]

    # error message in case any of the tables are missing the required columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Missing required column(s): {', '.join(missing_cols)}")
        return None
    
    # repo filter
    repo_filter = df['pr_target_branch_repo_name'].isin(selected_repos) if selected_repos else True

    # month and repo filter
    # this means the box plot will represent time-to-merge and time-to-close times for prs opened in the selected month
    if selected_month:
        mask = repo_filter & (df['pr_created_at_monthyear'] == selected_month)

    # filters concatenated pr_dfs from folder pull_requests
    df = df.loc[mask].copy()

    # in case filtered df contains no data (which may definitely be the case for non-active repos)
    if df.empty:
        st.info('No pull request data for current filter selection')
        return None

    # convert datetime columns to the datetime data format
    # errors = 'coerce' means invalid parsing will be set as NaT
    df['pr_created_at'] = pd.to_datetime(df['pr_created_at'], errors = 'coerce')
    df['pr_closed_at'] = pd.to_datetime(df['pr_closed_at'], errors = 'coerce')
    df['pr_merged_at'] = pd.to_datetime(df['pr_merged_at'], errors = 'coerce')

    # calculate durations in days from columns which have been converted to datetime above
    # divide seconds by 60 = minutes
    # divide mins by 60 = hours
    # divide hours by 24 = days
    df['time_to_close_days'] = (df['pr_closed_at'] - df['pr_created_at']).dt.total_seconds() / (60 ** 2 * 24)
    df['time_to_merge_days'] = (df['pr_merged_at'] - df['pr_created_at']).dt.total_seconds() / (60 ** 2 * 24)

    # keep only valid non-negative durations; meaning get rid of NaT values and negative values
    # & means the logical operator and; intersection
    close_df = df[df['time_to_close_days'].notna() & (df['time_to_close_days'] >= 0)].copy()
    merge_df = df[df['time_to_merge_days'].notna() & (df['time_to_merge_days'] >= 0)].copy()

    st.write('Distribution of time to close PRs')
    if close_df.empty:
        st.info('No closed pull requests available for this selection')
    else:
        fig_close = px.box(close_df, y = 'time_to_close_days', points = 'outliers')
        fig_close.update_layout(
            yaxis_title = 'Days from PR creation to PR close',
            xaxis_title = ''
        )
        st.plotly_chart(fig_close, use_container_width = True)

    st.write('Distribution of time to merge PRs')
    if merge_df.empty:
        st.info('No merged pulls requests available for this selection')
    else:
        fig_merge = px.box(merge_df, y = 'time_to_merge_days', points = 'outliers')
        fig_merge.update_layout(
            yaxis_title = 'Days from PR creation to PR merge',
            xaxis_title = ''
        )
        st.plotly_chart(fig_merge, use_container_width = True)

def prs_by_author_bar_chart(raw_dfs, selected_repos, selected_month):

    '''
    creates horizontal bar chart showing the number of PRs opened by each PR creator in the selected month
    
    raw_dfs: pr_dfs, the unfiltered concatenated excels from folder pull_requests
    selected_repos: repo selections from sidebar
    selected_month: selected monthyear from sidebar
    '''

    # title of visualisation
    st.write('PR creators')

    # copy unfiltered concatenated pr_dfs
    df = raw_dfs.copy()

    # required columns for this visualisation
    required_cols = [
        'pr_target_branch_repo_name',
        'pr_user_login',
        'pr_created_at_monthyear',
        'pr_node_id'
    ]

    # missing columns array which will usually be empty unless any table doesn't contain the required columns
    missing_cols = [col for col in required_cols if col not in df.columns]

    # in the case of missing columns from any of the tables in the concatenation
    # meaning if missing_cols isn't empty
    if missing_cols:
        st.error(f"Missing required column(s):' {', '.join(missing_cols)}")
        return None

    # filter by repo(s)
    mask = (
        df['pr_target_branch_repo_name'].isin(selected_repos) if selected_repos else True
    )

    # filter by selected month based on when the PR was opened, adding to the selected_repo mask
    if selected_month:
        mask = mask & (
            df['pr_created_at_monthyear'] == selected_month
        )

    # applying mask and creating filtered df
    filtered_df = df.loc[mask].copy()

    # in case filtered df has no rows
    if filtered_df.empty:
        st.info('No pull request data for the current filter selection')
        return None

    # group by PR creator and count PRs created/opened by each one
    prs_by_author = (
        filtered_df
        .groupby('pr_user_login', as_index = False)['pr_node_id']
        .count() # counts pr_node_id by pr_user_login and pr_user_login is NOT the index of the new dataframe called prs_by_author
        .rename(columns = {'pr_node_id': 'number_of_prs'}) # the new count column still has the column header pr_node_id but now contains counts, so the header name is converted to number_of_prs
        .sort_values('number_of_prs', ascending = False) # orders rows in prs_by_author in descending order of newly renamed columne number_of_prs
    )

    # create the horizontal bar chart
    fig = px.bar(
        prs_by_author,
        x = 'number_of_prs',
        y = 'pr_user_login',
        orientation = 'h',
        labels = {
            'number_of_prs': 'Number of PRs opened',
            'pr_user_login': 'PR creator'
        },
        color_discrete_sequence = ['fuchsia'] # px.colors.qualitative.Plotly
    )

    # largest creator at the top
    fig.update_layout(
        yaxis = {
            'categoryorder': 'total ascending'
        }
    )

    # creates container with figure inside
    st.plotly_chart(fig, use_container_width = True)

def daily_pr_activity_bar_charts(raw_dfs, selected_repos, selected_month):

    '''
    Creates three vertical bar charts for the selected month:
    1. PRs opened daily
    2. PRs merged daily
    3. PRs closed daily

    Each chart filters using its own timestamp
    '''

    # copy raw_dfs, which in this case is pr_dfs
    df = raw_dfs.copy()

    # state the required columns for these three visualisations
    required_cols = [
        'pr_target_branch_repo_name',
        'pr_created_at',
        'pr_merged_at',
        'pr_closed_at'
    ]

    # in case there are missing columns in any of the tables in the folder pull_requests, meaning missing_cols's length is greater than 0, an error will come up in the dashboard
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        st.error(f"Missing required column(s): {', '.join(missing_cols)}")
        return None

    # filter by selected repo(s)
    if selected_repos:
        df = df[df['pr_target_branch_repo_name'].isin(selected_repos)].copy()

    # convert timestamps to datetime
    df['pr_created_at'] = pd.to_datetime(df['pr_created_at'], errors = 'coerce')
    df['pr_merged_at'] = pd.to_datetime(df['pr_merged_at'], errors = 'coerce')
    df['pr_closed_at'] = pd.to_datetime(df['pr_closed_at'], errors = 'coerce')

    # get first and last date of selected month
    selected_month_start = pd.to_datetime(selected_month, format = '%B %Y')
    selected_month_end = selected_month_start + pd.offsets.MonthEnd(1)

    # full list of dates in selected month
    all_dates = pd.date_range(
        start = selected_month_start,
        end = selected_month_end,
        freq = 'D'
    )

    # new function with output of 
    def make_daily_counts(timestamp_col):

        '''
        timestamp_col: one of the timestamp columns in required_cols
        '''

        # filters pr_dfs to just the selected month
        event_df = df[
            df[timestamp_col].between(
                selected_month_start,
                selected_month_end + pd.Timedelta(days = 1) - pd.Timedelta(seconds = 1)
            )
        ].copy()

        if event_df.empty:
            daily_counts = pd.DataFrame({
                'date': all_dates,
                'count': 0
            })

        else:
            # pandas.Series.dt.normalize
            # convert times to midnight
            # the time component of the datetime is converted to midnight which is useful in cases when the time doesn't matter
            # length unaltered
            # timezone unaffected
            event_df['date'] = event_df[timestamp_col].dt.normalize()

            # new dataframe with days and counts of prs opened/closed/merged
            daily_counts = (
                event_df
                .groupby('date')
                .size() # returns number of rows for each date
                .reset_index(name = 'count') # the number of rows for each date is stored under the column header 'count'
            )

            # table consisting of one column containing all days of selected month
            full_dates_df = pd.DataFrame({'date': all_dates})

            # fiinal table which left joins full_dates_df with daily_counts on the date column, filling in NaN values with 0
            daily_counts = (
                full_dates_df
                .merge(daily_counts, on = 'date', how = 'left')
                .fillna({'count': 0})
            )

            # convert count column data type to int
            daily_counts['count'] = daily_counts['count'].astype(int)

        # output daily_counts table with number of prs per day which were opened/merged/closed
        # this function within a function returns the table needed for the outer function, which is the table needed for the individual bar charts
        return daily_counts

    # dataframe for prs opened
    opened_daily = make_daily_counts('pr_created_at')

    # title of the bar chart for daily prs opened
    st.write('PRs opened daily')

    # bar chart for prs opened per day
    fig_opened = px.bar(
        opened_daily,
        x = 'date',
        y = 'count',
        labels = {
            'date': 'Date',
            'count': 'Number of PRs opened'
        },
        color_continuous_scale = px.colors.sequential
    )

    # plotting bar chart for prs opened per day
    st.plotly_chart(fig_opened, use_container_width = True)

    # dataframe for prs merged
    merged_daily = make_daily_counts('pr_merged_at')

    # title of the bar chart for daily prs merged
    st.write('PRs merged daily')

    # bar chart for prs merged per day
    fig_merged = px.bar(
        merged_daily,
        x = 'date',
        y = 'count',
        labels = {
            'date': 'Date',
            'count': 'Number of PRs merged'
        },
        color_discrete_sequence = px.colors.qualitative.Alphabet
    )

    # plotting bar chart for prs merged per day
    st.plotly_chart(fig_merged, use_container_width = True)

    # dataframe for prs closed
    closed_daily = make_daily_counts('pr_closed_at')

    # title of the bar chart for daily prs closed
    st.write('PRs closed daily')

    # bar chart for prs closed per day
    fig_closed = px.bar(
        closed_daily,
        x = 'date',
        y = 'count',
        labels = {
            'date': 'Date',
            'count': 'Number of PRs closed'
        },
        color_discrete_sequence = ['deeppink']
    )

    # plotting bar chart for prs closed per day
    st.plotly_chart(fig_closed, use_container_width = True)

def unresolved_prs_area_chart(raw_dfs, selected_repos, selected_month):

    '''
    creates an area chart showing daily unresolved PR backlog across the selected month

    two lines/areas shown:
    - total unresolved PRs
    - unresolved PRs opened during the selected month

    raw_dfs: pr_dfs, the unfiltered concatenated excels from folder pull_requests
    selected_repos: repo selections from sidebar
    selected_month: selected monthyear from sidebar
    '''

    # title of area chart
    st.write('Unresolved PR backlog')

    df = raw_dfs.copy()

    # required columns for this area chart
    required_cols = [
        'pr_target_branch_repo_name',
        'pr_created_at',
        'pr_closed_at'
    ]

    # array of missing columns in the unaggregated concatenated dataframe
    missing_cols = [col for col in required_cols if col not in df.columns]

    # if missing_cols isn't empty
    if missing_cols:
        st.error(f"Missing required column(s): {', '.join(missing_cols)}")
        return None

    # filter by selected repo(s)
    if selected_repos:
        df = df[df['pr_target_branch_repo_name'].isin(selected_repos)].copy()

    # convert timestamps to datetime
    df['pr_created_at'] = pd.to_datetime(df['pr_created_at'], errors = 'coerce')
    df['pr_closed_at'] = pd.to_datetime(df['pr_closed_at'], errors = 'coerce')

    # remove rows where created_at is invalid, meaning it's NaT
    df = df.dropna(subset = ['pr_created_at'])

    # in case there's no data in the dataframe
    if df.empty:
        st.info('No pull request data for the current filter selection')
        return None

    # first day of selected month
    selected_month_start = pd.to_datetime(selected_month, format = '%B %Y')

    # first day of following month
    selected_month_end_exclusive = (selected_month_start + pd.offsets.MonthBegin(1))

    # every day in selected month which will be x-axis
    all_dates = pd.date_range(
        start = selected_month_start,
        end = selected_month_end_exclusive - pd.Timedelta(days = 1),
        freq = 'D'
    )

    # initialise array for collecting individual dicts for each day
    chart_rows = []

    # calculate backlog for every day
    for day in all_dates:

        # use the end of the current day, which is the next day
        day_end = day + pd.Timedelta(days = 1)

        # create filter
        # PR has been created before the next day
        # AND
        # either PR hasn't been closed OR it's been closed sometime from the next day onwards
        total_unresolved_mask = (
            (df['pr_created_at'] < day_end)
            &
            (
                df['pr_closed_at'].isna() | (df['pr_closed_at'] >= day_end)
            )
        )

        # count of all unresolved PRs per day
        total_unresolved = df.loc[total_unresolved_mask, 'pr_created_at'].count()

        # unresolved PRs that were opened during selected month
        # intersection of total_unresolved_mask and PR is created after month start inclusive and before month end exclusive
        opened_this_month_mask = (
            total_unresolved_mask
            &
            (df['pr_created_at'] >= selected_month_start)
            &
            (df['pr_created_at'] < selected_month_end_exclusive)
        )

        # count of unresolved PRs opened in selected month per day
        unresolved_opened_this_month = df.loc[opened_this_month_mask, 'pr_created_at'].count()

        # create dictionary for area chart
        chart_rows.append({
            'date': day,
            'total_unresolved': total_unresolved,
            'unresolved_opened_this_month': unresolved_opened_this_month
        })

    # convert dict to df
    chart_df = pd.DataFrame(chart_rows)

    # create container for area chart - blank canvas
    fig = go.Figure()

    # line for total unresolved PRs
    fig.add_trace(
        go.Scatter(
            x = chart_df['date'],
            y = chart_df['total_unresolved'],
            mode = 'lines',
            line_color = 'deeppink',
            name = 'Total unresolved PRs',
            fill = 'tozeroy',
            fillcolor = 'pink',
            hovertemplate = (
                'Date: %{x|%Y-%m-%d}<br>'
                'Total unresolved PRs: %{y}'
            )
        )
    )

    # line for unresolved PRs opened in selected month
    fig.add_trace(
        go.Scatter(
            x = chart_df['date'],
            y = chart_df['unresolved_opened_this_month'],
            mode = 'lines',
            line_color = 'orchid',
            name = 'Unresolved PRs opened this month',
            fill = 'tozeroy',
            fillcolor = 'violet',
            hovertemplate = (
                'Date: %{x|%Y-%m-%d}<br>'
                'Opened this month and unresolved: %{y}'
            )
        )
    )

    # adds info to chart
    fig.update_layout(
        xaxis_title = 'Date',
        yaxis_title = 'Number of unresolved PRs',
        hovermode = 'x unified',
        xaxis = dict(type = 'date')
    )

    # plot visualisation
    st.plotly_chart(
        fig,
        use_container_width = True
    )

# title of first section
st.title('GitHub Analytics - Commits')

# ungrouped unionised dfs from commits_history folder
ungrouped_commits_history = read_in_and_concat_commits_history_dfs()

# filter outputs
selected_repos, selected_month = global_filter() # global_filter() already called here, so no need to call it again in its own line to make sidebar appear

# ungrouped filtered df
ungrouped_filtered_df = globally_filtered_commits_history_dfs(ungrouped_commits_history, selected_repos, selected_month)

# ungrouped unionised dfs from for_12_kpi folder
past_29_months_commits_history_dfs = read_in_and_concat_commits_history_dfs(foldername = 'for_12_kpi')

# concatenates all excel files in the additions and deletions folder
additions_and_deletions_dfs = read_in_and_concat_commits_history_dfs(foldername = 'additions_and_deletions')

# filters all additions and deletions by repo name and selected month
filtered_additions_and_deletions = globally_filtered_commits_history_dfs(additions_and_deletions_dfs, selected_repos, selected_month)

# actual kpi visualisation for past 12 months and YoY% excluding selected month
kpi_12_visualisation(past_29_months_commits_history_dfs, selected_repos, selected_month, n = 13)

# actual kpi visualisation for past 6 months and % difference from 6 months before excluding selected month
kpi_12_visualisation(past_29_months_commits_history_dfs, selected_repos, selected_month, n = 7)

# actual kpi visualisation for past month and MoM% excluding selected month
kpi_12_visualisation(past_29_months_commits_history_dfs, selected_repos, selected_month, n = 2)

# actual pie chart visualisation for commits per commit author in selected month
commits_history_pie_chart_visualisation(ungrouped_filtered_df)

# top 5 authors by additions
top_5_authors_additions_table(filtered_additions_and_deletions)

# actual bar chart visualisation for daily additions and deletions, colour-coded by author_email
daily_additions_deletions_bar_chart_visualisation(ungrouped_filtered_df = filtered_additions_and_deletions)

# title of second section
st.title('GitHub Analytics - Pull Requests')

# concatenated pr dfs
pr_dfs = read_in_and_concat_commits_history_dfs(foldername = 'pull_requests')

# pr kpi outputs
pr_kpi_arr = pr_kpis(pr_dfs, selected_repos, selected_month, 2)

# actual kpi visualisation
display_pr_kpis(pr_kpi_arr)

# box plots of time-to-close and time-to-merge
time_to_conclude_distributions(pr_dfs, selected_repos, selected_month)

# horizontal bar chart for PRs opened grouped by pr_user_login
prs_by_author_bar_chart(pr_dfs, selected_repos, selected_month)

# 3 bar charts for daily pr stats
daily_pr_activity_bar_charts(pr_dfs, selected_repos, selected_month)

# area chart of unresolved PRs
unresolved_prs_area_chart(pr_dfs, selected_repos, selected_month)