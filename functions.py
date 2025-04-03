import pandas as pd
import re
import asyncio
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
    lower_text = text.lower()
    lower_word = word.lower()
    res = lower_text.find(lower_word)
    if res == -1:        
        positions = None
    else:
        positions = word_position(lower_word, lower_text)

    return positions
    
def highlight(keywords, text):

        highlighted_text = ""
        current_position = 0

        words_df = pd.DataFrame()

        for word in keywords: 
            tag = word
            positions = detect_word(tag, text)

            if positions == None:
                pass
            else:
                new_row = pd.DataFrame({'word' : [positions.word],
                                        'start': [positions.start],
                                        'end': [positions.end]})
                words_df = pd.concat([words_df, new_row], 
                                     ignore_index=True)

        df = words_df.sort_values(by=['start'])
        print(df)

        for i in range(0, len(df)):

            start_position = df.iloc[i]['start']
            end_position = df.iloc[i]['end']
            
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

def highlight_from_selected_row(input, df, patterns):
    selected_idx = list(input)
    print(selected_idx)
    title = df.iloc[selected_idx]["Title"].values[0]
    description = df.iloc[selected_idx]["Description_all"].values[0]
    description = description.strip()
    description_all = title + '<p>' + description + '</p>'

    try:
        tags = patterns
        description = highlight(tags, description_all)
    except:
        description = HTML(description_all)

    return description