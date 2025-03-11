import json
from pathlib import Path

path = Path(__file__)
app_dir = path.parent.absolute()
print(app_dir)
app_dir = str(app_dir)

feeds_dict = {}

feeds_dict["feed_title"] = ["Le Soir - Une",
                            "La Libre - Derniers",
                            "RTBF - Général",
                            "RTBF - Local",
                            "RTBF - Belgique",
                            "L'Avenir - Belgique",
                            "L'Avenir - Brabant wallon",
                            "L'Avenir - Bruxelles",
                            "L'Avenir - Wallonie picarde",
                            "L'Avenir - Liège",
                            "L'Avenir - Verviers",
                            "L'Avenir - Charleroi",
                            "L'Avenir - Luxembourg",
                            "L'Avenir - Mons-Centre",
                            "L'Avenir - Basse-Sambre",
                            "L'Avenir - Namur",
                            "L'Avenir - Entre-Sambre-et-Meuse",
                            "L'Avenir - Huy-Waremme",

]

feeds_dict["feed_url"] = ["./rss/lesoir_une.xml",
                          "https://www.lalibre.be/arc/outboundfeeds/rss/?outputType=xml",
                          "https://rss.rtbf.be/article/rss/highlight_rtbf_info.xml",
                          "https://rss.rtbf.be/article/rss/highlight_rtbfinfo_info-regions.xml",
                          "https://rss.rtbf.be/article/rss/highlight_rtbfinfo_info-belgique.xml",
                          "https://www.lavenir.net/arc/outboundfeeds/rss/section/actu/belgique/?outputType=xml",
                          "https://www.lavenir.net/arc/outboundfeeds/rss/section/regions/brabantwallon/?outputType=xml",
                          "https://www.lavenir.net/arc/outboundfeeds/rss/section/regions/bruxelles/?outputType=xml",
                          "https://www.lavenir.net/arc/outboundfeeds/rss/section/regions/wallonie-picarde/?outputType=xml",
                          "https://www.lavenir.net/arc/outboundfeeds/rss/section/regions/liege/?outputType=xml",
                          "https://www.lavenir.net/arc/outboundfeeds/rss/section/regions/verviers/?outputType=xml",
                          "https://www.lavenir.net/arc/outboundfeeds/rss/section/regions/charleroi/?outputType=xml",
                          "https://www.lavenir.net/arc/outboundfeeds/rss/section/regions/luxembourg/?outputType=xml",
                          "https://www.lavenir.net/arc/outboundfeeds/rss/section/regions/mons-centre/?outputType=xml",
                          "https://www.lavenir.net/arc/outboundfeeds/rss/section/regions/basse-sambre/?outputType=xml",
                          "https://www.lavenir.net/arc/outboundfeeds/rss/section/regions/namur/?outputType=xml",
                          "https://www.lavenir.net/arc/outboundfeeds/rss/section/regions/sambre-meuse/?outputType=xml",
                          "https://www.lavenir.net/arc/outboundfeeds/rss/section/regions/huy-waremme/?outputType=xml",
                          
    
]

def make_feed_dict():
    feeds = json.dumps(feeds_dict)
    with open(app_dir + "/feeds_dict.json", "w") as outfile:
        outfile.write(feeds)
    print("FILE WRITTEN")

    
def make_selected_dict():
    feeds = json.dumps(feeds_dict["feed_title"])
    with open(app_dir + "/feeds_selected.json", "w") as outfile:
        outfile.write(feeds)
    print("FILE WRITTEN")

keywords = ["féminicide",
            "homicide",
            "crime passionnel",
            "victime",
            "corps d'une femme",
            "ex-compagnon",
            "ex-mari",
            "femme",
            "meurtre",
            "assassinat",
            ]

def make_keywords_list():
    list = json.dumps(keywords)
    with open(app_dir + "/keywords.json", "w") as outfile:
        outfile.write(list)
    print("FILE WRITTEN")

make_feed_dict()