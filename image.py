"""
March 4, 2024

This code is in beta, it's not recommended for us right now
"""

# https://platform.openai.com/docs/api-reference/images

import requests
from openai import OpenAI

client = OpenAI()

prompt = input("PROMPT: ")

response = client.images.generate(
  model="dall-e-3",
  # prompt="a white siamese cat",
  prompt=prompt,
  size="1024x1024",
  quality="standard",
  # quality="hd",
  n=1,
)

image_url = response.data[0].url

# Save the image locally
image_data = requests.get(image_url).content
with open('siamese_cat.jpg', 'wb') as handler:
    handler.write(image_data)

