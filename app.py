import pandas as pd
import json
from datetime import datetime
from shiny import App, reactive, render, req, ui
from htmltools import HTML, a
from functions import highlight_from_selected_row, waiting_notif
from fuzzysearch import find_near_matches
from manage_data import get_json_content, get_sheet_content, load_feeds, parse_and_append

today = datetime.today()
lastmonth = datetime.today() - pd.Timedelta(days=15)

app_ui =ui.page_sidebar(
            ui.sidebar(
                ui.input_action_button("reload", "LOAD NEW ARTICLES", class_="btn-success", width="80%"), 
                ui.input_switch("switch_rss", "RSS Feeds", True), 
                ui.input_switch("switch_webscrap", "Webscraping", True), 
                ui.accordion(
                    ui.accordion_panel("Keywords",
                                    ui.input_switch("switch_keys", "Deselect all", True),
                                    ui.output_ui("list_keywords"),
                                    ), 
                    ui.accordion_panel("RSS feeds", 
                                    ui.output_ui("list_feeds")
                                    ), 
                    ui.accordion_panel("Webscraping", 
                                    ui.output_ui("list_webscraping")
                                    ),  
                    id="acc_sidebar",  
                    open=["RSS feeds","Webscraping","Keywords"]
                ),  
            
                bg="#f8f8f8", 
                open="always"),

            ui.page_navbar( 
                ui.nav_panel("Articles",                     
                            ui.layout_columns(
                                ui.card(
                                    ui.input_date_range("slider_dates_range", 
                                        "Dates range",
                                        start = lastmonth,
                                        end = today,
                                        format="dd-mm-yyyy"
                                        ),
                                    ui.output_data_frame("df_all_feeds"),
                                    height="100%"
                                ), 
                                ui.output_ui("description_display"),
                                col_widths=(6, 6),
                                            ),
                            ),
                ui.nav_panel("Saved articles",                     
                            ui.layout_columns(
                                ui.card(
                                    ui.output_data_frame("df_saved_links"),
                                    height="100%"
                                ), 
                                ui.output_ui("description_saved_display"),
                                col_widths=(6, 6),
                                            ),
                            ),
                ui.nav_panel("Manage RSS feeds",
                            ui.layout_columns(  
                                ui.card(
                                    ui.card(
                                        ui.input_text("feed_rss", "Add RSS feed"),
                                        ui.input_action_button("add_rss", "Add RSS Feed to the list", class_="btn-success")
                                        ),
                                    ui.card(
                                        ui.output_ui("feeds_to_del")
                                        )
                                    ),
                                ui.card(
                                    ui.card_header("RSS feed preview"),
                                    ui.output_data_frame("df_new_feed")),
                                col_widths=(6, 6),  
                            ),
                            ),
                ui.nav_panel("Add/Delete keywords",
                                ui.card(
                                    ui.layout_columns(
                                        ui.card(
                                            ui.input_text("new_keyword", "Add keyword"),
                                            ui.input_action_button("add_keyword", "Add keyword", class_="btn-success")
                                            ),
                                        ui.card(
                                            ui.output_ui("keyword_to_del")
                                            ),
                                        col_widths=(6, 6),
                                    ),
                                    ),
                            ),
            title="Monitoring",  
            id="page",  
            fillable=True
    ),
    fillable=True
)

def server(input, output, session):

    try:
        saved_rows, kept_rows_file = get_json_content("kept_rows.json")
        saved_rows = pd.DataFrame(saved_rows)
    except Exception as e:
        print(e) 
        saved_rows = None

    try:
        content, all_data_file = get_json_content("all_data.json")
        parsed_df = pd.DataFrame(content)
        
    except Exception as e:
        print(e)
        parsed_df = pd.DataFrame()

    # initialisation des valeurs réactives

    rval_saved_rows_content = reactive.Value(saved_rows)
    rval_saved_rows_file = reactive.Value(kept_rows_file)
    rval_parsed_table = reactive.Value(parsed_df)
    rval_nloads = reactive.Value(0)
    rval_filtered_table = reactive.Value() 
    rval_new_feed_name = reactive.Value("")
    rval_confirmation_delete = reactive.Value(0)
    rval_to_del_rss = reactive.Value("")
    rval_saved_table = reactive.Value()
    rval_all_patterns = reactive.Value()
    rval_near_keywords = reactive.Value()
    rval_date_last = reactive.Value()
    rval_date_first = reactive.Value()
    rval_date_limit = reactive.Value(lastmonth)
    rval_feeds_selected = reactive.Value()

    # SWITCH BUTTONS 

    @reactive.effect
    @reactive.event(input.switch_rss)
    def _():
        value = input.switch_rss()
        if value:
            feeds, file = get_json_content("feeds_dict.json")
            feeds = list(feeds["feed_title"])
            ui.update_checkbox_group(
                "checkbox_feeds",
                selected=feeds,
            )
        elif not value:
            ui.update_checkbox_group(
                "checkbox_feeds",
                selected=[],
            )

    @reactive.effect
    @reactive.event(input.switch_webscrap)
    def _():
        value = input.switch_webscrap()
        if value:
            df = get_sheet_content("1bN_JcxcndhdX_QL9P2OtPZsyoCmxYJ7SOmZDHga_OCI", "DB_ACTU")
            sites = list(df["Feed"].unique())
            print(sites)
            ui.update_checkbox_group(
                "checkbox_sites",
                selected=sorted(sites),
            )
        elif not value:
            ui.update_checkbox_group(
                "checkbox_sites",
                selected=[],
            )

    @reactive.effect
    @reactive.event(input.switch_keys)
    def _():
        value = input.switch_keys()
        if value:
            keywords, file = get_json_content("keywords.json")
            ui.update_checkbox_group(
                "checkbox_keys",
                selected=sorted(keywords),
            )
            ui.update_switch("switch_keys",
                             label="Deselect all")
        elif not value:
            ui.update_checkbox_group(
                "checkbox_keys",
                selected=[],
            )
            ui.update_switch("switch_keys",
                             label="Select all")
            
    # LOAD/RELOAD DATA FROM RSS FEEDS AND/OR SPREADSHEETS
    
    @reactive.effect
    @reactive.event(input.reload)
    async def _():
        await waiting_notif(reload_df(), "Parsing feeds", "reload"+str(rval_nloads()))

    async def reload_df():
        n = rval_nloads() + 1
        df = load_feeds(int(n))
        near_keys = []
        for description in df['Description_all']:
            for key in list(input.checkbox_keys()):
                try:
                    matches = find_near_matches(key, str(description), 
                                                # max_insertions=0,
                                                # max_deletions=0,
                                                max_l_dist=0)
                    for match in matches:
                        print(match)
                        print(match.matched)
                        near_keys.append(match.matched)
                except Exception as e:
                    print(e)
                    print("error while matching")
        rval_parsed_table.set(df)
        rval_near_keywords.set(near_keys)

    # SHOW FILTERED DATA              

    @reactive.effect
    @reactive.event(input.slider_dates_range)
    def _():
        range_dates = input.slider_dates_range()
        rval_date_limit.set(range_dates[0])

    @render.data_frame
    def df_all_feeds():
        parsed_df = rval_parsed_table()

        feeds_selected, file = get_json_content("feeds_selected.json")
        feeds_selected = input.checkbox_feeds()
        with open('feeds_selected.json', 'w') as f:
            json.dump(feeds_selected, f)
        file.SetContentFile('feeds_selected.json')
        file.Upload()

        feeds_selected = input.checkbox_feeds()

        sites_selected = input.checkbox_sites()
        selected = list(feeds_selected) + list(sites_selected)
        rval_feeds_selected.set(selected)

        filtered_df = parsed_df[parsed_df['Feed'].isin(selected)] 

        keywords_selected = list(input.checkbox_keys())

        all_patterns = keywords_selected
        set_patterns = list(set(all_patterns))
        if len(set_patterns) < 1:
            ui.notification_show("0 keyword selected", 
                                type='warning',
                                duration=5,
                                id="id_no_key")
            df = filtered_df
        else: 
            rval_all_patterns.set(set_patterns)
            pattern  = "|".join(set_patterns)
            print(pattern)
            filtered_df = filtered_df.dropna()
            df = filtered_df[filtered_df['Description_all'].str.contains(pattern,
                                                            case = False)]
            
        df = df.drop_duplicates(subset=['Title'])
        
        df['Date'] = pd.to_datetime(df['Date'], 
                                    dayfirst=True)
        date_last = df['Date'].max()
        rval_date_last.set(date_last)
        date_first = df['Date'].min()
        rval_date_first.set(date_first)

        df = df.sort_values(by='Date', ascending=False)

        date_limit = rval_date_limit().strftime("%d-%m-%Y - %H:%M")

        df['Date'] = df['Date'].dt.strftime("%d-%m-%Y - %H:%M")

        print(df['Date'])

        df = df[df['Date'] > date_limit]

        rval_filtered_table.set(df)
        return render.DataGrid(df.iloc[:,[0,1,9]], 
                                row_selection_mode="single",
                                width="100%")
    
    # SHOW DESCRIPTION

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

        description = highlight_from_selected_row(
            input= input.df_all_feeds_selected_rows(),
            df = rval_filtered_table(),
            patterns = rval_all_patterns()
        )

        description_card = ui.card( 
            ui.card_header("Description"),
            ui.layout_columns(
                a("Go to URL", class_="btn btn-success", href=rval_url(), target="_blank"),
                ui.input_action_button("keep", "Save", class_="btn-warning"),
                width=1 / 2,
                ),
            description,
            full_screen=True, 
            # min_height="100%"

        )
        return description_card

# KEYWORDS MANAGEMENT
    
    @render.ui
    def list_keywords():
        keywords, file = get_json_content("keywords.json")

        checkboxes_keywords = ui.input_checkbox_group(  
            id = "checkbox_keys",  
            label = "List of keywords",  
            choices = sorted(keywords),
            selected = sorted(keywords)
            )

        return checkboxes_keywords
    
    @reactive.effect
    @reactive.event(input.add_keyword)
    def _():

        keys, file = get_json_content("keywords.json")

        if input.new_keyword() != "":
            keys.append(input.new_keyword())
            with open('keywords.json', 'w') as f:
                json.dump(keys, f)
            file.SetContentFile('keywords.json') 
            file.Upload()

            ui.notification_show("Keyword added", 
                         duration=2, 
                         type="message",
                         id="key_added")
            ui.modal_remove()

            try:
                keywords_selected, file = get_json_content("keywords_selected.json")
                print("json loaded")
                
            except Exception as e:
                print(e)
                keywords_selected = None

            ui.update_checkbox_group(  
                id = "checkbox_keys",  
                label = "List of keywords",  
                choices = sorted(keys),
                selected=keywords_selected
                )

        else:
            ui.modal_remove()
            m = ui.modal(
            "Impossible to add this keyword",
            title=None,
            easy_close=True,
            footer=None)
            ui.modal_show(m)

    @render.ui
    def keyword_to_del():
        keys, file = get_json_content("keywords.json")

        ui_del = ui.TagList(
            ui.input_select("keys_to_del", 
                "Select a keyword to delete", 
                sorted(keys),
                ),
            ui.input_action_button("del_key", "Delete keyword", class_="btn-warning"),
            ) 
        
        return ui_del
    
    @reactive.effect
    @reactive.event(input.del_key)
    def _():
        keys, file = get_json_content("keywords.json")

        key_to_del = input.keys_to_del()
        index = keys.index(key_to_del)
        del keys[index]

        with open('keywords.json', 'w') as f:
            json.dump(keys, f)
        file.SetContentFile('keywords.json') 
        file.Upload()

        rval_confirmation_delete.set(0)
        rval_to_del_rss.set("")

        keys, file = get_json_content("keywords.json")

        ui.update_select("keys_to_del", choices = sorted(keys))
    
# FEEDS MANAGEMENT

    @render.ui
    def list_feeds():
        try:

            feeds, file = get_json_content("feeds_dict.json")
            feeds = list(feeds["feed_title"])
            
            try:
                feeds_selected, file = get_json_content("feeds_selected.json")
                print("json loaded")
                
            except Exception as e:
                print(e)
                feeds_selected = None

            print(feeds_selected)
    
            checkboxes_feeds = ui.input_checkbox_group(  
                id = "checkbox_feeds",  
                label = "List of feeds",  
                choices = sorted(feeds),
                selected = feeds_selected
                )
        except Exception as e:
            print(e)
            checkboxes_feeds = ui.input_checkbox_group(  
                id = "checkbox_feeds",  
                label = "No feed",  
                choices = [],
                selected = []
                )
    
        return checkboxes_feeds
    
    @render.ui
    def list_webscraping():
        try:

            df = get_sheet_content("1bN_JcxcndhdX_QL9P2OtPZsyoCmxYJ7SOmZDHga_OCI", "DB_ACTU")
            sites = list(df["Feed"].unique())
    
            checkboxes_feeds = ui.input_checkbox_group(  
                id = "checkbox_sites",  
                label = "List of sites",  
                choices = sorted(sites),
                selected = sorted(sites)
                )
        except Exception as e:
            print(e)
            checkboxes_feeds = ui.input_checkbox_group(  
                id = "checkbox_sites",  
                label = "No site",  
                choices = [],
                selected = []
                )
    
        return checkboxes_feeds

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
            parsed_df = parsed_df.sort_values(by=['Date'], ascending=False)
            return render.DataGrid(parsed_df.iloc[:,[0,1,8,9]], 
                                    row_selection_mode="single",
                                    width="100%")
        except Exception as e:
            print(e)
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
                        ui.input_action_button(
                            "confirm_name", 
                            "Add feed")
                                ),
                easy_close=True
                            )
        ui.modal_show(m)

    @reactive.effect
    @reactive.event(input.confirm_name)
    def _():
        feeds, file = get_json_content("feeds_dict.json")

        if input.new_name() != "":
            feeds["feed_title"].append(input.new_name())
            feeds["feed_url"].append(input.feed_rss())

            with open('feeds_dict.json', 'w') as f:
                json.dump(feeds, f)
            file.SetContentFile('feeds_dict.json') 
            file.Upload()

            rval_new_feed_name.set("")

            ui.update_checkbox_group(  
                id = "checkbox_feeds",  
                choices = sorted(list(feeds["feed_title"])),
                selected=rval_feeds_selected()
                )
            
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
        feeds, file = get_json_content("feeds_dict.json")
        
        if rval_confirmation_delete() == 0:
            ui_del = ui.TagList(
                        ui.input_select("feeds_titles_to_del", 
                            "Select a feed to delete", 
                            sorted(feeds["feed_title"])),
                        ui.input_action_button("del_rss", "Delete RSS feed", class_="btn-warning"))
        if rval_confirmation_delete() == 1:
            ui_del = ui.TagList(
                        ui.input_select("feeds_titles_to_del", 
                            "Select a feed to delete", 
                            sorted(feeds["feed_title"]),
                            selected = rval_to_del_rss()),
                        ui.input_action_button("del_rss", "Delete RSS feed", class_="btn-warning"),
                        ui.input_action_button("del_rss_confirmation", "Confirm delete", class_="btn-danger")
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
        feeds, file = get_json_content("feeds_dict.json")

        feed_to_del = input.feeds_titles_to_del()
        index = feeds["feed_title"].index(feed_to_del)
        del feeds["feed_title"][index]
        del feeds["feed_url"][index]

        with open('feeds_dict.json', 'w') as f:
            json.dump(feeds, f)
        file.SetContentFile('feeds_dict.json') 
        file.Upload()

        rval_confirmation_delete.set(0)
        rval_to_del_rss.set("")

        feeds, file = get_json_content("feeds_dict.json")

        ui.update_select("feeds_titles_to_del", choices = sorted(feeds))

        ui.update_checkbox_group(  
                id = "checkbox_feeds",  
                choices = sorted(list(feeds["feed_title"])),
                selected=rval_feeds_selected()
                )

    # save a row/link/article

    @reactive.effect
    @reactive.event(input.keep)
    async def _():
        req(input.df_all_feeds_selected_rows())
        selected_idx = list(input.df_all_feeds_selected_rows())
        print(selected_idx)
        row_kept = list(rval_filtered_table().iloc[selected_idx].values[0])
        print(row_kept)
        df = rval_saved_rows_content()
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
        row_kept = pd.DataFrame([row_kept])
        concat_df = pd.concat([df, row_kept])
        concat_df['Date'] = pd.to_datetime(concat_df['Date'], 
                                        dayfirst=True)
        concat_df = concat_df.sort_values(by='Date', ascending=False)
        concat_df['Date'] = concat_df['Date'].dt.strftime('%d-%m-%Y - %H:%M')
        rval_saved_rows_content.set(concat_df)
        file = rval_saved_rows_file()
        concat_df.to_json("kept_rows.json", orient="records")
        file.SetContentFile("kept_rows.json")
        file.Upload()
        print("json saved")
        ui.notification_show("Article saved", 
                                type='message',
                                duration=5,
                                id="id_keep_feed")

    @render.data_frame
    def df_saved_links():
        df = pd.DataFrame(rval_saved_rows_content())
        print(df)
        rval_saved_table.set(df)
        return render.DataGrid(df.iloc[:,[0,1,9]], 
                                row_selection_mode="single",
                                width="100%")


    @reactive.Calc
    def rval_saved_url():
        req(input.df_saved_links_selected_rows())
        selected_idx = list(input.df_saved_links_selected_rows())
        print(selected_idx)
        link = rval_saved_table().iloc[selected_idx]["URL"].values[0]
        return link

    @reactive.Calc
    def rval_saved_hypertext():
        hypertext = HTML('<a href="' + rval_saved_url() + '" target="_blank"><b>Go to url</b></a>')
        return hypertext
    
    @render.ui
    def description_saved_display():
        req(input.df_saved_links_selected_rows())

        description = highlight_from_selected_row(
            input= input.df_saved_links_selected_rows(),
            df = rval_saved_table(),
            patterns = rval_all_patterns()
        )

        description_card = ui.card( 
            ui.card_header("Description"),
            ui.layout_columns(
                a("Go to URL", class_="btn btn-success", href=rval_saved_url(), target="_blank"),
                ui.input_action_button("delete_link", "Delete", class_="btn-warning"),
                width=1 / 2,
                ),
            description,
            full_screen=True, 
        )
        return description_card

    @reactive.effect
    @reactive.event(input.delete_link)
    async def _():
        req(input.df_saved_links_selected_rows())
        selected_idx = list(input.df_saved_links_selected_rows())
        df = pd.DataFrame(rval_saved_rows_content())
        df = df.reset_index(drop=True)
        print(df)
        df = df.drop(index = selected_idx, axis = 0)
        print(df)
        rval_saved_rows_content.set(df)
        file = rval_saved_rows_file()
        df.to_json("kept_rows.json")
        file.SetContentFile("kept_rows.json")
        file.Upload()
        


app = App(app_ui, server)
