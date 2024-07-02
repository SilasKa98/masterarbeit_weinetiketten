import json

from Services.DoctrService import DoctrService


doctr = DoctrService()
data = doctr.read_in_files("C:\Masterarbeit_ocr_env\wine_images\\archiv20a\saarbueg_bergschloesschen.jpg")



print(data)