import re

RARITY_MAP = {
    "🔮": "limited",
    "🎐": "celestial",
    "💮": "exclusive",
    "🟡": "legendary",
    "🟠": "rare",
    "🔴": "medium",
    "🔵": "common",
}

EVENT_MAP = {
    "👶": "chibi",
    "👥": "duo",
    "🎮": "game",
    "🤝🏻": "group",
    "📙": "manga/manhua/manhwa",
    "🤝": "trio",

    "⛰": "adventurer",
    "🏀": "basketball",
    "🐎": "cowboy",
    "🐰": "bunny",
    "🎄": "christmas",
    "🎃": "halloween",
    "👘": "kimono",
    "🧹": "maid",
    "🎸": "musician",
    "🚓": "officer",
    "🎒": "school",
    "🏖": "summer",
    "☃️": "winter",

    "🎩": "tuxedo",
    "🏴‍☠️": "pirate",
    "🏁": "racer",
    "🩺": "doctor/nurse",
    "⚽": "soccer",
    "💞": "valentine",
    "🪐": "cosmonaut",

    "🀄️": "abbess",
    "💍": "bride",
    "🎊": "cheerleader",
    "🥻": "saree",
    "🎾": "tennis",
}


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
        event = None
        event_name = None

        event_match = re.search(r"\[(.*?)\]", name_part)

        if event_match:
            emoji = event_match.group(1)
            event = emoji
            event_name = EVENT_MAP.get(emoji, "unknown")
            name_part = re.sub(r"\[.*?\]", "", name_part).strip()
        else:
            for emo, name_val in EVENT_MAP.items():
                if emo in name_part:
                    event = emo
                    event_name = name_val
                    name_part = name_part.replace(emo, "").strip()
                    break

        name = name_part

        # RARITY
        rarity = None
        for emoji, value in RARITY_MAP.items():
            if emoji in text:
                rarity = value
                break

        if not rarity:
            return None, "Rarity not found"

        return {
            "type": ctype,
            "anime": anime,
            "char_id": char_id,
            "name": name,
            "rarity": rarity,
            "event": event,
            "event_name": event_name
        }, None

    except Exception as e:
        return None, f"Parse failed: {str(e)}"
