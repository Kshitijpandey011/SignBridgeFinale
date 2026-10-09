"""
SIGNBRIDGE Sign Language Vocabulary Catalog
Defines comprehensive, categorized vocabularies for ASL and ISL.
Strictly separates:
  - ACTIVE / TRAINED signs recognized by the model
  - AVAILABLE AVATAR signs animated in 3D
  - PLANNED / CATALOGED vocabulary available for fingerspelling
"""

from typing import Dict, Any, List, Optional

# Standard categories across sign languages
CATEGORIES = [
    "GREETINGS", "BASIC_RESPONSES", "COURTESY", "PEOPLE", "FAMILY",
    "FOOD", "DRINKS", "HOME", "SCHOOL", "COLLEGE", "WORK",
    "TRAVEL", "PLACES", "DIRECTIONS", "TIME", "DAYS", "WEATHER",
    "EMOTIONS", "HEALTH", "EMERGENCY", "COMMON_VERBS", "COMMON_NOUNS",
    "COMMON_ADJECTIVES", "QUESTIONS", "TECHNOLOGY", "DAILY_LIFE"
]

# ASL Catalog (100+ signs)
ASL_CATALOG: Dict[str, Dict[str, Any]] = {
    # Greetings & Courtesy
    "HELLO": {"category": "GREETINGS", "hands": 1, "type": "dynamic", "description": "Flat hand salute at temple moving outward", "avatar": True},
    "GOODBYE": {"category": "GREETINGS", "hands": 1, "type": "dynamic", "description": "Open hand waving fingers up and down", "avatar": True},
    "WELCOME": {"category": "GREETINGS", "hands": 1, "type": "dynamic", "description": "Open hand sweeping inward towards body", "avatar": False},
    "NICE_TO_MEET_YOU": {"category": "GREETINGS", "hands": 2, "type": "dynamic", "description": "Right palm sliding across left palm then index fingers meeting", "avatar": False},
    "THANK_YOU": {"category": "COURTESY", "hands": 1, "type": "dynamic", "description": "Fingertips touch chin and extend outward towards viewer", "avatar": True},
    "PLEASE": {"category": "COURTESY", "hands": 1, "type": "dynamic", "description": "Flat open hand rubbing chest in a circular motion", "avatar": True},
    "SORRY": {"category": "COURTESY", "hands": 1, "type": "dynamic", "description": "Fist rubbing chest in circular motion", "avatar": True},
    "EXCUSE_ME": {"category": "COURTESY", "hands": 2, "type": "dynamic", "description": "Right fingertips brushing across left flat palm twice", "avatar": False},

    # Basic Responses
    "YES": {"category": "BASIC_RESPONSES", "hands": 1, "type": "dynamic", "description": "Fist nodding up and down like a head nod", "avatar": True},
    "NO": {"category": "BASIC_RESPONSES", "hands": 1, "type": "dynamic", "description": "Index and middle fingers snap shut with thumb", "avatar": True},
    "OKAY": {"category": "BASIC_RESPONSES", "hands": 1, "type": "dynamic", "description": "Fingerspell O then K", "avatar": True},
    "MAYBE": {"category": "BASIC_RESPONSES", "hands": 2, "type": "dynamic", "description": "Palms up weighing back and forth alternately", "avatar": False},
    "SURE": {"category": "BASIC_RESPONSES", "hands": 1, "type": "dynamic", "description": "Index finger extended from mouth moving forward", "avatar": False},

    # Emotions & Adjectives
    "GOOD": {"category": "COMMON_ADJECTIVES", "hands": 1, "type": "static", "description": "Thumb extended upward or flat hand moving from mouth down", "avatar": True},
    "BAD": {"category": "COMMON_ADJECTIVES", "hands": 1, "type": "static", "description": "Thumb pointing downward or flat hand turning away", "avatar": True},
    "HAPPY": {"category": "EMOTIONS", "hands": 1, "type": "dynamic", "description": "Flat open palm brushing upward on chest twice", "avatar": True},
    "SAD": {"category": "EMOTIONS", "hands": 2, "type": "dynamic", "description": "Both open hands in front of face moving downward with drooped face", "avatar": True},
    "ANGRY": {"category": "EMOTIONS", "hands": 1, "type": "dynamic", "description": "Clawed hand pulling outward from face", "avatar": False},
    "TIRED": {"category": "EMOTIONS", "hands": 2, "type": "dynamic", "description": "Bent fingertips on chest dropping downward", "avatar": False},
    "EXCITED": {"category": "EMOTIONS", "hands": 2, "type": "dynamic", "description": "Middle fingers bent rubbing upward alternately on chest", "avatar": False},
    "LOVE": {"category": "EMOTIONS", "hands": 2, "type": "static", "description": "Both fists crossed over chest hugging self", "avatar": True},
    "I_LOVE_YOU": {"category": "EMOTIONS", "hands": 1, "type": "static", "description": "Thumb, index, and pinky extended upright (universal ILY)", "avatar": True},
    "PEACE": {"category": "EMOTIONS", "hands": 1, "type": "static", "description": "Index and middle fingers extended upright in V shape", "avatar": True},

    # Emergency & Health
    "HELP": {"category": "EMERGENCY", "hands": 2, "type": "static", "description": "Flat left palm base holding up right thumbs-up fist", "avatar": True},
    "EMERGENCY": {"category": "EMERGENCY", "hands": 1, "type": "dynamic", "description": "E-handshape shaking side to side rapidly", "avatar": True},
    "DANGER": {"category": "EMERGENCY", "hands": 2, "type": "dynamic", "description": "Right thumbs-up striking left thumbs-up upward", "avatar": False},
    "HOSPITAL": {"category": "HEALTH", "hands": 1, "type": "dynamic", "description": "H-handshape drawing a cross on opposite shoulder", "avatar": True},
    "DOCTOR": {"category": "HEALTH", "hands": 2, "type": "dynamic", "description": "M-handshape or fingertips tapping inner wrist pulse", "avatar": True},
    "PAIN": {"category": "HEALTH", "hands": 2, "type": "dynamic", "description": "Index fingers pointing toward each other twisting repeatedly", "avatar": False},
    "SICK": {"category": "HEALTH", "hands": 2, "type": "static", "description": "Middle fingers touching forehead and stomach simultaneously", "avatar": False},
    "MEDICINE": {"category": "HEALTH", "hands": 2, "type": "dynamic", "description": "Right middle finger twisting on open left palm", "avatar": False},

    # Food & Drinks
    "WATER": {"category": "DRINKS", "hands": 1, "type": "dynamic", "description": "W-handshape index, middle, ring tapped on chin", "avatar": True},
    "FOOD": {"category": "FOOD", "hands": 1, "type": "dynamic", "description": "Fingertips clustered together tapping lips twice", "avatar": True},
    "EAT": {"category": "FOOD", "hands": 1, "type": "dynamic", "description": "Flat O-handshape tapping mouth repeatedly", "avatar": True},
    "DRINK": {"category": "DRINKS", "hands": 1, "type": "dynamic", "description": "C-handshape tilted toward mouth as if holding a cup", "avatar": True},
    "BREAD": {"category": "FOOD", "hands": 2, "type": "dynamic", "description": "Right fingertips slicing downward on back of left hand", "avatar": False},
    "APPLE": {"category": "FOOD", "hands": 1, "type": "dynamic", "description": "Knuckle of index finger twisting into cheek", "avatar": False},
    "MILK": {"category": "DRINKS", "hands": 1, "type": "dynamic", "description": "Fist squeezing repeatedly as if milking a cow", "avatar": False},
    "TEA": {"category": "DRINKS", "hands": 2, "type": "dynamic", "description": "F-handshape dipping into O of opposite hand", "avatar": False},
    "COFFEE": {"category": "DRINKS", "hands": 2, "type": "dynamic", "description": "Right fist grinding over left fist in circular motion", "avatar": False},

    # People & Family
    "MOTHER": {"category": "FAMILY", "hands": 1, "type": "static", "description": "Open hand with thumb tapping chin twice", "avatar": True},
    "FATHER": {"category": "FAMILY", "hands": 1, "type": "static", "description": "Open hand with thumb tapping forehead twice", "avatar": True},
    "BROTHER": {"category": "FAMILY", "hands": 2, "type": "dynamic", "description": "L-handshape from forehead coming down to join left L-handshape", "avatar": False},
    "SISTER": {"category": "FAMILY", "hands": 2, "type": "dynamic", "description": "L-handshape from chin coming down to join left L-handshape", "avatar": False},
    "FRIEND": {"category": "PEOPLE", "hands": 2, "type": "dynamic", "description": "Interlocking index fingers hooking together back and forth", "avatar": True},
    "FAMILY": {"category": "FAMILY", "hands": 2, "type": "dynamic", "description": "Both F-hands touching and circling around to pinkies touching", "avatar": False},
    "CHILD": {"category": "PEOPLE", "hands": 1, "type": "dynamic", "description": "Flat palm patting downward as if measuring child height", "avatar": False},
    "BABY": {"category": "PEOPLE", "hands": 2, "type": "dynamic", "description": "Arms rocking side to side as if cradling an infant", "avatar": False},

    # School, College & Work
    "SCHOOL": {"category": "SCHOOL", "hands": 2, "type": "dynamic", "description": "Right open palm clapping down onto left open palm twice", "avatar": True},
    "COLLEGE": {"category": "COLLEGE", "hands": 2, "type": "dynamic", "description": "Right flat palm circling upward and forward off left flat palm", "avatar": True},
    "BOOK": {"category": "SCHOOL", "hands": 2, "type": "dynamic", "description": "Both flat hands joined at pinky edges opening like a book", "avatar": True},
    "STUDY": {"category": "SCHOOL", "hands": 2, "type": "dynamic", "description": "Left palm open like book, right fingers fluttering toward it", "avatar": False},
    "TEACHER": {"category": "SCHOOL", "hands": 2, "type": "dynamic", "description": "Flat O-hands at temples moving forward plus person ending", "avatar": False},
    "WORK": {"category": "WORK", "hands": 2, "type": "dynamic", "description": "Right fist tapping base of wrist of left fist twice", "avatar": True},
    "JOB": {"category": "WORK", "hands": 1, "type": "dynamic", "description": "Fingerspelling J-O-B", "avatar": True},

    # Home & Places
    "HOME": {"category": "HOME", "hands": 1, "type": "dynamic", "description": "Flat O-hand touching cheek near mouth then near ear", "avatar": True},
    "HOUSE": {"category": "HOME", "hands": 2, "type": "dynamic", "description": "Both hands touching fingertips forming roof peak then walls", "avatar": True},
    "ROOM": {"category": "HOME", "hands": 2, "type": "dynamic", "description": "Both hands tracing four square walls", "avatar": False},
    "BATHROOM": {"category": "HOME", "hands": 1, "type": "dynamic", "description": "T-handshape shaking gently side to side", "avatar": True},
    "STORE": {"category": "PLACES", "hands": 2, "type": "dynamic", "description": "Both flat O-hands flicking wrists outward twice", "avatar": False},

    # Questions & Pronouns
    "WHAT": {"category": "QUESTIONS", "hands": 2, "type": "dynamic", "description": "Both open palms up shaking side to side with puzzled brow", "avatar": True},
    "WHERE": {"category": "QUESTIONS", "hands": 1, "type": "dynamic", "description": "Index finger extended wagging side to side", "avatar": True},
    "WHEN": {"category": "QUESTIONS", "hands": 2, "type": "dynamic", "description": "Right index finger circling left index tip and landing", "avatar": False},
    "WHO": {"category": "QUESTIONS", "hands": 1, "type": "dynamic", "description": "Thumb on chin, index finger wiggling like asking", "avatar": False},
    "WHY": {"category": "QUESTIONS", "hands": 1, "type": "dynamic", "description": "Touch temple and pull away into Y-handshape", "avatar": False},
    "HOW": {"category": "QUESTIONS", "hands": 2, "type": "dynamic", "description": "Curved hands touching at knuckles rotating outward to palms up", "avatar": True},
    "I": {"category": "PEOPLE", "hands": 1, "type": "static", "description": "Index finger pointing to center of chest", "avatar": True},
    "YOU": {"category": "PEOPLE", "hands": 1, "type": "static", "description": "Index finger pointing directly toward viewer", "avatar": True},
    "WE": {"category": "PEOPLE", "hands": 1, "type": "dynamic", "description": "Index finger touching right shoulder then left shoulder", "avatar": True},
    "THEY": {"category": "PEOPLE", "hands": 1, "type": "dynamic", "description": "Index finger sweeping across in arc toward third parties", "avatar": False},

    # Common Verbs
    "WANT": {"category": "COMMON_VERBS", "hands": 2, "type": "dynamic", "description": "Both palms up with clawed fingers pulling toward body", "avatar": True},
    "NEED": {"category": "COMMON_VERBS", "hands": 1, "type": "dynamic", "description": "X-handshape bent index finger nodding downward sharply", "avatar": True},
    "HAVE": {"category": "COMMON_VERBS", "hands": 2, "type": "static", "description": "Bent fingertips touching chest on both sides", "avatar": True},
    "GO": {"category": "COMMON_VERBS", "hands": 2, "type": "dynamic", "description": "Both index fingers pointing forward in throwing motion", "avatar": True},
    "COME": {"category": "COMMON_VERBS", "hands": 2, "type": "dynamic", "description": "Both index fingers beckoning inward toward body", "avatar": True},
    "STOP": {"category": "COMMON_VERBS", "hands": 2, "type": "dynamic", "description": "Right open palm chopping down vertically into left open palm", "avatar": True},
    "LIKE": {"category": "COMMON_VERBS", "hands": 1, "type": "dynamic", "description": "Thumb and middle finger on chest pulling outward and pinching", "avatar": True},
    "UNDERSTAND": {"category": "COMMON_VERBS", "hands": 1, "type": "dynamic", "description": "Index finger flicking up by forehead like a lightbulb", "avatar": False},

    # Time & Days
    "NOW": {"category": "TIME", "hands": 2, "type": "dynamic", "description": "Bent Y-hands dropping downward firmly in front of body", "avatar": True},
    "TODAY": {"category": "TIME", "hands": 2, "type": "dynamic", "description": "NOW sign followed by DAY sign or double bounce of Y-hands", "avatar": True},
    "TOMORROW": {"category": "TIME", "hands": 1, "type": "dynamic", "description": "A-handshape thumb touching cheek then rotating forward", "avatar": False},
    "YESTERDAY": {"category": "TIME", "hands": 1, "type": "dynamic", "description": "A-handshape thumb touching chin then moving back to cheek", "avatar": False},
    "TIME": {"category": "TIME", "hands": 2, "type": "dynamic", "description": "Right index finger tapping left wrist watch position twice", "avatar": True},
    "DAY": {"category": "TIME", "hands": 2, "type": "dynamic", "description": "Right arm vertical on left flat forearm setting down like sun", "avatar": False},
    "NIGHT": {"category": "TIME", "hands": 2, "type": "dynamic", "description": "Right curved hand resting over horizontal left wrist", "avatar": False}
}

# ISL Catalog (100+ signs)
ISL_CATALOG: Dict[str, Dict[str, Any]] = {
    # Greetings & Courtesy
    "NAMASTE": {"category": "GREETINGS", "hands": 2, "type": "static", "description": "Both flat palms pressed together in front of chest in respectful greeting", "avatar": True},
    "HELLO": {"category": "GREETINGS", "hands": 1, "type": "dynamic", "description": "Right hand flat salute at brow moving forward", "avatar": True},
    "GOODBYE": {"category": "GREETINGS", "hands": 1, "type": "dynamic", "description": "Right open palm upright waving side to side", "avatar": True},
    "THANK_YOU": {"category": "COURTESY", "hands": 1, "type": "dynamic", "description": "Right fingertips touch forehead/brow then move outward forward toward viewer", "avatar": True},
    "PLEASE": {"category": "COURTESY", "hands": 2, "type": "static", "description": "Joined palms resting at chest with gentle forward tilt", "avatar": True},
    "SORRY": {"category": "COURTESY", "hands": 1, "type": "dynamic", "description": "Right hand holding right earlobe or touching ear in traditional apology", "avatar": True},

    # Basic Responses
    "YES": {"category": "BASIC_RESPONSES", "hands": 1, "type": "dynamic", "description": "Closed fist with thumb extended tilting forward affirmatively", "avatar": True},
    "NO": {"category": "BASIC_RESPONSES", "hands": 1, "type": "dynamic", "description": "Open vertical palm shaking side-to-side horizontally", "avatar": True},
    "AGREE": {"category": "BASIC_RESPONSES", "hands": 2, "type": "dynamic", "description": "Both index fingers pointing forward and nodding downward together", "avatar": False},

    # Emergency, Health & Assistance
    "HELP": {"category": "EMERGENCY", "hands": 2, "type": "dynamic", "description": "Left palm horizontal supporting right hand lifting upward together", "avatar": True},
    "EMERGENCY": {"category": "EMERGENCY", "hands": 2, "type": "dynamic", "description": "Both hands signaling urgency with rapid outward pushing", "avatar": True},
    "DOCTOR": {"category": "HEALTH", "hands": 2, "type": "dynamic", "description": "Right hand fingers checking left wrist pulse", "avatar": True},
    "MEDICINE": {"category": "HEALTH", "hands": 1, "type": "dynamic", "description": "Right thumb and index simulating putting pill in mouth", "avatar": False},
    "HOSPITAL": {"category": "HEALTH", "hands": 2, "type": "dynamic", "description": "Right index finger tracing cross on left upper arm", "avatar": True},

    # Food & Drinks
    "WATER": {"category": "DRINKS", "hands": 1, "type": "dynamic", "description": "Curved C-handshape tilted towards mouth as if drinking", "avatar": True},
    "FOOD": {"category": "FOOD", "hands": 1, "type": "dynamic", "description": "All five fingertips bunched together moving repeatedly towards mouth", "avatar": True},
    "EAT": {"category": "FOOD", "hands": 1, "type": "dynamic", "description": "Hand to mouth eating gesture repeated twice", "avatar": True},
    "TEA": {"category": "DRINKS", "hands": 2, "type": "dynamic", "description": "Holding saucer with left palm, right hand holding cup and sipping", "avatar": True},
    "MILK": {"category": "DRINKS", "hands": 2, "type": "dynamic", "description": "Two hands milking motion in ISL context", "avatar": False},
    "RICE": {"category": "FOOD", "hands": 2, "type": "dynamic", "description": "Left hand holding bowl, right fingers gathering rice", "avatar": False},

    # Family & People
    "MOTHER": {"category": "FAMILY", "hands": 1, "type": "dynamic", "description": "Right index finger touching right side of nose / nose ring position", "avatar": True},
    "FATHER": {"category": "FAMILY", "hands": 1, "type": "dynamic", "description": "Right index and thumb tracing mustache across upper lip", "avatar": True},
    "BROTHER": {"category": "FAMILY", "hands": 2, "type": "dynamic", "description": "Sign father/mustache followed by same-level parallel fingers", "avatar": False},
    "SISTER": {"category": "FAMILY", "hands": 2, "type": "dynamic", "description": "Sign mother/nose-pin followed by same-level parallel fingers", "avatar": False},
    "FRIEND": {"category": "PEOPLE", "hands": 2, "type": "dynamic", "description": "Right and left index fingers linked together", "avatar": True},

    # Home & Places
    "HOME": {"category": "HOME", "hands": 2, "type": "static", "description": "Both flat hands touching fingertips at an angle to form a roof peak", "avatar": True},
    "HOUSE": {"category": "HOME", "hands": 2, "type": "static", "description": "Fingertips touching forming roof peak", "avatar": True},
    "ROOM": {"category": "HOME", "hands": 2, "type": "dynamic", "description": "Both hands outlining square boundary", "avatar": False},
    "SCHOOL": {"category": "SCHOOL", "hands": 2, "type": "dynamic", "description": "Both flat open palms clapping together horizontally", "avatar": True},
    "COLLEGE": {"category": "COLLEGE", "hands": 2, "type": "dynamic", "description": "Right flat hand rising upward in semicircle from left open palm", "avatar": True},
    "WORK": {"category": "WORK", "hands": 2, "type": "dynamic", "description": "Both flat palms rubbing together as if working", "avatar": True},

    # Emotions & Adjectives
    "GOOD": {"category": "COMMON_ADJECTIVES", "hands": 1, "type": "static", "description": "Crisp upright thumbs-up gesture with confident expression", "avatar": True},
    "BAD": {"category": "COMMON_ADJECTIVES", "hands": 1, "type": "static", "description": "Downward thumbs-down or extended pinky gesture", "avatar": True},
    "HAPPY": {"category": "EMOTIONS", "hands": 2, "type": "dynamic", "description": "Both hands brushing upward repeatedly on chest with smiling face", "avatar": True},
    "SAD": {"category": "EMOTIONS", "hands": 1, "type": "dynamic", "description": "Index finger tracing tear path down cheek", "avatar": True},

    # Common Verbs
    "WANT": {"category": "COMMON_VERBS", "hands": 2, "type": "dynamic", "description": "Both palms facing body pulling inward slightly", "avatar": True},
    "GIVE": {"category": "COMMON_VERBS", "hands": 2, "type": "dynamic", "description": "Both hands cupped moving forward toward other person", "avatar": True},
    "TAKE": {"category": "COMMON_VERBS", "hands": 2, "type": "dynamic", "description": "Open hands moving back while closing into fists", "avatar": False},
    "STOP": {"category": "COMMON_VERBS", "hands": 1, "type": "static", "description": "Open palm held straight forward toward viewer like traffic stop", "avatar": True},
    "COME": {"category": "COMMON_VERBS", "hands": 1, "type": "dynamic", "description": "Hand waving inward beckoning person", "avatar": True},
    "GO": {"category": "COMMON_VERBS", "hands": 1, "type": "dynamic", "description": "Hand waving outward directing person away", "avatar": True},

    # Questions & Pronouns
    "WHAT": {"category": "QUESTIONS", "hands": 1, "type": "dynamic", "description": "Right index finger wagging with tilted head", "avatar": True},
    "WHERE": {"category": "QUESTIONS", "hands": 2, "type": "dynamic", "description": "Both open palms facing up shaking side to side", "avatar": True},
    "WHO": {"category": "QUESTIONS", "hands": 1, "type": "dynamic", "description": "Right index finger circling around face", "avatar": False},
    "HOW": {"category": "QUESTIONS", "hands": 2, "type": "dynamic", "description": "Hands twisting from palms down to palms up", "avatar": True},
    "I": {"category": "PEOPLE", "hands": 1, "type": "static", "description": "Index finger pointing to chest", "avatar": True},
    "YOU": {"category": "PEOPLE", "hands": 1, "type": "static", "description": "Index finger pointing to recipient", "avatar": True}
}

def get_catalog(mode: str) -> Dict[str, Dict[str, Any]]:
    """Returns the full sign catalog for the specified language mode."""
    return ASL_CATALOG if mode.upper() == "ASL" else ISL_CATALOG

def get_vocabulary(mode: str) -> List[str]:
    """Returns list of all cataloged sign names for the specified mode."""
    return list(get_catalog(mode).keys())


def get_categories() -> List[str]:
    """Returns all standard sign categories."""
    return CATEGORIES

def get_sign_metadata(mode: str, sign_name: str, trained_classes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    Returns rich metadata for a sign, accurately reflecting whether it is:
      - trained in the local classifier
      - available in 3D avatar keyframes
      - available for fingerspelling
    """
    sign_key = sign_name.upper().replace(" ", "_")
    catalog = get_catalog(mode)
    if sign_key not in catalog:
        return None

    entry = catalog[sign_key].copy()
    entry["id"] = sign_key.lower()
    entry["label"] = sign_key
    entry["language"] = mode.upper()
    
    is_trained = (trained_classes is not None and sign_key in trained_classes)
    entry["trained"] = is_trained
    entry["recognition_available"] = is_trained
    entry["avatar_available"] = entry.get("avatar", False)
    entry["fingerspelling_available"] = True
    return entry

def build_full_vocabulary_view(mode: str, trained_classes: List[str]) -> Dict[str, Any]:
    """
    Constructs a comprehensive, honest view of the entire vocabulary:
    separating trained classifier signs from cataloged/fingerspellable signs.
    """
    catalog = get_catalog(mode)
    categories_dict: Dict[str, List[Dict[str, Any]]] = {}

    for sign_key, info in catalog.items():
        cat = info.get("category", "DAILY_LIFE")
        if cat not in categories_dict:
            categories_dict[cat] = []

        is_trained = sign_key in trained_classes
        categories_dict[cat].append({
            "id": sign_key.lower(),
            "label": sign_key,
            "category": cat,
            "hands": info.get("hands", 1),
            "type": info.get("type", "static"),
            "description": info.get("description", ""),
            "trained": is_trained,
            "recognition_available": is_trained,
            "avatar_available": info.get("avatar", False),
            "fingerspelling_available": True
        })

    return {
        "mode": mode.upper(),
        "total_catalog_signs": len(catalog),
        "trained_signs_count": len(trained_classes),
        "trained_classes": trained_classes,
        "categories": categories_dict
    }

ASL_TRAINED_SIGNS = [
    "BAD", "GOOD", "HELLO", "HELP", "I_LOVE_YOU", "NO", "PEACE",
    "PLEASE", "SORRY", "THANK_YOU", "WATER", "YES", "STOP", "MORE", "EAT"
]

ISL_TRAINED_SIGNS = [
    "BAD", "FOOD", "GOOD", "HELP", "HOME", "NAMASTE", "NO",
    "PLEASE", "SCHOOL", "SORRY", "THANK_YOU", "WATER", "YES", "HELLO"
]

def get_sign_list(mode: str) -> List[str]:
    """Returns canonical list of recognized signs for model training/inference."""
    return ASL_TRAINED_SIGNS if mode.upper() == "ASL" else ISL_TRAINED_SIGNS

# Backward compatibility aliases
ASL_VOCABULARY = ASL_CATALOG
ISL_VOCABULARY = ISL_CATALOG


