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

##########################################
#Side Panel functionality
##########################################
    # let user select the aggregation date field and load the data bsed on selection
    st.sidebar.header("Horizontal Axis")

    date_field = st.sidebar.radio(label="", options=["Job application filing date", "Permit issued date",
    'Job completion date'], index=0)

    date_field_dict = {"Job application filing date": "date_filed", "Permit issued date": "date_permittd",
    'Job completion date': "date_statusx"}

    agg_db = load_data(date_field_dict[date_field])

    #margin: -1.2rem 5px 1rem 5px
    subtext_style="font-size:0.8rem; margin: -0.5rem 5px 0.8rem 5px; color:#808080; padding: 0.2rem !important;"

    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            <strong>Job application filing date</strong>: The first step in the process for all job applications  
        </p>
    ''', unsafe_allow_html=True)

    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            <strong>Permit issued date</strong>: When construction work may begin  
        </p>
    ''', unsafe_allow_html=True)

    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            <strong>Job completion date</strong>: When the earliest certificate of occuapancy is issued  
            (for buildings and alterations). For demolitions, this   
            date is equal to the permit issued date 
        </p>
    ''', unsafe_allow_html=True)


    # let user select the aggregation date field and load the data bsed on selection
    st.sidebar.header("Vertical Axis")

    devs_or_units = st.sidebar.radio(label="", options=["Number of developments", "Sum of residential units"], index=0)
    
    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            <strong>Number of developments</strong>: The count DOB jobs filed/issued that week
        </p>
    ''', unsafe_allow_html=True)

    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            <strong>Sum of residential units</strong>: The net number of residential units associated with the DOB jobs
        </p>
    ''', unsafe_allow_html=True)

    # job type selection
    st.sidebar.header("Job Type")

    new_building = st.sidebar.checkbox('New building', value=True)

    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            An application to build a new structure
        </p>
    ''', unsafe_allow_html=True)

    alteration = st.sidebar.checkbox('Major alteration', value=True)

    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            An "A1" alteration changing use, egress, or occupancy of the building
        </p>
    ''', unsafe_allow_html=True)


    demolition = st.sidebar.checkbox('Demolition', value=True)

    st.sidebar.markdown(f'''
        <p style="{subtext_style}">
            Fully or partially demolish an existing building
        </p>
    ''', unsafe_allow_html=True)

    # add in options to select by boroguhs
    st.sidebar.header("Borough")

    borough = st.sidebar.selectbox(label='', 
        options= ['All boroughs', 'Manhattan', 'Brooklyn', 'Staten Island', 'Queens', 'Bronx'], index=0)

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
                The proposed or existing building is entirely non-residential
            </p>
        ''', unsafe_allow_html=True)

        st.sidebar.info("Please note **at least one** Use Type must be selected")
        
        # residential and nonresidential 
        if residential and nonresidential:

            agg_db = agg_db

            use_str = ''

        elif residential:

            agg_db = agg_db.loc[agg_db.occ_category == 'Residential']

            use_str = 'Residential '

        elif nonresidential:

            agg_db = agg_db.loc[agg_db.occ_category == 'Other']

            use_str = 'Non-Residential '

    # mask use to create array for selection using the dataframe
    jmask = np.array([new_building, alteration, demolition])

    job_types = np.array(['New Building', 'Alteration', 'Demolition'])
    
    slctd_job_types = job_types[jmask]

    agg_db = agg_db.loc[agg_db.job_type.isin(slctd_job_types)]

    job_str = slctd_job_types.tolist() # use the job string for appropriate titles

    job_str = [s + 's' for s in job_str]

    # set the boroughs strings
    if borough != 'All boroughs':

        agg_db = agg_db.loc[agg_db.boro == borough]

        bo_str = borough

    else:

        bo_str = 'NYC'

    # aggreage either developments or net units on a weekly level. 
    if devs_or_units == 'Number of developments':

        # calculate the weekly count for the interested 
        agg_week = agg_db.groupby(['year', 'week']).agg({'total_count': 'sum'}).reset_index()

        if date_field == 'Job application filing date':

            graph_format = ['Job Applications Filed Per Week in ' + bo_str + ' (in ' + use_str + (', ').join(job_str) + ')', 
            'Number of Applications Filed']
    
        elif date_field == 'Permit issued date':

            graph_format = [' Permits Issued Per Week in ' + bo_str + ' (in ' + use_str + (', ').join(job_str) + ')',
            'Number of Permits Issued']
        
        else:

            graph_format = ['Certificates of Occupancy Issued Per Week in '  + bo_str + ' (in ' + use_str +  (', ').join(job_str) + ')',
            'Number of Certificates of Occupancy']

    else:

        # calculate the weekly residentia units based on the 
        agg_week = agg_db.groupby(['year', 'week']).agg({'total_units_net': 'sum'}).reset_index()

        if date_field == 'Job application filing date':

            graph_format = ['Net Units in Job Applications Filed Per Week in ' + bo_str + ' (in ' + (', ').join(job_str) + ')', 
            'Number of Residential Units in Applications Filed']
    
        elif date_field == 'Permit issued date':

            graph_format = ['Net Units in Permis Issued Per Week in ' + bo_str + ' (in ' + (', ').join(job_str) + ')',
            'Number of Residential Units in Permits Issued']
        
        else:

            graph_format = ['Net Units in Certificates of Occupancy Issued Per Week in ' + bo_str + ' (in ' + (', ').join(job_str) + ')',
            'Number of Residential Units in Certificates of Occupancy']

    # adjust the year field to string for plotting     
    agg_week.year = agg_week.year.astype(int).astype(str)

    # add the three year averages to the plot
    three_year_avg = calculate_three_year_avg(agg_week)

 #########################################################################
 #Main Panel content starts here
 ##########################################################################   

    st.title('Real Time Development Tracker')

    st.header('About the Tracker')
    st.info("""
    
    On March 27, 2020 NYS issued a ban on all nonessential construction in 
    effort to contain COVID-19. Since this time, the definition of [**essential**](https://www1.nyc.gov/assets/buildings/pdf/essential_vs_non-essential.pdf) has widened 
    somewhat but reductions in building application and permit activity are still apparent. 
    This tracker displays weekly data [**updates**](https://data.cityofnewyork.us/Housing-Development/DOB-Job-Application-Filings/ic3t-wcy2) from the Department of Buildings, showing major 
    construction (new buildings, major alterations, and demolitions) at three important 
    milestones (application filed, permit issued, and certificate of occupancy issued).  
      
    Please let us know if you have any comments and questions about this open-source dashboard 
    by [**raising an issue**](https://github.com/NYCPlanning/hed-real-time-devdb/issues) in the project [**github repo**](https://github.com/NYCPlanning/hed-real-time-devdb), or emailing **HED_DL(at)planning.nyc.gov**.   
      
    + Use the left-hand pane to specify milestone date, aggregation type, DOB job type, and building use type. 
    + Click or hover on the chart itself to customize years displayed, zoom in on the plot area, and see data values.

    """)

    # create a accruate title for the graph based on the criteria selected (job type,)
    st.subheader(graph_format[0])

    visualize(three_year_avg, graph_format)

    #start the executive summary section
    st.header('Excutive Summary for Week Beginning May 25')

    st.info("""
    ### Job Applications Filings
    + Work need not be deemed essential in order to file a job application.  
    + Applications for all major construction projects (new buildings, major alterations, and demolitions) dropped beginning in week 12 (March 16) and hit a record low for the year on week 14 (March 30).  
    + Applications have been gradually increasing since week 15 (April 6), with a dramatic spike on week 19 (May 4) and returning to levels that are about half of what was filed at this time during the last three years. 
    + Despite the diminished number of applications for new residential buildings, the number of units associated with those jobs is very high, even surpassing the number of units filed for in previous years, suggesting that applicants are primarily submitting for larger jobs. 

    ### Permits Issued
    + COVID-19 and the construction ban had the greatest impact on permits issued, since permits are only currently being issued for [**essential construction**](https://www1.nyc.gov/assets/buildings/html/essential-active-construction.html).  
    + 2020 permits for all new buildings, major alterations, and demolitions were keeping pace with the last three years until week 12 (March 16), when they began to drop less than 10% of typical volumes. The few permits that have been issued since the construction ban took effect on March 27 (week 14) include residential and non-residential buildings alike. 

    ### Certificates of Occupancy
    + Certificates of Occupancy (COs) are currently only being issued for essential construction.  
    + CO issuance reached a low in week 17 (April 20) and continues to decline and has increased only modestly since then.  
    + The last two months have seen the number of COs issued for new buildings with residences drop by about half compared to the last three years, and residential units drop by about one third. 
    """)

    st.header('Excutive Summary for Week Beginning May 11')

    st.info("""
    ### Job Applications Filings
    + Work need not be deemed essential in order to file a job application.  
    + Applications for all major construction projects (new buildings, major alterations, and demolitions) dropped beginning in week 12 (March 16) and hit a record low for the year on week 14 (March 30).  
    + Applications have been gradually increasing since week 15 (April 6), with a dramatic spike on week 19 (May 4) and returning to levels that are about half of what was filed at this time during the last three years. 
    + Despite the diminished number of applications for new residential buildings, the number of units associated with those jobs is very high, suggesting that applicants are primarily submitting for larger jobs. 

    ### Permits Issued
    + COVID-19 and the construction ban had the greatest impact on permits issued, since permits are only currently being issued for [**essential construction**](https://www1.nyc.gov/assets/buildings/html/essential-active-construction.html).  
    + 2020 permits for all new buildings, major alterations, and demolitions were keeping pace with the last three years until week 12 (March 16), when they began to drop less than 10% of typical volumes. The few permits that have been issued since the construction ban took effect on March 27 (week 14) include residential and non-residential buildings alike. 

    ### Certificates of Occupancy
    + Certificates of Occupancy (COs) are currently only being issued for essential construction.  
    + CO issuance began to drop in week 12 (March 16) and continues to decline. Last week had the lowest volume of COs issued since the pandemic began.  
    + New buildings with residences saw a brief spike in week 19 (May 4) but dropped to historic lows last week (May 11).   
    + The last 4 weeks have seen the number of COs issued for new buildings with residences drop by about half compared to the last three years, and residential units drop by about one third.  
    """)

    st.header('Excutive Summary for Week Beginning May 3')

    st.info("""
    ### Job Applications Filings
    + Work need not be deemed essential in order to file a job application.
    + Applications for all major construction projects (new buildings, major alterations, and demolitions) dropped beginning in week 12 (March 16) and hit a record low for the year on week 14 (March 30).
    + Applications have been gradually increasing since week 15 (April 6) but are still about half of what was filed at this time during the last three years.
    + Job applications for new buildings with residences bottomed out in weeks 15 and 16 and have picked up somewhat in weeks 17 (April 20) and 18 (April 27).
    + Despite the relatively small number of applications for new residential buildings, the number of units associated with those jobs is still high, suggesting that applicants are primarily submitting for larger jobs. 
    
    ### Permits Issued
    + COVID-19 and the construction ban had the greatest impact on permits issued, since permits are only currently being issued for [**essential construction**](https://www1.nyc.gov/assets/buildings/html/essential-active-construction.html).  
    + 2020 permits for all new buildings, major alterations, and demolitions were keeping pace with the last three years until week 12 (March 16), when they began to drop to only one or two per week. The few permits that have been issued since the construction ban took effect on March 27 (week 14) include residential and non-residential buildings alike. 
    
    ### Certificates of Occupancy
    + COs are currently only being issued for essential construction.
    + Certificate of occupancy (CO) issuance began to drop in week 12 (March 16), and has continued dropping through the most current data.
    + COs issued for new residential buildings is currently about 10% of normal volume, containing about 20% of normal unit counts as defined by the previous three years.
    + While CO issuance of residential units is declining in new building construction, there was a recent boost of units from alterations. Weeks 17 and 18 saw a higher number of completed residential units in alterations than in previous years even though these are occurring in a very small number of buildings. This supports the observation once again that only large residential buildings are being granted essential construction status, likely because they contain affordable units.
    """)



def fill_zeros(agg_db, conn):
    
    f = pd.read_sql('''SELECT * FROM zero_fill_template WHERE week <> 53''', con=conn)
               
    df = pd.DataFrame(columns=agg_db.columns)

    for year in agg_db.year.unique():

        new = f.merge(agg_db.loc[agg_db.year == year], how='left', on=['week', 'job_type', 'occ_category', 'boro']).fillna(value=0)

        new.year = year
        
        if year == 2020:
            
            new = pd.DataFrame(new.loc[new.week < int(datetime.datetime.now().strftime("%V"))])

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
        boro,
        coalesce(COUNT(*), 0) as total_count,
        SUM(classa_net :: NUMERIC) as total_units_net,
        (CASE 
            WHEN resid_flag IS NULL THEN 'Other'
            ELSE 'Residential'
        END AS occ_category)
        

    FROM   final_devdb

    WHERE
        Extract('year' FROM {0} :: timestamp) >= 2010

    GROUP  BY 
        Extract('year' FROM {0} :: timestamp), 
        Extract('week' FROM {0} :: timestamp), 
        job_type, 
        boro,
        (CASE 
            WHEN resid_flag IS NULL THEN 'Other'
            ELSE 'Residential'
        END AS occ_category)
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

    three_year_avg = pd.concat([avg_17_19, avg_14_16, avg_11_13, agg_week], axis=0)

    return three_year_avg

def visualize(three_year_avg, graph_format):

    af = three_year_avg.columns[1]

    fig = px.line(three_year_avg, x="week", y=af, color="year",
        #hover_name='year',
        #hover_data=['week', af, 'year'],
        category_orders={'year':['Three-Year Average 2017 - 2019', 'Three-Year Average 2014 - 2016', 'Three-Year Average 2011 - 2013',
            '2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012', '2011', '2010']},
        color_discrete_sequence=[ '#FF0000','#228B22','#00BFFF', '#000000',
             '#D3D3D3', '#D3D3D3', '#D3D3D3', '#D3D3D3', '#D3D3D3', '#D3D3D3', '#D3D3D3', '#D3D3D3', '#D3D3D3', '#D3D3D3']
            )
    legend_only = ['Three-Year Average 2014 - 2016', 'Three-Year Average 2011 - 2013','2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012', '2011', '2010']
    

    # add the date to 2020 hover text
    mds = pd.date_range(start=str(2020), end=str(2021), freq='W-MON').strftime("%B %d, %Y").tolist()

    wn = int(datetime.datetime.now().strftime("%V"))

    fig.for_each_trace(
        lambda trace: trace.update(visible='legendonly') if trace.name in legend_only else()
    )

    #fig.update_traces(hovertemplate='<i><b>Year</b></i>: %{year}<br><i>Count</i>: %{y: } <br><b>Week number</b>: %{x}<br>'
    #)

    fig.update_traces(hovertemplate='<i><b>Year</b></i>: 2020<br>' + 
        '<i><b>Count</b></i>: %{y: }'+
        '<br><b>Week number</b>: %{x}<br>'+
        '<b>Week Start Date:</b> %{text}', 
        text=mds[:wn], 
        selector={'name': '2020'}
    )
 
    #fig.for_each_trace(        
    #    lambda trace: trace.update(#hoverdata=,
    #    hovertemplate='<i>year</i>: %{year} <br>' + 
    #    '<i>count</i>: %{y: }'+
    #    '<br><b>week number</b>: %{x}<br>'+
    #    '<b>date: %{text}</b>',
    #    text = mds[:22]) if trace.name == '2020' else()
    #)   

    
    # plot formatting
    fig.update_xaxes(showgrid=False)

    fig.update_layout(
        #title=graph_format[0],
        xaxis_title='Week Number',
        yaxis_title=graph_format[1],
        template='plotly_white',
        hovermode="x",
        
    )

    # plot with streamlit
    st.plotly_chart(fig)


if __name__ == "__main__":

    main()

