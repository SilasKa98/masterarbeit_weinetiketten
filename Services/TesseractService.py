import pytesseract
from pytesseract import TesseractError

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
import cv2
import matplotlib.pyplot as plt
from PIL import Image


class TesseractService:

    @staticmethod
    def read_in_files(read_in_image, language):
        image = cv2.imread(read_in_image)
        if language == "unknown":
            image_text = pytesseract.image_to_string(image)
        else:
            try:
                image_text = pytesseract.image_to_string(image, lang=language)
            except TesseractError:
                # use default lang if the given lang is not found(e.g. lang pack not installed)
                image_text = pytesseract.image_to_string(image)
        return image_text
