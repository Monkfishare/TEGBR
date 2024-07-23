import re

# Read bookmark data from the file
with open('bookmarks_raw.txt', 'r', encoding='utf-8') as file:
    bookmark_data = file.read()

# Split the data into individual bookmarks
bookmarks = re.split(r'BookmarkBegin', bookmark_data)
bookmarks = [b.strip() for b in bookmarks if b.strip()]

# Extract BookmarkLevel: 1 information and subtract "1" from each BookmarkPageNumber
level_1_bookmarks = []
level_1_count = 0

for bookmark in bookmarks:
    if "BookmarkLevel: 1" in bookmark:
        if level_1_count < 2:
            # Skip the first two occurrences
            level_1_count += 1
            continue

        title_match = re.search(r'BookmarkTitle: (.+)', bookmark)
        page_number_match = re.search(r'BookmarkPageNumber: (\d+)', bookmark)

        if title_match and page_number_match:
            title = title_match.group(1)
            page_number = int(page_number_match.group(1)) - 1  # Subtract "1" from the page number
            level_1_bookmarks.append({"Title": title, "PageNumber": page_number})

# Write the extracted information to a new text file named "bookmarks.txt"
with open('bookmarks.txt', 'w', encoding='utf-8') as output_file:
    for bookmark_info in level_1_bookmarks:
        output_file.write("BookmarkBegin\n")
        output_file.write("BookmarkLevel: 1\n")
        output_file.write("BookmarkTitle: {}\n".format(bookmark_info["Title"]))
        output_file.write("BookmarkPageNumber: {}\n".format(bookmark_info["PageNumber"]))
