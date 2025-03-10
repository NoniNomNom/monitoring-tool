import numpy as np
import pandas as pd
import json
from shiny import App, reactive, render, req, ui
from htmltools import HTML, a
from functions import highlight, load_feeds, parse_and_append, waiting_notif

try:
    saved_rows = pd.read_json("kept_rows.json",
                                orient = "records")
except: 
    saved_rows = None

app_ui =ui.page_sidebar(
        ui.sidebar(ui.input_action_button("reload", "Parse feeds", class_="btn-success", width="80%"), 
                   ui.accordion(  
                        ui.accordion_panel("Feeds", 
                                           ui.output_ui("list_feeds")),  
                        ui.accordion_panel("Keywords", 
                                           ui.output_ui("list_keywords")),   
                        id="acc_sidebar",  
                        open=["Feeds", "Keywords"]
                    ),  
                
                   bg="#f8f8f8", 
                   open="open"),

            ui.page_navbar( 
                ui.nav_panel("RSS Feeds",                     
                            ui.layout_columns(
                                ui.card(
                                    ui.output_data_frame("df_all_feeds"),
                                    height="100%"
                                ), 
                                ui.output_ui("description_display"),
                                col_widths=(6, 6),
                                            ),
                            ),
                ui.nav_panel("Saved links",                     
                            ui.layout_columns(
                                ui.card(
                                    ui.output_data_frame("df_saved_links"),
                                    height="100%"
                                ), 
                                ui.card(  
                                    ui.card_header("Description"),
                                    ui.output_ui("description_saved_display"),
                                ), 
                                col_widths=(6, 6),
                                            ),
                            ),
                ui.nav_panel("Manage feeds",
                            ui.layout_columns(  
                                ui.card(
                                    ui.card(ui.input_text("feed_rss", "Add RSS feed"),
                                        ui.input_action_button("add_rss", "Add RSS Feed to the list", class_="btn-success", width="50%")),
                                    ui.card(
                                        ui.output_ui("feeds_to_del")
                                        )
                                    ),
                                ui.card(ui.output_data_frame("df_new_feed")),
                                col_widths=(4, 8),  
                            ),
                            ),
            title="Monitoring",  
            id="page",  
            fillable=True
    ),
    fillable=True
)

def server(input, output, session):

    parsed_df = pd.read_json("all_data.json",
                            orient = "records") # chargement initial des feeds

    # valeurs réactives

    rval_parsed_table = reactive.Value(parsed_df)
    rval_nloads = reactive.Value(0)
    rval_filtered_table = reactive.Value() 
    rval_new_feed_name = reactive.Value("")
    rval_confirmation_delete = reactive.Value(0)
    rval_to_del_rss = reactive.Value("")
    rval_saved_links = reactive.Value(saved_rows)
    rval_saved_table = reactive.Value()
    
    @reactive.effect
    @reactive.event(input.reload)
    async def _():
        await waiting_notif(reload_df(), "Parsing feeds", "reload"+str(rval_nloads()))

    async def reload_df():
        n = rval_nloads() + 1
        df = load_feeds(int(n))
        rval_parsed_table.set(df)

    @render.data_frame
    def df_all_feeds():
        parsed_df = rval_parsed_table()
        feeds_selected = input.checkbox_feeds()

        with open('feeds_selected.json', 'w') as f:
            json.dump(feeds_selected, f)
        print("feeds_selected.json saved")

        df_feeds = parsed_df[parsed_df['Feed'].isin(feeds_selected)]
        keywords_selected = list(input.checkbox_keys())

        with open('keywords_selected.json', 'w') as f:
            json.dump(keywords_selected, f)
        print("keywords_selected.json saved")

        pattern  = "|".join(keywords_selected)
        df = df_feeds[df_feeds['Description'].str.contains(pattern,
                                                           case = False)]
        rval_filtered_table.set(df)
        return render.DataGrid(df.iloc[:,[0,1,9]], 
                                row_selection_mode="single",
                                width="100%")
    
    @reactive.Calc
    def rval_url():
        req(input.df_all_feeds_selected_rows())
        selected_idx = list(input.df_all_feeds_selected_rows())
        print(selected_idx)
        link = rval_filtered_table().iloc[selected_idx]["URL"].values[0]
        return link

    @reactive.Calc
    def rval_hypertext():
        hypertext = HTML('<a href="' + rval_url() + '" target="_blank"><b>Go to url</b></a>')
        return hypertext
        
    @render.ui
    def description_display():
        req(input.df_all_feeds_selected_rows())
        selected_idx = list(input.df_all_feeds_selected_rows())
        print(selected_idx)
        description_all = rval_filtered_table().iloc[selected_idx]["Description_all"].values[0]
        try:
            # description = HTML(description)
            tags = input.checkbox_keys()
            description = highlight(tags, description_all)
        except:
            description = HTML(rval_hypertext())

        description_card = ui.card( 
            ui.card_header("Description"),
            description,
            ui.layout_columns(
                a("Go to URL", class_="btn btn-success", href=rval_url(), target="_blank"),
                ui.input_action_button("keep", "Keep link", class_="btn-warning", width="80%"),
                width=1 / 2,
                ),
            full_screen=True, 
            min_height="100%"

        )
        return description_card

    @render.ui
    def list_feeds():
        parsed_df = rval_parsed_table()
        feeds = list(parsed_df["Feed"])
        feeds = np.array(feeds)
        feeds = np.unique(feeds)
        feeds = list(feeds)
        try:
            with open("feeds_selected.json", "r") as f: 
                feeds_selected = json.load(f)
            print("json loaded")
            
        except:
            feeds_selected = None

        print(feeds_selected)
        checkboxes_feeds = ui.input_checkbox_group(  
            id = "checkbox_feeds",  
            label = "List of feeds",  
            choices = sorted(feeds),
            selected = feeds_selected
            )

        return checkboxes_feeds
    
    @render.ui
    def list_keywords():
        with open("keywords.json", "r") as f: 
            keywords = json.load(f)

        try:
            with open("keywords_selected.json", "r") as f: 
                keywords_selected = json.load(f)
            print("json loaded")
            
        except:
            keywords_selected = None

        print(keywords_selected)

        checkboxes_keywords = ui.input_checkbox_group(  
            id = "checkbox_keys",  
            label = "List of feeds",  
            choices = sorted(keywords),
            selected = sorted(keywords_selected)
            )

        return checkboxes_keywords

    @render.data_frame
    def df_new_feed():
        req(input.feed_rss())
        url = input.feed_rss()
        try: 
            parsed_entries, parsed_feed = parse_and_append(url, feed_name= "")
            feed_name = parsed_feed.feed.get('title', 'Unknown')
            parsed_df = pd.DataFrame(parsed_entries)
            parsed_df["Feed"] = feed_name
            rval_new_feed_name.set(feed_name)
            parsed_df = parsed_df.sort_values(by=['Year', 'Month', 'Day', 'Hour'], ascending=False)
            return render.DataGrid(parsed_df.iloc[:,[0,1,8,9]], 
                                    row_selection_mode="single",
                                    width="100%")
        except:
            return "Could not parse feed"
    
    @reactive.effect
    @reactive.event(input.add_rss)
    def _():
        req(input.feed_rss())
        m = ui.modal(
                ui.card(ui.input_text("new_name", 
                                                "Change name of feed",
                                                value=rval_new_feed_name(),
                                                ),
                        ui.input_action_button("confirm_name", "Add feed")
                                ),
                easy_close=True
                            )
        ui.modal_show(m)

    @reactive.effect
    @reactive.event(input.confirm_name)
    def _():

        with open("feeds_dict.json", "r") as f: 
            feeds = json.load(f)

        if input.new_name() != "":
            feeds["feed_title"].append(input.new_name())
            feeds["feed_url"].append(input.feed_rss())

            with open('feeds_dict.json', 'w') as f:
                json.dump(feeds, f)

            rval_new_feed_name.set("")
            ui.notification_show("Feed added", 
                         duration=2, 
                         type="message",
                         id="feed_added")
            ui.modal_remove()

        else:
            ui.modal_remove()
            m = ui.modal(
            "Impossible to add this feed",
            title=None,
            easy_close=True,
            footer=None)
            ui.modal_show(m)

    @render.ui
    def feeds_to_del():
        with open("feeds_dict.json", "r") as f: 
            feeds = json.load(f)
        if rval_confirmation_delete() == 0:
            ui_del = ui.TagList(
                        ui.input_select("feeds_titles_to_del", 
                            "Select a feed to delete", 
                            sorted(feeds["feed_title"])),
                        ui.input_action_button("del_rss", "Delete RSS feed", class_="btn-warning", width="50%"))
        if rval_confirmation_delete() == 1:
            ui_del = ui.TagList(
                        ui.input_select("feeds_titles_to_del", 
                            "Select a feed to delete", 
                            sorted(feeds["feed_title"]),
                            selected = rval_to_del_rss()),
                        ui.input_action_button("del_rss", "Delete RSS feed", class_="btn-warning", width="50%"),
                        ui.input_action_button("del_rss_confirmation", "Confirm delete", class_="btn-danger", width="50%")
                        )

        
        return ui_del
    
    @reactive.effect
    @reactive.event(input.del_rss)
    def _():
        rval_confirmation_delete.set(1)
        feed_to_del = input.feeds_titles_to_del()
        rval_to_del_rss.set(feed_to_del)
        print(feed_to_del)
        print(rval_confirmation_delete)

    @reactive.effect
    @reactive.event(input.del_rss_confirmation)
    def _():
        with open("feeds_dict.json", "r") as f: 
            feeds = json.load(f)

        feed_to_del = input.feeds_titles_to_del()
        index = feeds["feed_title"].index(feed_to_del)
        del feeds["feed_title"][index]
        del feeds["feed_url"][index]

        with open("feeds_dict.json", "w") as outfile: 
            json.dump(feeds, outfile)

        rval_confirmation_delete.set(0)
        rval_to_del_rss.set("")

        with open("feeds_dict.json", "r") as f: 
            feeds = json.load(f)

        ui.update_select("feeds_titles_to_del", choices = sorted(feeds["feed_title"]))

    @reactive.effect
    @reactive.event(input.keep)
    async def _():
        req(input.df_all_feeds_selected_rows())
        selected_idx = list(input.df_all_feeds_selected_rows())
        print(selected_idx)
        row_kept = list(rval_filtered_table().iloc[selected_idx].values[0])
        print(row_kept)
        df = []
        row_kept = {
                    "Title": row_kept[0],
                    "Date": row_kept[1],
                    "Day": int(row_kept[2]),
                    "Month": int(row_kept[3]),
                    "Year": int(row_kept[4]),
                    "Hour": row_kept[5],
                    "URL": row_kept[6],
                    "Description_all": row_kept[7],
                    "Description": row_kept[8],
                    "Feed": row_kept[9]
                }
        df.append(row_kept)
        saved_rows = rval_saved_links()
        if saved_rows != None:
            df.extend(saved_rows)
        print(df)
        df = pd.DataFrame(df)
        rval_saved_links.set(df)
        df.to_json("kept_rows.json",
                      orient="records")

        rval_saved_links.set(saved_rows)
        print("json saved")

    @render.data_frame
    def df_saved_links():
        df = pd.DataFrame(rval_saved_links())
        df = df.sort_values(by=['Year', 'Month', 'Day', 'Hour'], ascending=False)
        print(df)
        rval_saved_table.set(df)
        return render.DataGrid(df.iloc[:,[0,1,9]], 
                                row_selection_mode="single",
                                width="100%")
       
    @reactive.Calc
    def link_saved_display():
        req(input.df_saved_links_selected_rows())
        selected_idx = list(input.df_saved_links_selected_rows())
        print(selected_idx)
        link = rval_saved_table().iloc[selected_idx]["URL"].values[0]
        link_displayed = HTML('<a href="' + link + '" target="_blank">Go to url</a>')
        return link_displayed
    
    @render.ui
    def description_saved_display():
        req(input.df_saved_links_selected_rows())
        selected_idx = list(input.df_saved_links_selected_rows())
        print(selected_idx)
        description = rval_saved_table().iloc[selected_idx]["Description_all"].values[0]
        try:
            description = HTML(description + '<p>' + link_saved_display())
        except:
            description = HTML(link_saved_display())
        return description

app = App(app_ui, server)
