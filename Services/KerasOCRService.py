import keras_ocr.pipeline


class KerasOCRService:

    def __init__(self):
        self.pipeline = keras_ocr.pipeline.Pipeline()

    def read_in_files(self, read_in_image):
        images = [keras_ocr.tools.read(url) for url in [read_in_image]]
        prediction_groups = self.pipeline.recognize(images)

        text_list = []
        for item in prediction_groups:
            for inner_item in item:
                text_list.append(inner_item[0])

        text_string = " ".join(text_list)
        return text_string

