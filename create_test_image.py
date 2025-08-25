from PIL import Image, ImageDraw

def create_test_image(filename="test_image.png"):
    """Creates a simple test image with a red square on a white background."""
    img = Image.new('RGB', (200, 200), color = 'white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 150, 150], fill='red')
    img.save(filename)
    print(f"Test image saved as {filename}")

if __name__ == '__main__':
    create_test_image()
