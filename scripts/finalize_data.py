import json

FILE_PATH = "movies_dataset.json"

def inject_graph_placeholders():
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            movies = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Could not find '{FILE_PATH}'.")
        return

    fixed_plots = 0
    fixed_casts = 0

    for movie in movies:
        # Standardize empty plot strings
        if not movie.get("plot_summary") or movie["plot_summary"].strip() == "":
            movie["plot_summary"] = "Plot summary currently unavailable for this release."
            fixed_plots += 1
            
        # Standardize empty cast arrays
        if not movie.get("cast") or len(movie["cast"]) == 0:
            movie["cast"] = [
                {
                    "actor": "Information Pending",
                    "role": "Main Cast"
                }
            ]
            fixed_casts += 1

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)

    print("✅ Post-processing complete. Graph-safe placeholders injected successfully.")
    print(f"   -> Standardized plots: {fixed_plots}")
    print(f"   -> Standardized casts: {fixed_casts}")

if __name__ == "__main__":
    inject_graph_placeholders()