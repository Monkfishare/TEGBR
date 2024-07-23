import aiohttp
import asyncio
import io
import os
import requests

# Function to extract and format texts by language and heading tag
def extract_and_format_texts(data, language, heading_tag):
    texts = [f"<{heading_tag}>{item['text']}</{heading_tag}>" for item in data if
             "lang" in item and item["lang"] == language and "text" in item]
    return texts

# Function to extract texts by language and preserve order with HTML tags
def extract_texts_in_order(data, language):
    texts = []
    for item in data:
        if "lang" in item and item["lang"] == language and "text" in item:
            content_type = item.get("type")
            if content_type == "subtitle":
                texts.append(f"<h4>{item['text']}</h4>")
            else:
                texts.append(f"<p>{item['text']}</p>")
    return texts

# Function to fetch subtitles from the API using the article ID and language code
def fetch_subtitles(article_id, language_code):
    subtitles_url = f"https://api.hummingbird.businessreview.global/api/article/index?id={article_id}"
    response = requests.get(subtitles_url)
    data = response.json()

    subtitles = []
    for content in data["body"]["content"]:
        if content["type"] == "subtitle":
            for subtitle_data in content["data"]:
                if subtitle_data["lang"] == language_code:
                    subtitles.append(subtitle_data["text"])

    return subtitles

# Function to replace <p> tags with <h4> tags for subtitles in HTML content
def replace_with_h4(html_content, subtitles):
    for subtitle in subtitles:
        html_content = html_content.replace(f"<p>{subtitle}</p>", f"<h4>{subtitle}</h4>")
    return html_content

# Function to perform the specified modifications
def modify_html_content(html_content):
    # Remove all "■"
    html_content = html_content.replace("■", "")

    # Add <span>■</span></p> to the end of the entire content
    html_content += "<span>■</span></p>"

    # Replace </p><span> with <span>
    html_content = html_content.replace("</p><span>", "<span>")

    # Replace </h4>\n<span>■</span></p> with </h4>
    html_content = html_content.replace("</h3>\n<span>■</span></p>", "</h3>")

    return html_content

async def fetch_article(session, sem, article_url, article_id, language_code):
    try:
        async with sem, session.get(article_url) as response:
            if response.status == 200:
                json_data = await response.json()

                fly_title_texts = extract_and_format_texts(json_data["body"]["fly_title"], language_code, "h2")
                title_texts = extract_and_format_texts(json_data["body"]["title"], language_code, "h1")
                rubric_texts = extract_and_format_texts(json_data["body"]["rubric"], language_code, "h3")

                all_texts = []
                for content_item in json_data["body"]["content"]:
                    if "data" in content_item:
                        all_texts.extend(extract_texts_in_order(content_item["data"], language_code))

                transition_html_content = io.StringIO()
                # Add the link to the first line
                transition_html_content.write(f'<a href="https://www.businessreview.global/latest/{article_id}">❀</a>\n')
                transition_html_content.write("\n".join(fly_title_texts + title_texts + rubric_texts) + "\n")
                transition_html_content.write("\n".join(all_texts))

                print(f"Transition content for article {article_id} created successfully")

                zh_cn_subtitles = fetch_subtitles(article_id, language_code)

                modified_html_content = modify_html_content(transition_html_content.getvalue())
                modified_html_content = replace_with_h4(modified_html_content, zh_cn_subtitles)

                return f"{modified_html_content}\n\n<div style='page-break-after: always;'></div>\n"

            else:
                print(f"Error: Unable to fetch data for article {article_id}. Status code: {response.status}")
                return None

        # await asyncio.sleep(1)  # Adjust the delay time as needed

    except Exception as e:
        print(f"Error: {e}")
        return None

async def main():
    year = "2024"  # Default to Fetch the latest 120 articles
    # Specify the target year as needed to fetch articles (from 2015 to the year prior to the current year), e.g., year = "2023"
    
    # Automatically set use_api_data to False if year is an empty string
    use_api_data = not bool(year)

    if use_api_data:
        # Fetch article IDs from the API (latest 120 articles)
        api_url = "https://api.hummingbird.businessreview.global/api/toc/get_articles"
        response = requests.get(api_url)

        if response.status_code == 200:
            json_data = response.json()
            articles_data = json_data.get("articles", {}).get("new", [])
            article_ids = [article.get("article_id", "") for article in articles_data]
        else:
            print(f"Error: Unable to fetch article IDs from API. Status code: {response.status_code}")
            return
    else:
        # Read article IDs from the text file
        file_path = f"assets/article_id/{year}.txt"
        if not os.path.exists(file_path):
            print(f"Error: Article IDs text file '{file_path}' not found.")
            return

        with open(file_path, "r") as file:
            article_ids = [line.strip() for line in file.readlines() if line.strip()]

    # Define the order of languages. Adjust the order and number based on your preferences.
    # Each language is represented by a language code: "en_GB" for English, "zh_CN" for Simplified Chinese, "zh_TW" for Traditional Chinese.
    # languages = ["zh_CN", "en_GB"]
    # languages = ["zh_CN"]
    # languages = ["en_GB"]
    languages = ["en_GB", "zh_CN"]  #Ajust the order and number of language as needed

    # Add a blank page at the beginning
    concatenated_html_content = '<h2>TEGBR</h2>\n<div style="page-break-before: always;"></div>\n'

    # Limit the number of concurrent requests using a semaphore
    sem = asyncio.Semaphore(20)  # Adjust the number as needed

    async with aiohttp.ClientSession() as session:
        for article_id in article_ids:
            tasks = [fetch_article(session, sem, f"https://api.hummingbird.businessreview.global/api/article/index?id={article_id}", article_id, lang) for lang in languages]

            results = await asyncio.gather(*tasks)

            concatenated_html_content += ''.join(results)

    concatenated_output_file_path = "TEGBR.html"
    with open(concatenated_output_file_path, "w", encoding="utf-8") as concatenated_output_file:
        concatenated_output_file.write(concatenated_html_content)

    print(f"{concatenated_output_file_path} created successfully with concatenated HTML content.")

if __name__ == "__main__":
    asyncio.run(main())
