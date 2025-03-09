import json
from pathlib import Path

path = Path(__file__)
app_dir = path.parent.absolute()
print(app_dir)
app_dir = str(app_dir)

feeds_dict = {}

feeds_dict["feed_title"] = ["Le Soir - Une",
                            "La Libre - Derniers"

]

feeds_dict["feed_url"] = ["./rss/lesoir_une.xml",
                          "https://www.lalibre.be/arc/outboundfeeds/rss/?outputType=xml"
    
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

make_feed_dict()
make_selected_dict()
