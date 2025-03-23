import json
import os
import shutil
from platform import processor
from unittest import case

from PIL import Image

from shared.struct_log import logger
from shared.utils import get_replicate_client
import asyncio

async def train_user_model_pipeline(user_id: int, input_dir: str) -> bool:
    """
    Stub for training logic. Add your actual model training pipeline here.
    Returns True on success, False on failure.
    """

    log = logger.bind(user_id=user_id, event_type="bot.services.model_trainer.train_user_model_pipeline")
    log.info(f">>> Training model for user {user_id} using photos in: {input_dir}")

    replicate_client = get_replicate_client()

    # Converting images and saving into "data" folder
    log.info(f"Starting converting images for user_id: {user_id}")
    output_dir = f"media/{user_id}/data"
    os.makedirs(output_dir, exist_ok=True)

    i = 0
    for filename in os.listdir(input_dir):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            img_path = os.path.join(input_dir, filename)
            img = Image.open(img_path)

            width, height = img.size
            new_size = min(width, height)

            left = (width - new_size) // 2
            top = (height - new_size) // 2
            right = left + new_size
            bottom = top + new_size

            img_cropped = img.crop((left, top, right, bottom))

            img_resized = img_cropped.resize((1024, 1024), Image.LANCZOS)

            output_path = os.path.join(output_dir, f"img-{i}.png")
            img_resized.save(output_path, format="PNG")

            i += 1
    log.info(f"Finished converting {i} images for user_id: {user_id}")

    # Generating description with images
    log.info("Starting generating description with images")
    for filename in os.listdir(output_dir):
        if filename.lower().endswith(".png"):
            img_path = os.path.join(output_dir, filename)
            image = open(img_path, "rb")
            # generate caption
            output = replicate_client.run(
                "yorickvp/llava-13b:80537f9eead1a5bfa72d5ac6ea6414379be41d4d4f6679fd776e9535d1eb58bb",
                input={
                    "image": image,
                    "prompt": "Please write a caption for this image. Focus on person details 60%. Focus on surrounding 40%. Make description as much as possible."
                    }
                )
            response = " ".join(list(output))

            caption = f"A photo of POK. {response}"

            caption_filename = img_path.split(".")[0] + ".txt"
            log.debug(f"Generated description for image {caption}")
            log.debug(f"Saving capture for file: {filename}")
            with open(caption_filename, "w") as file:
                file.write(caption)
            log.debug(f"Saved capture for file: {filename} complete")

    shutil.make_archive(output_dir, "zip", f"media/{user_id}/")

    # Initialising model
    model = replicate_client.models.create(
        owner="vladimyr1991",
        name=f"flux-dev-{user_id}",
        visibility="private",
        hardware="gpu-t4",
        description=f"FLUX.1 finetuned on {user_id}"
        )

    log.info(f"Model created: {model.name}")
    log.info(f"Model URL: https://replicate.com/{model.owner}/{model.name}")
    with open(f"media/{user_id}/data.zip", "rb") as image:
        training = replicate_client.trainings.create(
            version="ostris/flux-dev-lora-trainer:b6af14222e6bd9be257cbc1ea4afda3cd0503e1133083b9d1de0364d8568e6ef",
            input={
                "input_images": image,
                "steps": 1000,
                },
            destination=f"{model.owner}/{model.name}"
            )
    log.info(f"Training created: {training.status}")
    log.info(f"Training URL: https://replicate.com/p/{training.id}")

    log.info(f"Starting training for user_id {user_id} in progress")
    while training.status in ["queued", "processing"]:
        await asyncio.sleep(2)
        training = replicate_client.trainings.get(training.id)
        log.debug(f"Training status is {training.status} ")

    if training.status == "succeeded":
        processing_succeed = True
    else:
        processing_succeed = False
    train_model_metadata = dict(
        user_id=user_id,
        model_name=model.name,
        model_url=f"https://replicate.com/{model.owner}/{model.name}",
        training_id=training.id,
        training_url=f"https://replicate.com/p/{training.id}",
        training_status=training.status
        )
    with open(f"media/{user_id}/train_model_metadata.json", "w") as file:
        json.dump(train_model_metadata, file)

    return processing_succeed
