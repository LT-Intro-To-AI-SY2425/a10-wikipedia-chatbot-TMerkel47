import re, string
from wikipedia import WikipediaPage
import wikipedia
from bs4 import BeautifulSoup
from match import match
from typing import List, Callable, Tuple, Any, Match

# ------------- Fetch and parse Lamborghini data from Wikipedia ------------------

def get_page_html(title: str) -> str:
    results = wikipedia.search(title)
    if not results:
        raise LookupError(f"No Wikipedia page found for {title}")
    return WikipediaPage(results[0]).html()

def get_first_infobox_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    results = soup.find_all(class_="infobox")
    if not results:
        raise LookupError("Page has no infobox")
    return results[0].text

def clean_text(text: str) -> str:
    only_ascii = "".join([char if char in string.printable else " " for char in text])
    no_dup_spaces = re.sub(" +", " ", only_ascii)
    no_dup_newlines = re.sub("\n+", "\n", no_dup_spaces)
    return no_dup_newlines.strip()

def get_match(text: str, pattern: str, error_text: str = "Property not found") -> Match:
    p = re.compile(pattern, re.DOTALL | re.IGNORECASE)
    match_obj = p.search(text)
    if not match_obj:
        raise AttributeError(error_text)
    return match_obj

# Fetch and parse Lamborghini automobiles list page once, store info here
print("Fetching Lamborghini model data from Wikipedia, please wait...")
html = get_page_html("List of Lamborghini automobiles")
soup = BeautifulSoup(html, "html.parser")

# The data is in tables — we'll parse the "Former production vehicles" table and others
# We'll extract Model, Production Duration, Engine, Top Speed for each model listed

def parse_lambo_tables(soup):
    model_data = {}
    # The tables of interest have class "wikitable"
    tables = soup.find_all("table", {"class": "wikitable"})
    # We'll parse each table row (skip header)
    for table in tables:
        rows = table.find_all("tr")
        headers = [th.get_text(strip=True).lower() for th in rows[0].find_all("th")]
        # We want columns like model, duration of production, engine, top speed
        # Find indexes for those columns (some tables have slightly different headers)
        try:
            model_idx = headers.index("model")
            duration_idx = headers.index("duration of production")
            engine_idx = headers.index("engine")
            top_speed_idx = headers.index("top speed")
        except ValueError:
            continue  # skip tables that don't have these headers
        
        for row in rows[1:]:
            cols = row.find_all(["td","th"])
            if len(cols) < max(model_idx, duration_idx, engine_idx, top_speed_idx) + 1:
                continue
            # Extract text for each column
            model_raw = cols[model_idx].get_text(separator=" ", strip=True)
            duration = cols[duration_idx].get_text(separator=" ", strip=True)
            engine = cols[engine_idx].get_text(separator=" ", strip=True)
            top_speed = cols[top_speed_idx].get_text(separator=" ", strip=True)

            # Models can be comma separated or have multiple variants in the cell
            models = [m.strip() for m in re.split(r",|/", model_raw)]
            for m in models:
                key = m.lower()
                model_data[key] = {
                    "model": m,
                    "duration": duration,
                    "engine": engine,
                    "top_speed": top_speed
                }
    return model_data

model_info = parse_lambo_tables(soup)

if not model_info:
    print("Warning: No Lamborghini model data found!")

# Print some models to help user get started
sample_models = list(model_info.keys())[:3]
print("Data loaded successfully.")
print("Some Lamborghini models you can ask about:", ", ".join([model_info[m]["model"] for m in sample_models]))

# ----------------- Helper functions to retrieve info --------------------

def get_duration(model_name: str) -> str:
    key = model_name.lower()
    if key in model_info:
        return model_info[key]["duration"]
    else:
        raise AttributeError(f"No production duration info for model '{model_name}'")

def get_engine(model_name: str) -> str:
    key = model_name.lower()
    if key in model_info:
        return model_info[key]["engine"]
    else:
        raise AttributeError(f"No engine info for model '{model_name}'")

def get_top_speed(model_name: str) -> str:
    key = model_name.lower()
    if key in model_info:
        return model_info[key]["top_speed"]
    else:
        raise AttributeError(f"No top speed info for model '{model_name}'")

# ----------------- Action functions --------------------

def duration_action(matches: List[str]) -> List[str]:
    model = " ".join(matches)
    try:
        duration = get_duration(model)
        return [f"The production duration of {model.title()} is: {duration}"]
    except AttributeError as e:
        return [str(e)]

def engine_action(matches: List[str]) -> List[str]:
    model = " ".join(matches)
    try:
        engine = get_engine(model)
        return [f"The engine type of {model.title()} is: {engine}"]
    except AttributeError as e:
        return [str(e)]

def top_speed_action(matches: List[str]) -> List[str]:
    model = " ".join(matches)
    try:
        top_speed = get_top_speed(model)
        return [f"The top speed of {model.title()} is: {top_speed}"]
    except AttributeError as e:
        return [str(e)]

def model_help_action(matches: List[str]) -> List[str]:
    model = " ".join(matches)
    # Just give user a nudge on what they can ask about this model
    key = model.lower()
    if key in model_info:
        return [f"Ask me about the production duration, engine type, or top speed of {model.title()}."]
    else:
        return [f"No information found for model '{model.title()}'. Try another Lamborghini model."]

def bye_action(dummy: List[str]) -> None:
    raise KeyboardInterrupt

# ---------------- Patterns and Actions ----------------

Pattern = List[str]
Action = Callable[[List[str]], List[Any]]

pa_list: List[Tuple[Pattern, Action]] = [
    # Production duration questions
    ("what is the production duration of %".split(), duration_action),
    ("how long was % produced".split(), duration_action),
    ("when was % produced".split(), duration_action),
    ("production duration of %".split(), duration_action),

    # Engine type questions
    ("what is the engine type of %".split(), engine_action),
    ("tell me the engine of %".split(), engine_action),
    ("engine type of %".split(), engine_action),
    ("engine of %".split(), engine_action),

    # Top speed questions
    ("what is the top speed of %".split(), top_speed_action),
    ("tell me the top speed of %".split(), top_speed_action),
    ("top speed of %".split(), top_speed_action),

    # Simple queries with just the model name or model+keyword
    (["%"], model_help_action),
    (["%", "production"], duration_action),
    (["%", "engine"], engine_action),
    (["%", "top", "speed"], top_speed_action),

    # Bye
    (["bye"], bye_action),
]

# ------------------ Main matching and input loop ------------------------

def search_pa_list(src: List[str]) -> List[str]:
    for pat, act in pa_list:
        mat = match(pat, src)
        if mat is not None:
            return act(mat)
    return ["I don't understand. Try asking about production duration, engine type, or top speed of a Lamborghini model."]

def query_loop() -> None:
    print("\nWelcome to the Lamborghini info chatbot!\n")
    print("Ask about production duration, engine type, or top speed of a Lamborghini model.")
    print("Type 'bye' to exit.\n")
    while True:
        try:
            query = input("Your query? ").replace("?", "").lower().split()
            if not query:
                print("Please enter a question or model name.")
                continue
            answers = search_pa_list(query)
            for ans in answers:
                print(ans)
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    query_loop()