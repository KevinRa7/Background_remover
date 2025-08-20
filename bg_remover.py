import argparse
import os
import sys
from rembg import remove
from PIL import Image, ImageFilter
from io import BytesIO
import requests

# Supported image formats
SUPPORTED_EXTENSIONS = [
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff",
    ".webp", ".svg", ".heif", ".heic", ".raw", ".cr2", ".nef", ".arw"
]

def is_supported(file_path_or_url):
    """Check if the file extension is supported."""
    _, ext = os.path.splitext(file_path_or_url.lower())
    if ext not in SUPPORTED_EXTENSIONS:
        print(f"Error: Unsupported file type '{ext}'. Please use one of {SUPPORTED_EXTENSIONS}")
        return False
    return True

def soften_edges(image):
    """Apply GaussianBlur to the alpha channel for smoother edges."""
    alpha = image.split()[-1]
    # Apply Gaussian blur to the alpha channel
    alpha = alpha.filter(ImageFilter.GaussianBlur(radius=1.5))
    image.putalpha(alpha)
    return image

def process_image(input_image, output_path):
    """Remove background, soften edges, and save the image."""
    try:
        print("Removing background...")
        output_image = remove(input_image)

        print("Softening edges...")
        output_image = soften_edges(output_image)

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        print(f"Saving processed image to {output_path}...")
        output_image.save(output_path, "PNG")
        print("Successfully saved the image.")
    except Exception as e:
        print(f"An error occurred during image processing: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Main function to parse arguments and initiate background removal."""
    parser = argparse.ArgumentParser(
        description="Remove background from an image using the rembg library.",
        epilog="Example usage:\n"
               "  python bg_remover.py --url https://example.com/image.jpg --output result.png\n"
               "  python bg_remover.py --file ./mypic.jpg --output clean.png",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Input group - either URL or local file must be provided
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--url", help="URL of the image to process.")
    input_group.add_argument("--file", help="Path to the local image file to process.")

    # Output argument
    parser.add_argument("--output", required=True, help="Path to save the processed transparent PNG file.")

    args = parser.parse_args()

    input_path = args.url if args.url else args.file
    if not is_supported(input_path):
        sys.exit(1)

    try:
        if args.url:
            print(f"Downloading image from URL: {args.url}")
            response = requests.get(args.url, stream=True)
            response.raise_for_status()
            input_image = Image.open(BytesIO(response.content))
        else: # args.file
            if not os.path.exists(args.file):
                print(f"Error: File not found at '{args.file}'", file=sys.stderr)
                sys.exit(1)
            print(f"Opening local image file: {args.file}")
            input_image = Image.open(args.file)

        process_image(input_image, args.output)

    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error opening or reading image file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
