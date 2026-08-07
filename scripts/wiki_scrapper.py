import requests
from bs4 import BeautifulSoup
import json
import re
import time
from urllib.parse import urljoin

BASE_URL = "https://en.wikipedia.org"
LIST_URL = f"{BASE_URL}/wiki/List_of_Telugu_films_of_2025"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_text(text):
    """Removes Wikipedia citations like [1], [2], [a] and extra spaces."""
    if not text:
        return ""
    text = re.sub(r'\[.*?\]', '', text)
    return " ".join(text.split())

def parse_infobox_list(td_element):
    """Extracts text items from a table cell, handling lists, line breaks, commas, and multi-name separators."""
    if not td_element:
        return []
    
    # Check for bulleted lists
    items = td_element.find_all('li')
    if items:
        return [clean_text(item.get_text()) for item in items]
    
    # Handle line breaks or div stacks
    text = td_element.get_text("\n")
    raw_lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    processed_items = []
    for line in raw_lines:
        # Split on commas, 'and', slashes, or dashes that separate distinct names
        sub_items = re.split(r',| and |/|–|—', line)
        for item in sub_items:
            cleaned = clean_text(item)
            if cleaned:
                processed_items.append(cleaned)
                
    return processed_items

def scrape_wikipedia_movie_to_exact_json(url, fallback_title=""):
    """Scrapes an individual movie page and maps it to your exact JSON schema with fallbacks."""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        heading = soup.find('h1', id='firstHeading')
        title_text = clean_text(heading.get_text()) if heading else fallback_title

        movie_data = {
            "title": title_text,
            "year": 2025,
            "language": "Telugu",
            "genre": [],
            "director": [],           # Converted to array to support multi-hop graph relations
            "story_by": [],           # Converted to array to support multi-hop graph relations
            "screenplay": [],         # Converted to array to support multi-hop graph relations
            "dialogues": [],          # Converted to array to support multi-hop graph relations
            "producers": [],
            "production_company": [], # Converted to array to support multi-hop graph relations
            "cast": [],
            "crew": {
                "music_director": [], # Converted to array to support multi-hop graph relations
                "cinematographer": [],# Converted to array to support multi-hop graph relations
                "editors": []
            },
            "release_details": {
                "date": "",
                "running_time_minutes": 0,
                "formats": ["Standard"]
            },
            "financials": {
                "budget": "",
                "box_office": ""
            },
            "plot_summary": ""
        }
        
        # 1. Parse Introduction for Genres and Year
        first_p = soup.find('p', class_=lambda x: x != 'mw-empty-elt')
        if first_p:
            p_text = first_p.get_text().lower()
            genre_matches = re.findall(r'\b(action|thriller|comedy|romance|drama|horror|sci-fi|political|masala|mythological|epic|fantasy)\b', p_text)
            if genre_matches:
                movie_data["genre"] = list(set([g.capitalize() for g in genre_matches]))
                
            year_match = re.search(r'\b(202\d)\b', p_text)
            if year_match:
                movie_data["year"] = int(year_match.group(1))

        # 2. Parse the Right-Hand Infobox Sidebar
        infobox = soup.find("table", {"class": "infobox"})
        written_by_fallback = []
        
        if infobox:
            for row in infobox.find_all("tr"):
                th = row.find("th")
                td = row.find("td")
                if th and td:
                    label = clean_text(th.get_text()).lower()
                    
                    if "directed" in label:
                        movie_data["director"] = parse_infobox_list(td)
                    elif "story" in label:
                        movie_data["story_by"] = parse_infobox_list(td)
                    elif "screenplay" in label:
                        movie_data["screenplay"] = parse_infobox_list(td)
                    elif "dialogue" in label:
                        movie_data["dialogues"] = parse_infobox_list(td)
                    elif "written" in label:
                        written_by_fallback = parse_infobox_list(td)
                    elif "produced" in label:
                        movie_data["producers"] = parse_infobox_list(td)
                    elif "production" in label or "company" in label:
                        movie_data["production_company"] = parse_infobox_list(td)
                    elif "music" in label:
                        movie_data["crew"]["music_director"] = parse_infobox_list(td)
                    elif "cinematography" in label:
                        movie_data["crew"]["cinematographer"] = parse_infobox_list(td)
                    elif "edit" in label:
                        movie_data["crew"]["editors"] = parse_infobox_list(td)
                    elif "release" in label:
                        date_match = re.search(r'\d{4}-\d{2}-\d{2}', td.get_text())
                        movie_data["release_details"]["date"] = date_match.group(0) if date_match else clean_text(td.get_text())
                    elif "running time" in label:
                        time_match = re.search(r'(\d+)\s*minutes', td.get_text())
                        if time_match:
                            movie_data["release_details"]["running_time_minutes"] = int(time_match.group(1))
                    elif "budget" in label:
                        movie_data["financials"]["budget"] = clean_text(td.get_text())
                    elif "box office" in label:
                        movie_data["financials"]["box_office"] = clean_text(td.get_text())

            # Map "Written by" fallback values if individual writing sections are absent
            if written_by_fallback:
                if not movie_data["story_by"]:
                    movie_data["story_by"] = written_by_fallback
                if not movie_data["screenplay"]:
                    movie_data["screenplay"] = written_by_fallback

        # 3. Robust Cast Section Parsing for Graph Compatibility
        cast_header = soup.find('h2', string=re.compile(r'Cast', re.IGNORECASE))
        if not cast_header:
            cast_span = soup.find('span', id=re.compile(r'Cast', re.IGNORECASE))
            if cast_span:
                cast_header = cast_span.find_parent('h2')
                
        if cast_header:
            next_node = cast_header.find_next_sibling()
            while next_node and next_node.name != 'h2':
                # Parse Standard Ordered/Unordered Lists
                if next_node.name in ['ul', 'ol']:
                    for li in next_node.find_all('li'):
                        li_text = clean_text(li.get_text())
                        if not li_text:
                            continue
                        
                        actor, role = "", ""
                        # Multi-delimiter structural check strategy
                        for delimiter in [" as ", " — ", " – ", " - ", " : ", ":"]:
                            if delimiter in li_text:
                                parts = li_text.split(delimiter, 1)
                                actor = parts[0].strip()
                                role = parts[1].strip()
                                break
                        
                        # Hyperlinked actor extraction fallback strategy
                        if not actor:
                            anchor = li.find('a')
                            if anchor:
                                actor = clean_text(anchor.get_text())
                                role = li_text.replace(actor, "").strip(" :,–—-")
                            else:
                                actor = li_text
                                role = ""
                        
                        if actor:
                            movie_data["cast"].append({
                                "actor": clean_text(actor), 
                                "role": clean_text(role) if role else "Unknown Role"
                            })
                            
                # Parse Cast Sections using Tables instead of Bulleted Lists
                elif next_node.name == 'table':
                    for tr in next_node.find_all('tr'):
                        tds = tr.find_all(['td', 'th'])
                        if len(tds) >= 2:
                            actor_cand = clean_text(tds[0].get_text())
                            role_cand = clean_text(tds[1].get_text())
                            if actor_cand and actor_cand.lower() not in ["actor", "cast", "character"]:
                                movie_data["cast"].append({
                                    "actor": actor_cand, 
                                    "role": role_cand if role_cand else "Unknown Role"
                                })
                next_node = next_node.find_next_sibling()

        # 4. Parse Plot Section for Summary Paragraphs
        plot_header = soup.find('h2', string=re.compile(r'Plot|Synopsis', re.IGNORECASE))
        if not plot_header:
            plot_span = soup.find('span', id=re.compile(r'Plot|Synopsis', re.IGNORECASE))
            if plot_span:
                plot_header = plot_span.find_parent('h2')
                
        if plot_header:
            plot_paragraphs = []
            next_node = plot_header.find_next_sibling()
            while next_node and next_node.name != 'h2':
                if next_node.name == 'p':
                    p_text = clean_text(next_node.get_text())
                    if p_text:
                        plot_paragraphs.append(p_text)
                next_node = next_node.find_next_sibling()
            movie_data["plot_summary"] = " ".join(plot_paragraphs)

        return movie_data
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def scrape_all_2025_movies():
    print("📡 Requesting master movie list page...")
    response = requests.get(LIST_URL, headers=headers)
    if response.status_code != 200:
        print("Failed to load list page.")
        return
        
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all("table", {"class": "wikitable"})
    
    all_movies_data = []
    seen_urls = set()
    
    for table in tables:
        if 'director' not in table.get_text().lower():
            continue
            
        rows = table.find_all("tr")[1:]
        for row in rows:
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
                
            for cell in cells:
                italic_tag = cell.find('i')
                if italic_tag:
                    raw_title = clean_text(italic_tag.get_text())
                    anchor = italic_tag.find('a', href=True)
                    
                    if anchor and "/wiki/" in anchor['href'] and "redlink=1" not in anchor['href']:
                        movie_url = urljoin(BASE_URL, anchor['href'])
                        
                        if movie_url not in seen_urls:
                            seen_urls.add(movie_url)
                            print(f"🎬 Scraping: {raw_title}")
                            
                            movie_json = scrape_wikipedia_movie_to_exact_json(movie_url, raw_title)
                            if movie_json:
                                all_movies_data.append(movie_json)
                            
                            time.sleep(1.0)
                    break

    output_filepath = "unpatched_dataset.json"
    try:
        with open(output_filepath, "w", encoding="utf-8") as f:
            json.dump(all_movies_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Data write operational. Complete dataset saved to '{output_filepath}'.")
    except Exception as file_err:
        print(f"⚠️ Could not write file: {file_err}")

    print("\n📦 Processing complete! Final Consolidated Output:")
    print(json.dumps(all_movies_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    scrape_all_2025_movies()