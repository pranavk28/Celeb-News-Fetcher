import requests
import json
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
from openai import OpenAI
import streamlit as st

def query_serper(query, api_key):
    url = "https://google.serper.dev/news"
    payload = json.dumps({
    "q": query
    })
    headers = {
    'X-API-KEY': serper_api_key,
    'Content-Type': 'application/json'
    }

    response = json.loads(requests.request("POST", url, headers=headers, data=payload).text)
    return response


def crawl_text(url):
    """
    Crawls a webpage and extracts text content in the order it appears.
    """
    try:
        # Send GET request to the URL
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Create BeautifulSoup object
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script, style, and hidden elements
        for element in soup(['script', 'style', 'meta', '[display:none]']):
            element.decompose()
            
        # Find all paragraphs and headers in order
        content_text = ''
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = element.get_text(strip=True)
            if text:  # Only add non-empty elements
                content_text += '\n' + text
        
        return True, content_text
        
    except requests.exceptions.HTTPError as http_err:
        error_msg = f"HTTP error occurred: {http_err}"
        return False, error_msg
        
    except requests.exceptions.ConnectionError:
        error_msg = "Failed to connect to the server"
        return False, error_msg
        
    except requests.exceptions.Timeout:
        error_msg = "Request timed out"
        return False, error_msg
        
    except requests.exceptions.RequestException as e:
        error_msg = f"An error occurred while fetching the page: {str(e)}"
        return False, error_msg
        
    except Exception as e:
        error_msg = f"An error occurred while parsing the page: {str(e)}"
        return False, error_msg
    
def combine_texts(crawl_links):
    count = 0
    full_text = ''
    for link in crawl_links:
        success,text = crawl_text(link)
        if success and text != '':
            count += 1
            full_text += f'Text {count}\n' + text + '\n'
        if count == 5:
            break
    return full_text
    

# Load environment variables from a .env file
load_dotenv()
serper_api_key = os.getenv('SERPER_API_KEY')
openai_api_key = os.getenv('OPENAI_API_KEY')

# Add a text input for the celebrity name
celebrity_name = st.text_input("Enter celebrity name:", "")
if st.button("Search") and celebrity_name:
    # Show a loading spinner while getting the information
    with st.spinner(f"Searching for information about {celebrity_name}..."):
        response = query_serper(celebrity_name,serper_api_key)
        crawl_links = [link['link'] for link in response['news']]
        context = combine_texts(crawl_links)

        client = OpenAI(api_key=openai_api_key)
        completion = client.chat.completions.create(
            model= 'gpt-4o-mini',
            messages=[
                {"role": "system", "content": "You are  assistant summarizing information on a personality from given scraped text for top news about celebrity as context. Summarize to 3 paragraph articles."},
                {"role": "user", "content":  f"""Answer the following question based on this context primarily:

                        {context}

                        Question: Summarize the latest news about {celebrity_name} 
                        """
                    }
            ]
        )
        bot_reply = completion.choices[0].message.content
        st.markdown(bot_reply)
else:
    # Show a placeholder message
    st.write("Enter a celebrity's name and click 'Search' to get information!")



