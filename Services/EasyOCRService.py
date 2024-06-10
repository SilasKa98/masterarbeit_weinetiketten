import cv2
import easyocr


class EasyOCRService:

    @staticmethod
    def read_in_files(read_in_image, language):
        print(language)
        image = cv2.imread(read_in_image)
        # create Reader object for specific language. Catch and use english if language code is not recognized
        try:
            ocr_reader = easyocr.Reader([language])
        except ValueError:
            ocr_reader = easyocr.Reader(["en"])

        image_text = ocr_reader.readtext(image, detail=0)

        return ' '.join(image_text)
