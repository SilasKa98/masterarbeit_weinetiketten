import json

from Services.DoctrService import DoctrService


doctr = DoctrService()
data = doctr.read_in_files_with_kie("C:\\Masterarbeit_ocr_env\\wine_images\\uploads\\i00234a01.jpg")
