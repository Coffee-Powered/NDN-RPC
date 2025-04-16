import numpy as np 
from numpy import ndarray
from PIL import Image, ImageOps
import io

# Large input -> Small output
def average_pixel(data: bytes) -> tuple[int]:
    image = Image.open(io.BytesIO(data))
    image_array: ndarray = np.array(image)

    print(f"--- Function stdout ---")
    print(f"Shape: {image_array.shape}")
    print(f"Item [0][0]: {image_array[0][0]}")

    image_array_average = np.average(image_array, axis=0)          # Average over cols
    image_array_average = np.average(image_array_average, axis=0)  # Average overall
    
    if type(image_array_average) != np.float64:
        # Convert RGB values to ints and convert list to tuple.
        image_array_average = tuple(map(int, image_array_average))
    else:
        # Create RGB values from single int (greyscale), cast as tuple.
        image_array_average = tuple([int(image_array_average)]*3)

    print(f"Average pixel: {image_array_average}")
    print(f"-----------------------")
    return image_array_average

# Large input -> Large output
def desaturate_image(data: bytes) -> bytes:
    image = Image.open(io.BytesIO(data))    
    image_desat = ImageOps.grayscale(image)
    buffer = io.BytesIO()
    image_desat.save(buffer, format=image.format)
    
    return buffer.getvalue()

# Small input -> Small output
def fibonacci(value: int) -> int:
    if value < 3:
        return 1
    else:
        return fibonacci(value-1) + fibonacci(value-2)

# Small input -> Large output
def color_image(value: tuple) -> bytes:
    height, width = 60, 80

    image_array: ndarray = np.full((height, width, 3), list(value), dtype=np.uint8)
    image = Image.fromarray(image_array)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    
    return buffer.getvalue()


# if __name__ == "__main__":
#     # from pathlib import Path
#     # path_images: Path = Path(Path.cwd().as_uri().split("code")[0]+"images")
#     from os import getcwd
#     path_images: str = getcwd().split("code")[0]+"images"
#    
#     print(path_images)
#     with open(f"{path_images}/coffee-small.jpg", "rb") as f:
#         img_desat: bytes = desaturate_image(f.read())
#         print("Image desaturated.")
#         pixel_av: tuple[float] = average_pixel(img_desat)
#         print(f"Average pixel: {pixel_av}")