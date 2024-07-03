import json

from Services.DoctrService import DoctrService
from Services.SearchImagesService import SearchImagesService

#doctr = DoctrService()
#data = doctr.read_in_files_with_kie("C:\\Masterarbeit_ocr_env\\wine_images\\uploads\\i00234a01.jpg")


search = SearchImagesService()
test = search.search_normal("Zeige mir weine aus italien")

print(test)
print(list(test.keys()))
