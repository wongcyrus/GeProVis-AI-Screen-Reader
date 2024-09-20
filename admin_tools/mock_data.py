import os
import requests
import json

urls = [
    "https://www.omlet.co.uk/images/cache/1024/682/Dog-Japanese_Shiba_Inu-Two_healthy_adult_Japanese_Shiba_Inus_standing_tall_together.jpg",
    # "https://mf.b37mrtl.ru/rbthmedia/images/2023.01/original/63c5431125df170e337b9f4f.jpg",
    # "https://mf.b37mrtl.ru/rbthmedia/images/2023.01/original/63c5431225df170e337b9f51.jpg",
    # "https://images.prismic.io/trustedhousesitters/6e0b2c72-627c-4b71-b426-cbaf4c0e2b62_Shiba+Inu+Names+Image+1.jpg?auto=compress,format&rect=0,0,4912,2456&w=960&h=480"
    # "https://mf.b37mrtl.ru/rbthmedia/images/2023.01/original/63c5431025df170e337b9f4e.jpg",
]


for url in urls:
    # urlencode url
    url = (
        url.replace(":", "%3A")
        .replace("/", "%2F")
        .replace("?", "%3F")
        .replace("=", "%3D")
        .replace("&", "%26")
    )
    api_url = f"https://gateway-5o6p2is6.ue.gateway.dev/gemini?url={url}"
    payload = json.dumps({"lang": "zh-CN"})
    headers = {"Content-Type": "application/json", "X-API-Key": "AIzaSyC5gQvyYk0VyrG38ZF6GSZ3oufl1sptEZE"}
    response = requests.request("POST", api_url, headers=headers, data=payload)

    print(response.text)
