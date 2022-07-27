import base64
import logging
from io import BytesIO
from PIL import Image


def base64_decode_image(image_base64):
    return Image.open(BytesIO(base64.b64decode(image_base64)))


def base64_encode_image(image: Image) -> str:
    buffered = BytesIO()
    image.save(buffered, 'JPEG')
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def combine_images(decoded_images: list[Image]) -> Image:
    if len(decoded_images) == 0:
        logging.error('No images received, aborting.')
        raise ZeroImagesReceivedException

    if len(decoded_images) != 9:
        logging.warning(f'Received a bad number of images - {len(decoded_images)}, expected 9. Will return only one.')
        return decoded_images[0]

    w, h = decoded_images[0].size
    combined_image = Image.new('RGB', (w*3, h*3))

    for row in range(3):
        for column in range(3):
            current_image = decoded_images[row*3 + column]
            combined_image.paste(current_image, (column*w, row*h))

    return combined_image


def combine_base64_images(images_base64: list[str]) -> str:
    decoded_images = [base64_decode_image(image_base64) for image_base64 in images_base64]
    combined_image = combine_images(decoded_images)
    return base64_encode_image(combined_image)


class ZeroImagesReceivedException(Exception):
    pass
