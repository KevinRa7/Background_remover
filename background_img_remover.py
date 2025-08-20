import os
import requests
import numpy as np
from rembg import remove
from PIL import Image, ImageFilter
from io import BytesIO

# Supported image formats
SUPPORTED_EXTENSIONS = [
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff",
    ".webp", ".svg", ".heif", ".heic", ".raw", ".cr2", ".nef", ".arw"
]

def is_supported(file_path_or_url):
    """Check if the file extension is supported."""
    _, ext = os.path.splitext(file_path_or_url.lower())
    return ext in SUPPORTED_EXTENSIONS

def refine_edges(output_image):
    """Clean halos and smooth edges of the cutout."""
    output_image = output_image.convert("RGBA")

    # Extract alpha channel
    alpha = output_image.split()[-1]

    # Erode/Dilate to tighten mask
    alpha = alpha.filter(ImageFilter.MinFilter(3))  # shrink
    alpha = alpha.filter(ImageFilter.MaxFilter(3))  # expand

    # Smooth edges
    alpha = alpha.filter(ImageFilter.GaussianBlur(radius=1.5))
    output_image.putalpha(alpha)

    # Convert to NumPy for halo removal
    arr = np.array(output_image)

    # Detect near-white pixels (halo areas) by correctly accessing color channels.
    # The original `arr.T` swapped height and width, causing a shape mismatch.
    # `np.rollaxis` correctly separates channels while preserving dimensions.
    r, g, b, a = np.rollaxis(arr, axis=-1)
    white_areas = (r > 200) & (g > 200) & (b > 200) & (a > 0)

    # Set alpha channel to 0 for white areas to make them transparent.
    # This is the correct way to index and assign values in NumPy.
    arr[white_areas, 3] = 0

    return Image.fromarray(arr)

def remove_background_from_url(image_url, output_path="output/output.png"):
    """Remove background from image downloaded via URL."""
    if not is_supported(image_url):
        print(f"[URL] Unsupported file type: {image_url}")
        return

    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        input_image = Image.open(BytesIO(response.content))

        # Remove background with alpha matting
        output_image = remove(
            input_image,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10
        )

        # Refine edges
        output_image = refine_edges(output_image)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        output_image.save(output_path, "PNG")

        print(f"[URL] Background removed successfully. Saved at: {output_path}")
    except Exception as e:
        print(f"[URL] Error: {e}")

def remove_background_from_file(input_path, output_path="output/output.png"):
    """Remove background from a local file."""
    if not is_supported(input_path):
        print(f"[FILE] Unsupported file type: {input_path}")
        return

    try:
        input_image = Image.open(input_path)

        # Remove background with alpha matting
        output_image = remove(
            input_image,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10
        )

        # Refine edges
        output_image = refine_edges(output_image)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        output_image.save(output_path, "PNG")

        print(f"[FILE] Background removed successfully. Saved at: {output_path}")
    except Exception as e:
        print(f"[FILE] Error: {e}")

if __name__ == "__main__":
    # --- Example for local file ---
    # To use this, replace 'path/to/your/image.jpg' with the actual file path.
    # example_file = "path/to/your/image.jpg"
    # if os.path.exists(example_file):
    #     remove_background_from_file(example_file, "output/local_result.png")
    # else:
    #     print(f"File not found: {example_file}. Please update the path.")

    # --- Example for URL ---
    # To use this, uncomment the lines and provide a valid image URL.
    # example_url = "https://i.ibb.co/chZkSMv/pexels-pixabay-220453.jpg"
    # remove_background_from_url(example_url, "output/url_result.png")

    print("Script finished. Modify the '__main__' block to process your files.")
