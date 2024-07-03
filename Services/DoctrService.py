from doctr.io import DocumentFile
from doctr.models import ocr_predictor, kie_predictor


class DoctrService:

    @staticmethod
    def read_in_files(read_in_image):

        model = ocr_predictor(pretrained=True)
        doc = DocumentFile.from_images(read_in_image)
        result = model(doc)
        result = result.export()

        text_list = []
        # Zugriff auf die "words" in jedem "line" unter "blocks"
        for page in result['pages']:
            for block in page['blocks']:
                for line in block['lines']:
                    for word in line['words']:
                        text_list.append(word['value'])

        text_string = ' '.join(text_list)
        return text_string

    @staticmethod
    def read_in_files_with_kie(read_in_image):
        model = kie_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)
        doc = DocumentFile.from_images(read_in_image)
        result = model(doc)

        all_predictions = []
        predictions = result.pages[0].predictions
        for class_name in predictions.keys():
            list_predictions = predictions[class_name]
            for prediction in list_predictions:
                print(f"Prediction for {class_name}: {prediction}")
                all_predictions.append(prediction)
