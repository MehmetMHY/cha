"""
April 8, 2025

INSTALL:

pip install youtube-comment-downloader
"""

from itertools import islice
from youtube_comment_downloader import *
import time
import json

downloader = YoutubeCommentDownloader()

url = input("URL: ")
count = int(input("SIZE: "))

comments = downloader.get_comments_from_url(
    url,
    sort_by=SORT_BY_POPULAR
)

start_time = time.time()

output = []
for comment in islice(comments, count):
    output.append(comment)

runtime = time.time() - start_time

print("OUTPUT:")
print(json.dumps(output, indent=4))
print()
print(f"RUNTIME: {runtime} seconds")
print(f"PER: {runtime / len(output)} seconds")

