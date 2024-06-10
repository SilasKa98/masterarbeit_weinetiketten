import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
import cv2
import matplotlib.pyplot as plt
from PIL import Image
from Services.EasyOCRService import EasyOCRService

easyOcr = EasyOCRService()

test = easyOcr.read_in_files("./test.jpg", "unknown")
print(test)
#string = pytesseract.image_to_string(image)
#print(string)