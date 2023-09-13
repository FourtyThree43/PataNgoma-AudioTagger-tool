from pyfiglet import figlet_format
from rgbprint import gradient_print, gradient_scroll, Color
f = figlet_format("text to render", font="slant")
# print(type(f))
gradient_print(f, start_color=0x4BBEE3, end_color=Color.medium_violet_red)
