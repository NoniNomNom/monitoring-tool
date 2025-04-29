from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from shiny import ui
from datetime import datetime, timedelta
import re
import feedparser
import json
import pandas as pd

google_auth = GoogleAuth(settings_file="settings.yaml")
google_auth.LocalWebserverAuth()
drive = GoogleDrive(auth = google_auth)

def get_file_id(file_name):
    file_list = drive.ListFile({'q': f"title='{file_name}' and trashed=false"}).GetList()
    id = file_list[0]['id']
    return id

def get_json_content(file_name):
    file_id = get_file_id(file_name)
    file = drive.CreateFile({'id' : file_id})
    file.GetContentFile(file_name, remove_bom=True)
    with open(file_name, "r") as f: 
            f = json.load(f)
    content = f
    return content, file

def get_sheet_content(sheet_id, sheet_name):
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    data = pd.read_csv(sheet_url)

    titles = data["TX_TITRE"]
    dates = pd.to_datetime(data['DT_DATE'])
    formatted_dates = dates.dt.strftime("%d-%m-%Y - %H:%M")
    formatted_days = dates.dt.strftime('%d')
    formatted_months = dates.dt.strftime('%m')
    formatted_years = dates.dt.strftime('%Y')
    formatted_hours = dates.dt.strftime('%H')
    urls = data["TX_URL"]

    # Function to fill TX1 based on TX2
    def fill_tx1(row):
        if pd.isna(row['TX_CHAPO']) or row['TX_CHAPO'] == '':
            return ""
        else: 
            return row['TX_CHAPO']

    # Apply the function to the dataframe
    description_shorts = data.apply(fill_tx1, axis=1)

    descriptions = data["TX_CHAPO"].astype(str) + " " + data["TX_TEXTE"].astype(str)
    
    sites = data["TX_SITE"]

    df_webscraped = pd.DataFrame({
        "Title":titles,
        "Date":formatted_dates,
        "Day":formatted_days,
        "Month":formatted_months.astype(int),
        "Year":formatted_years.astype(int),
        "Hour": formatted_hours.astype(int),
        "URL": urls,
        "Description_all": descriptions.str.strip(),
        "Description": description_shorts,
        "Feed": sites
        })

    return df_webscraped

def parse_and_append(feed_url, feed_name, all_data = None, error = 0, out_time = 0):

        parsed_feed = feedparser.parse(feed_url)
        parsed_entries = []
   
        back = datetime.now() - timedelta(days=30) # changer le nombre de jours si besoin
        
        entries = parsed_feed.entries if 'entries' in parsed_feed else []
        print(len(entries))
        
        for entry in entries:
            title = entry.title

            if not title:
                print("NO TITLE")
                error = error + 1
                continue
            else :
                date = entry.published_parsed if 'published_parsed' in entry else None
                if date and datetime(*date[:6]) < back or date == None:
                    print("OUT OF TIME")
                    out_time = out_time + 1
                    continue
                url = entry.link if 'link' in entry else None
                description = entry.summary if 'summary' in entry else None
                words = re.sub('<[^<]+?>', '', description)
                words = str(words).split()
                description_short = ' '.join(words[:15])
                formatted_date = datetime.strftime(datetime(*date[:6]), "%d-%m-%Y - %H:%M") if date else None
                formatted_day = datetime.strftime(datetime(*date[:6]), "%d") if date else None
                formatted_month = datetime.strftime(datetime(*date[:6]), "%m") if date else None
                formatted_year = datetime.strftime(datetime(*date[:6]), "%Y") if date else None
                formatted_hour = datetime.strftime(datetime(*date[:6]), "%H:%M") if date else None

                print(formatted_date)
                
                formatted_date = str(formatted_date)

                parsed_entries.append({
                    "Title": title,
                    "Date": formatted_date,
                    "Day": int(formatted_day),
                    "Month": int(formatted_month),
                    "Year": int(formatted_year),
                    "Hour": formatted_hour,
                    "URL": url,
                    "Description_all": description,
                    "Description": description_short,
                    "Feed": feed_name,
                })

        return parsed_entries, parsed_feed

def load_feeds(nloads = 0):

    try:
        content, all_data_file = get_json_content("all_data.json")
        all_data = pd.DataFrame(content)

    except:
        all_data = None
        print("no df")

    feeds, file = get_json_content("feeds_dict.json")
    # with open("feeds_dict.json", "r") as f: 
    #     feeds = json.load(f)

    df_feeds = pd.DataFrame(feeds)
    parsed_table = []
    error = 0
    out_time = 0
    feed_broken = 0
    feeds_broken = []

    ui.notification_show("Parsing feeds", 
                        duration=120, 
                        type="message",
                        id="id_parsing"+str(nloads))

    for index, row in df_feeds.iterrows():
        feed_url = row['feed_url']
        feed_name = row['feed_title']
        print(feed_name)
        try:
            parsed_entries, parsed_feed = parse_and_append(feed_url, feed_name, all_data)
            parsed_table.extend(parsed_entries)
        except:
            feed_broken = feed_broken + 1
            feeds_broken.append(feed_name)
            continue

    feeds_df = pd.DataFrame(parsed_table)
    webscraped_df = get_sheet_content("1bN_JcxcndhdX_QL9P2OtPZsyoCmxYJ7SOmZDHga_OCI", "DB_ACTU")
    webscraped_df.to_json("webscrap_df.json")
    final_df = pd.concat([feeds_df, webscraped_df])

    print(final_df)
    print("NUMBER OF ERRORS:")
    print(error)
    print("NUMBER OF OUT_TIME:")
    print(out_time)
    print("FEEDS BROKEN:")
    print(feed_broken)
    print(feeds_broken)

    final_df.to_json("all_data.json",
                      orient="records")
    all_data_file.SetContentFile("all_data.json")
    all_data_file.Upload()
    
    ui.notification_remove(id="id_parsing"+str(nloads))

    return final_df