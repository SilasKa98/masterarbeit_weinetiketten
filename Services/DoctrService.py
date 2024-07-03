from doctr.io import DocumentFile
from doctr.models import ocr_predictor


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
