"""Get the NASA image of the day and display it in iTerm2"""
import imgcat
import requests
import json


def get_image():
    """Get the NASA image of the day and display it in iTerm2"""
    url = "https://apod.nasa.gov/apod/image/2308/M66_JwstTomlinson_1080.jpg"
    imgcat.imgcat(requests.get(url).content)

if __name__ == "__main__":
    get_image()