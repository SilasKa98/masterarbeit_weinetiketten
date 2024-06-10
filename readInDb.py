from Services.DatabaseService import DatabaseService
from ActionProcessor import ActionProcessor

action_processor = ActionProcessor()
image_reads = action_processor.process_directory("wine_images", False, "tesseract")


for image_info in image_reads:
    database_service = DatabaseService()
    select_result = database_service.select_from_table("etiketten_infos", "*", "name=%s", [image_info[2]])
    if not select_result:
        database_service.insert_into_table(
            "etiketten_infos",
            ["text_tesseract", "path", "name", "detected_language", "image_directory"],
            [image_info[0], image_info[1], image_info[2], image_info[3], image_info[4]]
        )
    else:
        database_service.update_table(
            "etiketten_infos", ["text_tesseract", "path","detected_language", "image_directory"],
            [image_info[0], image_info[1], image_info[3], image_info[4]],
            "name",
            image_info[2]
        )



