import re

def parse_caption(text):
    try:
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # TYPE
        if "waifu" in lines[0].lower():
            ctype = "w"
        elif "husbando" in lines[0].lower():
            ctype = "h"
        else:
            return None, "Invalid type"

        # ANIME
        anime = lines[1]

        # ID + NAME
        match = re.match(r"(\d+):\s*(.+)", lines[2])
        if not match:
            return None, "Invalid ID format"

        char_id = int(match.group(1))
        name_part = match.group(2)

        # EVENT
        event_match = re.search(r"\[(.*?)\]", name_part)
        event = f"[{event_match.group(1)}]" if event_match else None

        name = re.sub(r"\[.*?\]", "", name_part).strip()

        # RARITY
        rarity_line = lines[3]
        rarity_match = re.search(r"RARITY:\s*([A-Za-z ]+)", rarity_line, re.IGNORECASE)

        if not rarity_match:
            return None, "Rarity not found"

        rarity = rarity_match.group(1).lower()

        # EVENT NAME
        event_name = None
        if len(lines) >= 5:
            event_name = lines[4]

        return {
            "type": ctype,
            "anime": anime,
            "char_id": char_id,
            "name": name,
            "rarity": rarity,
            "event": event,
            "event_name": event_name
        }, None

    except:
        return None, "Parse failed"
