import pandas as pd
import feedparser
import json
import re
import asyncio
from datetime import datetime, timedelta
from htmltools import HTML
from shiny import ui

async def waiting_notif(task, message, id_notif): # show a notification popup to give a feedback
    loading_task = asyncio.create_task(task)
    while not loading_task.done():
        ui.notification_show(message, 
                                type='message',
                                duration=3600,
                                id=id_notif)
        await asyncio.sleep(0)
    ui.notification_remove(id=id_notif)
    

def parse_and_append(feed_url, feed_name, error = 0, out_time = 0):
        parsed_feed = feedparser.parse(feed_url)
        parsed_entries = []
        
        back = datetime.now() - timedelta(days=10)

        
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
                    "Feed": feed_name
                })

        return parsed_entries, parsed_feed

def load_feeds(nloads = 0):

    with open("feeds_dict.json", "r") as f: 
        feeds = json.load(f)

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
            parsed_entries, parsed_feed = parse_and_append(feed_url, feed_name)
            parsed_table.extend(parsed_entries)
        except:
            feed_broken = feed_broken + 1
            feeds_broken.append(feed_name)
            continue
        
    parsed_df = pd.DataFrame(parsed_table)
    print(parsed_df)
    parsed_df = parsed_df.sort_values(by=['Year', 'Month', 'Day', 'Hour'], ascending=False)

    print(parsed_df)
    print("NUMBER OF ERRORS:")
    print(error)
    print("NUMBER OF OUT_TIME:")
    print(out_time)
    print("FEEDS BROKEN:")
    print(feed_broken)
    print(feeds_broken)

    ui.notification_remove(id="id_parsing"+str(nloads))

    return parsed_df

class word_position():
    def __init__(self, 
                 word: str,
                 text: str) -> None:
        self.word = word
        self.text = text
        
        match = re.search(word, text)
        self.start = match.start()
        self.end = match.end()

def detect_word(word, text):
    res = text.find(word)
    if res == -1:
         positions = None
    else:
        positions = word_position(word, text)
    
    return positions
     
def highlight(keywords, text):

        highlighted_text = ""
        current_position = 0

        for word in keywords: 
            tag = word
            positions = detect_word(tag, text)
            if positions == None:
                 continue
            
            start_position = positions.start
            end_position = positions.end 

            color = "#fedda2"

            segment = text[current_position:start_position]
            highlighted_text += segment.replace("\n", "<br>")
            
            highlighted_text += (
                f'<span style="background-color:{color}" title="{tag}">'
                + text[start_position:end_position]
                + "</span>"
            )

            current_position = end_position

        highlighted_text += text[current_position:]

        html_output = f"""
            <html>
                <body>
                    <p>{highlighted_text}</p>
                </body>
            </html>
            """
        
        html_output = str(html_output).replace("\n", "</br>")
        
        highlighted = HTML(html_output)

        return highlighted

pos = detect_word("salut", "salut bonjour")
print(pos)