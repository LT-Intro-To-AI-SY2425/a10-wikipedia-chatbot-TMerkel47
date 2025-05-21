import re
from wikipedia import page
from bs4 import BeautifulSoup
from typing import List  # Add this import for List type hinting

# Fetch and clean the Wikipedia page of Lamborghini automobiles
def get_page_html(url: str) -> str:
    """Fetches the HTML of the given Wikipedia page URL"""
    lamborghini_page = page(url)
    return lamborghini_page.content

# Helper function to extract the table from the HTML
def get_table_html(html: str) -> str:
    """Extracts the HTML of the first table found in the page"""
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table", {"class": "wikitable"})
    return str(tables[0]) if tables else ""

# Function to extract the relevant details (top speed, engine type, production duration) for each model
def extract_car_info(table_html: str) -> dict:
    """Extracts key details from the Lamborghini automobile table"""
    car_info = {}

    # Extract data for each model using regular expressions
    car_info["models"] = extract_models(table_html)
    car_info["details"] = {model: {
        "top_speed": extract_top_speed(table_html, model),
        "engine_type": extract_engine_type(table_html, model),
        "production_duration": extract_production_duration(table_html, model)
    } for model in car_info["models"]}
    
    return car_info

# Regex to extract car models from the table
def extract_models(table_html: str) -> List[str]:
    """Extracts the names of Lamborghini models from the table"""
    pattern = r"\[\[([^|]+)\|([^]]+)\]\]"  # Matches the link to the model (e.g., [[Lamborghini Urus|Urus]])
    matches = re.findall(pattern, table_html)
    return [match[1].strip().lower() for match in matches]  # Return lowercase names for easier matching

# Regex to extract top speed for a specific model
def extract_top_speed(table_html: str, model: str) -> str:
    """Extracts the top speed of the specific car from the table"""
    pattern = rf"(\[\[{re.escape(model)}\|[^\]]+\]\]).*?Top speed\s*[^0-9]*?(?P<speed>\d+)\s*km/h"
    match = re.search(pattern, table_html, re.IGNORECASE)
    return match.group("speed") if match else "Not found"

# Regex to extract engine type for a specific model
def extract_engine_type(table_html: str, model: str) -> str:
    """Extracts the engine type of the specific car from the table"""
    pattern = rf"(\[\[{re.escape(model)}\|[^\]]+\]\]).*?Engine\s*[^A-Za-z]*?(?P<engine_type>[A-Za-z0-9\s\-]+)"
    match = re.search(pattern, table_html, re.IGNORECASE)
    return match.group("engine_type") if match else "Not found"

# Regex to extract production duration for a specific model
def extract_production_duration(table_html: str, model: str) -> str:
    """Extracts the production duration of the specific car from the table"""
    pattern = rf"(\[\[{re.escape(model)}\|[^\]]+\]\]).*?Production\s*[^0-9]*?(?P<years>[\d]{4}-[\d]{4})"
    match = re.search(pattern, table_html, re.IGNORECASE)
    return match.group("years") if match else "Not found"

# Chatbot query response
def chatbot_response(query: str, car_info: dict) -> str:
    """Handles the user's query and responds accordingly"""
    query = query.lower()

    # Check if the user is asking about a specific model
    for model in car_info["models"]:
        if model in query:
            details = car_info["details"].get(model)
            if details:
                if "top speed" in query:
                    return f"The top speed of the Lamborghini {model.title()} is {details['top_speed']} km/h."
                elif "engine" in query or "engine type" in query:
                    return f"The engine type of the Lamborghini {model.title()} is {details['engine_type']}."
                elif "production" in query or "years of production" in query:
                    return f"The Lamborghini {model.title()} was produced from {details['production_duration']}."
                else:
                    return "Sorry, I didn't understand your question. Please ask about top speed, engine type, or production duration."
    return "Sorry, I couldn't find that model. Please try again with a valid Lamborghini model."

if __name__ == "__main__":
    # URL of the Lamborghini automobiles list page
    url = "https://en.wikipedia.org/wiki/List_of_Lamborghini_automobiles"

    # Fetch and clean the page data
    html_content = get_page_html(url)
    table_html = get_table_html(html_content)

    # Extract car information (models and their respective details)
    car_info = extract_car_info(table_html)
    
    # Chatbot interaction
    print("Welcome to the Lamborghini Car Info Chatbot!")
    while True:
        user_query = input("Ask about a Lamborghini car: ").strip()
        if user_query.lower() == "exit":
            print("Goodbye!")
            break
        response = chatbot_response(user_query, car_info)
        print(response)
