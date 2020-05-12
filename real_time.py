import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import numpy as np
import os
import datetime

def main():

    st.title('Real Time Development Database')


    # let user select the aggregation date field and load the data bsed on selection
    st.sidebar.header("Horizontal Axis")

    date_field = st.sidebar.radio(label="", options=["Job Application Filing Date", "Permit Issued Date",
    'Job Completion Date'], index=0)

    date_field_dict = {"Job Application Filing Date": "date_filed", "Permit Issued Date": "date_permittd",
    'Job Completion Date': "date_statusx"}

    agg_db = load_data(date_field_dict[date_field])

    #margin: -1.2rem 5px 1rem 5px
    subtext_style="font-size:0.8rem; margin: -0.5rem 5px 1.5rem 5px; color:#969696; padding: 0.2rem !important;"

    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            <strong>Job Application Filing Date</strong>: The first step in the process for all job applications  
        </p>
    ''', unsafe_allow_html=True)

    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            <strong>Permit Issued Date</strong>: When construction work may begin  
        </p>
    ''', unsafe_allow_html=True)

    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            <strong>Job Completion</strong>: When the earliest certificate of occuapancy if issued  
            (for buildings and alterations). For demolitions, this   
            date is equal to the permit issued date 
        </p>
    ''', unsafe_allow_html=True)


    # let user select the aggregation date field and load the data bsed on selection
    st.sidebar.header("Vertical Axis")

    devs_or_units = st.sidebar.radio(label="", options=["Number of developments", "Sum by residential units"], index=0)
    
    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            <strong>Number of developments</strong>: the count DOB jobs filed/issued that week
        </p>
    ''', unsafe_allow_html=True)

    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            <strong>Sum by residential units</strong>: the net number of residential units associated with the DOB jobs
        </p>
    ''', unsafe_allow_html=True)

    # job type selection
    st.sidebar.header("Job Type")

    new_building = st.sidebar.checkbox('New Building', value=True)

    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            an application to build a new structure
        </p>
    ''', unsafe_allow_html=True)

    alteration = st.sidebar.checkbox('Major Alteration', value=True)

    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            an "A1" alteration changing use, egress, or occupancy of the building
        </p>
    ''', unsafe_allow_html=True)


    demolition = st.sidebar.checkbox('Demolition', value=True)

    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            fully or partially demolish an existing building
        </p>
    ''', unsafe_allow_html=True)

    # add in options to select by boroguhs
    st.sidebar.header("Borough")

    borough = st.sidebar.selectbox(label='Use the dropdown options to view data for all boroughs or just a single borough', 
        options= ['All Boroughs', 'Manhattan', 'Brooklyn', 'Staten Island', 'Queens', 'Bronx'], index=0)

    # two checkbox for residential if it is relevant
    if devs_or_units == 'Number of developments':

        st.sidebar.header("Use Type")

        residential = st.sidebar.checkbox('Contains residences', value=True)

        st.sidebar.markdown(f'''
            <p style="{subtext_style}">
                The propsed or existing building contains residential units
            </p>
        ''', unsafe_allow_html=True)


        nonresidential = st.sidebar.checkbox('Non-residential', value=True)
        
        st.sidebar.markdown(f'''
            <p style="{subtext_style}">
                Building is entirely non-residential
            </p>
        ''', unsafe_allow_html=True)

        st.sidebar.info("Please note **at least one** of options above should be selected")
        
        rmask = np.array([residential, nonresidential])

        use_types = np.array(['Residential', 'Other'])
        
        slctd_use_types = use_types[rmask]

        # select only the dataframe with residential unit if residential checkbox is ticked
        agg_db = agg_db.loc[agg_db.occ_category.isin(slctd_use_types)]

    # mask use to create array for selection using the dataframe
    jmask = np.array([alteration, demolition, new_building])

    job_types = np.array(['Alteration', 'Demolition', 'New Building'])
    
    slctd_job_types = job_types[jmask]

    agg_db = agg_db.loc[agg_db.job_type.isin(slctd_job_types)]

    if borough != 'All Boroughs':

        agg_db = agg_db.loc[agg_db.boro == borough]

    # aggreage either developments or net units on a weekly level. 
    job_str = slctd_job_types.tolist() # use the job string for appropriate titles

    if devs_or_units == 'Number of developments':

        # calculate the weekly count for the interested 
        agg_week = agg_db.groupby(['year', 'week']).agg({'total_count': 'sum'}).reset_index()

        if date_field == 'Job Application Filing Date':

            graph_format = [(',').join(job_str) + ' Job Application Filed Per Week', 
            'Number of Application Filed']
    
        elif date_field == 'Permit Issued Date':

            graph_format = [(',').join(job_str) + ' Permits Issued Per Week',
            'Number of Permits Issued']
        
        else:

            graph_format = [(',').join(job_str) + 'Certificate of Occupancy Per Week',
            'Number of Certificate of Occupancy']

    else:

        # calculate the weekly residentia units based on the 
        agg_week = agg_db.groupby(['year', 'week']).agg({'total_units_net': 'sum'}).reset_index()

        if date_field == 'Job Application Filing Date':

            graph_format = ['Net Residential Units ' + (',').join(job_str) + ' in Job Application Filed Per Week', 
            'Number of Residential Units in Application Filed']
    
        elif date_field == 'Permit Issued Date':

            graph_format = ['Net Residential Units ' + (',').join(job_str) + ' in Permits Issued Per Week',
            'Number of Residential Units in Permits Issued']
        
        else:

            graph_format = ['Net Residential Units ' + (',').join(job_str) + ' in Certificate of Occupancy Per Week',
            'Number of Residential Units in Certificate of Occupancy']

    # adjust the year field to string for plotting     
    agg_week.year = agg_week.year.astype(int).astype(str)

    # add the three year averages to the plot
    three_year_avg = calculate_three_year_avg(agg_week)

    # create a accruate title for the graph based on the criteria selected (job type,)
    st.subheader(graph_format[0])

    visualize(three_year_avg, agg_week, graph_format)

    st.info("""
    ### HINTS:
    This is a interative [plotly express plot](https://plotly.com/python/plotly-express/). Here are few tips about how to 
    interact with the plot.
    + **Double click on any year or groups in the colored legend on the right side of the plot to
    to focus on single line.** You can then add the other relevant group back onto the plots by single-click on them
    individuallly. 
    + **You then also click and drag to zoom into a specific area of the plot.** Notice the axis will also
    adjust with as the zoom is performed. 
    + You can click on two-arrows icons on the top right corner on the fringe of the
    plot. **You will only see this icon when your cursos is hovering on the plot.** 
    """)


def fill_zeros(agg_db, conn):
    
    f = pd.read_sql('''SELECT * FROM zero_fill_template''', con=conn)
               
    df = pd.DataFrame(columns=agg_db.columns)

    for year in agg_db.year.unique():

        new = f.merge(agg_db.loc[agg_db.year == year], how='left', on=['week', 'job_type', 'occ_category', 'boro']).fillna(value=0)

        new.year = year
        
        if year == 2020:
            
            new = new.loc[new.week <= int(datetime.datetime.now().strftime("%V"))]

        df = pd.concat([df, new], axis=0, sort=True)

    return df

@st.cache
def load_data(date_field):

    conn = create_engine(os.environ.get('ENGINE'))

    agg_db = pd.read_sql('''
    SELECT 
        Extract('year' FROM {0} :: timestamp) AS year, 
        Extract('week' FROM {0} :: timestamp) AS week, 
        job_type, 
        occ_category, 
        boro,
        coalesce(COUNT(*), 0) as total_count,
        SUM(units_net :: NUMERIC) as total_units_net

    FROM   devdb_export 

    WHERE
        Extract('year' FROM {0} :: timestamp) >= 2010
        AND 
        Extract('week' FROM {0} :: timestamp) <> 1
        AND 
        Extract('week' FROM {0} :: timestamp) <> 53

    GROUP  BY 
        Extract('year' FROM {0} :: timestamp), 
        Extract('week' FROM {0} :: timestamp), 
        job_type, 
        occ_category,
        boro
    '''.format(date_field), con = conn)
    
    filled_agg_db = fill_zeros(agg_db, conn)

    return filled_agg_db

def calculate_three_year_avg(agg_week):

    #aggregate field
    af = agg_week.columns[2]

    # average of years 2019 - 2017, 16 - 14, 13 - 11 
    avg_17_19 = agg_week.loc[agg_week.year.isin(['2019', '2018', '2017'])].groupby('week').agg({af: 'mean'}).reset_index()

    avg_17_19['year'] = 'Three-Year Average 2017 - 2019'

    avg_14_16 = agg_week.loc[agg_week.year.isin(['2016', '2015', '2014'])].groupby('week').agg({af: 'mean'}).reset_index()

    avg_14_16['year'] = 'Three-Year Average 2014 - 2016'

    avg_11_13 = agg_week.loc[agg_week.year.isin(['2013', '2012', '2011'])].groupby('week').agg({af: 'mean'}).reset_index()

    avg_11_13['year'] = 'Three-Year Average 2011 - 2013'

    three_year_avg = pd.concat([avg_17_19, avg_14_16, avg_11_13], axis=0)

    three_year_avg.sort_values(by=['year', 'week'], ascending=False, inplace=True)

    return three_year_avg

def visualize(three_year_avg, agg_week, graph_format):

    #aggregate field
    af = agg_week.columns[2]

    # ploting with plotly express
    fig = px.line(three_year_avg, x="week", y=af, color="year")

    # add the 2020 in black
    one_year = agg_week.loc[agg_week.year == '2020'] 
    fig.add_trace(go.Scatter(
        x=one_year.week,
        y=one_year.iloc[:, 2],
        name='2020',
        mode="lines",
        line=dict(color='black')
    ))

    # plot the other years in gray
    other_years = ['2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017','2018','2019', '2020']

    other_years.sort(reverse=True)
 

    for yr in other_years:

        # plot 2020 in black and other years in grey
        if yr == '2020':
            continue
        else:
            clr = 'grey'
            vb = 'legendonly'

        one_year = agg_week.loc[agg_week.year == yr] 

        fig.add_trace(go.Scatter(
            x=one_year.week,
            y=one_year.iloc[:, 2],
            name=yr,
            mode="lines",
            line=dict(color=clr),
            visible=vb
        ))


    # plot formatting
    fig.update_layout(
        xaxis_title='Week Number',
        yaxis_title=graph_format[1],
        template='plotly_white'
    )

    # plot with streamlit
    st.plotly_chart(fig)


if __name__ == "__main__":

    main()

