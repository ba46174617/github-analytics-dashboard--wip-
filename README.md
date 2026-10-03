# GitHub Analytics Dashboard

## Overview
This is a streamlit dashboard for analysing monthly GitHub activity for the past 6 months for public repositories under a username. For my dashboard, I used 'freeCodeCamp' as the username, but you can change the username. But if there exist private repositories under that username, they won't be counted because the code here only fetches public repository data. The dashboard currently includes data on commits and pull requests, but in later versions I also plan on including analytics on issues and code reviews. 

## Features
- Commit volume analysis
- Pull request KPIs
- PR creator rankings
- Daily PR activity
- Time-to-close and time-to-merge distributions
- Unresolved PR backlog trends

## Tech Stack
- Python
- Streamlit
- Pandas
- Plotly
- GitHub REST API
- GitHub GraphQL API
- Excel

## Dashboard Screenshots
<img src="images/1 Dashboard Overview First Part.png">
<img src="images/2 Dashboard Overview Second Part.png">
<img src="images/3 Dashboard Overview Third Part.png">
<img src="images/4 Dashboard Overview Fourth Part.png">
<img src="images/5 Dashboard Overview Fifth Part.png">
<img src="images/6 Dashboard Overview Sixth Part.png">

## Running the project
Only app.py and Tables for Individual Visualisations Draft 2.ipynb are needed. The other folders and files are generated from the jupyter notebook
1. Create an empty folder in your local storage
2. Download and store app.py and Tables for Individual Visualisations Draft 2.ipynb in that folder
3. In the jupyter notebook, replace the dummy token codes with classic token codes which you will need to generate beforehand from https://github.com/settings/tokens
4. Change the owner to the username of which you want to analyse the repositories
5. Go to the last cell before the heading 'Read in data from excel for checks - NOT part of data transformation pipeline', select all the content and uncomment, make sure that cell stays selected
6. In the notebook toolbar select Kernel > Restart Kernel and Run up to Selected Cell
7. Wait for notebook to finish running and you should see new files and folders generated in the folder you created in the beginning. These contain the excel files app.py will ingest. It's possible you might that some uploads failed for the function that creates pull_requests, so once the execution is finished, you can run that function only again, or you can go to the GraphQL query of the function and change the 'first' parameter to a lower number and try running that function again
8. Once all the folders and files needed are generated, open app.py
9. Run it, and in the terminal, type 'streamlit run app.py' and then press enter, which should lead to the pop up of the streamlit window
