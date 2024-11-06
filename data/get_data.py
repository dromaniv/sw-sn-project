import wikipedia
import os

def fetch_and_save_page(page_title):
    """
    Fetches the content of a Wikipedia page and saves it to a text file.

    Parameters:
    - page_title (str): The title of the Wikipedia page to fetch.

    Returns:
    - None
    """
    try:
        # Fetch the Wikipedia page
        page = wikipedia.page(page_title)
        
        # Get the content of the page
        content = page.content
        
        # Create a safe filename by replacing spaces with underscores and removing problematic characters
        safe_title = "".join(char if char.isalnum() or char in (" ", "_") else "_" for char in page_title)
        safe_title = safe_title.replace(" ", "_")
        output_file = f"{safe_title}.txt"
        
        # Save the content to the text file with UTF-8 encoding
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(content)
        
        print(f"✅ Content of '{page_title}' has been saved to '{output_file}'.")
    
    except wikipedia.exceptions.DisambiguationError as e:
        print(f"⚠️ DisambiguationError: The title '{page_title}' is ambiguous. Suggestions:")
        for option in e.options:
            print(f" - {option}")
    
    except wikipedia.exceptions.PageError:
        print(f"❌ PageError: The page titled '{page_title}' does not exist on Wikipedia.")
    
    except Exception as e:
        print(f"⚠️ An unexpected error occurred while processing '{page_title}': {e}")


def main():
    # Set the language to English (default is English, but setting it explicitly for clarity)
    wikipedia.set_lang("en") # pl ru  en de  fr zh  simple
    
    # List of Wikipedia page titles to fetch
    titles = ["Andrzej Duda", "Joe Biden", "Donald Trump"]  #TODO: Add more titles? NO CLUE WHY JOE BIDEN not working :(
                                                            # Duda just for testing, Biden works for pl wiki
    
    # Create an output directory to store the text files
    output_dir = "sw-sn-project\data"
    os.makedirs(output_dir, exist_ok=True)
    
    # Change the current working directory to the output directory
    os.chdir(output_dir)
    
    # Iterate over each title and fetch/save the content
    for title in titles:
        fetch_and_save_page(title)
        # add == General information == at the beginning of the file, cus wikipedia does not have it and it is needed for the split_txt_files.py
        title = title.replace(" ", "_")
        try:
            with open(f"{title}.txt", "r", encoding="utf-8") as file:
                content = file.read()
            with open(f"{title}.txt", "w", encoding="utf-8") as file:
                file.write("== General information ==\n\n" + content)
        except:
            print(f"❌ No file found for {title}")

if __name__ == "__main__":
    main()
