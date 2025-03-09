from htmltools import HTML
import re

class word_position():
    def __init__(self, 
                 word: str,
                 text: str) -> None:
        self.word = word
        self.text = text
        
        match = re.search(word, text)
        self.start = match.start()
        self.end = match.end()

        
def highlight(tags, text):

        highlighted_text = ""
        current_position = 0

        for tag_list in tags: 
            tag = tag_list[0] # mots
            score = tag_list[1] # inutile
            positions = word_position(tag, text) # récupérer position
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
        
        anonymized = HTML(html_output)

        return anonymized