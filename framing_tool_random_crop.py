import os
import random
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATIONS ---
PRINT_DPI = 300
STICKING_MARGIN_CM = 1  # Extra margin for sticking behind mount board
VIRTUAL_MOUNT_RATIO = 0.85  # Virtual mount board takes up 85% of frame visible area
# Updated Officeworks print sizes (in cm)
OFFICEWORKS_PRINT_SIZES_CM = [
    (15, 10), (12.5, 12.5), (12.5, 18), (15, 15), (15, 20.5),
    (20.5, 20.5), (20.5, 25.5), (20.5, 30.5), (28, 35.5),
    (30.5, 30.5), (30.5, 40.6), (30.5, 45.5)
]

FRAME_AND_MOUNT_OPTIONS = [
    # [frame_h, frame_w, mount_h, mount_w] or None for no mount
    [24.5, 19, None, None],
    [13.7, 8.7, None, None],
    [None, None, 8.4, 10.8],
    [None, None, 37.6, 27.3],
    [24.3, 32.8, None, None],
    [28.7, 20, None, None],
    [28.5, 22.7, None, None],
    [None, None, 36.5, 29.5],
    [24.2, 19.3, None, None],
    [49.4, 39.1, None, None],
]

# --- HELPERS ---
def cm_to_pixels(cm):
    return int((cm / 2.54) * PRINT_DPI)

def find_closest_print_size(w_cm, h_cm):
    options = [(w, h) for (w, h) in OFFICEWORKS_PRINT_SIZES_CM] + [(h, w) for (w, h) in OFFICEWORKS_PRINT_SIZES_CM]
    return min(options, key=lambda size: abs(size[0] - w_cm) + abs(size[1] - h_cm))

def resize_and_random_crop(img, target_w, target_h, seed=None):
    if seed is not None:
        random.seed(seed)
    
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h

    # Resize first (preserve aspect ratio, but overshoot target in one dimension)
    if img_ratio > target_ratio:
        new_height = target_h
        new_width = int(target_h * img_ratio)
    else:
        new_width = target_w
        new_height = int(target_w / img_ratio)

    img = img.resize((new_width, new_height), Image.LANCZOS)

    # Random crop position
    max_x = new_width - target_w
    max_y = new_height - target_h
    left = random.randint(0, max_x) if max_x > 0 else 0
    top = random.randint(0, max_y) if max_y > 0 else 0

    return img.crop((left, top, left + target_w, top + target_h))

def generate_print_file(img_path, target_w_px, target_h_px, output_name, seed):
    img = Image.open(img_path)
    img = resize_and_random_crop(img, target_w_px, target_h_px, seed)
    img.save(os.path.join("output_random", f"{output_name}_print.jpg"), dpi=(PRINT_DPI, PRINT_DPI))

def generate_visual(img_path, frame_w_px, frame_h_px, mount_w_px, mount_h_px, output_name, seed):
    canvas = Image.new("RGB", (frame_w_px, frame_h_px), color="white")
    img = Image.open(img_path)
    cropped = resize_and_random_crop(img, mount_w_px, mount_h_px, seed)
    top_margin = max(0, int((frame_h_px - mount_h_px) * 0.4))
    left = (frame_w_px - mount_w_px) // 2
    canvas.paste(cropped, (left, top_margin))
    draw = ImageDraw.Draw(canvas)
    text_area_h = int((frame_h_px - mount_h_px) * 0.6)
    text_area_h = min(text_area_h, frame_h_px)
    draw.rectangle([0, max(0, frame_h_px - text_area_h), frame_w_px, frame_h_px], fill="white")
    canvas.save(os.path.join("output_random", f"{output_name}_visual.jpg"), dpi=(PRINT_DPI, PRINT_DPI))

def process_all_photos(photo_paths, num_to_select=10):
    selected_photos = random.sample(photo_paths, min(num_to_select, len(photo_paths)))

    for i, img_path in enumerate(selected_photos):
        choice = random.choice(FRAME_AND_MOUNT_OPTIONS)
        frame_h, frame_w, mount_h, mount_w = choice
        
        # Generate a unique seed for this photo based on its index and filename
        seed = hash((i, os.path.basename(img_path)))

        if mount_h and mount_w:
            # CASE 1: Mount provided (ignore frame if not given)
            output_name = f"photo_{i+1}_mount_{mount_w:.1f}x{mount_h:.1f}"
            
            # Calculate print dimensions (mount size + sticking margin)
            print_w_cm = mount_w + STICKING_MARGIN_CM * 2
            print_h_cm = mount_h + STICKING_MARGIN_CM * 2
            closest_w, closest_h = find_closest_print_size(print_w_cm, print_h_cm)
            print_w_px = cm_to_pixels(closest_w)
            print_h_px = cm_to_pixels(closest_h)
            
            # For the visual, we'll show the mount size with a small border
            visual_frame_w_px = cm_to_pixels(mount_w + 2)  # 1cm border each side
            visual_frame_h_px = cm_to_pixels(mount_h + 2)
            mount_w_px = cm_to_pixels(mount_w)
            mount_h_px = cm_to_pixels(mount_h)
            
            generate_print_file(img_path, print_w_px, print_h_px, output_name, seed)
            generate_visual(img_path, visual_frame_w_px, visual_frame_h_px, mount_w_px, mount_h_px, output_name, seed)

        else:
            # CASE 2: No mount, frame only => calculate virtual mount
            virtual_mount_w = round(frame_w * VIRTUAL_MOUNT_RATIO, 1)
            virtual_mount_h = round(frame_h * VIRTUAL_MOUNT_RATIO, 1)
            output_name = f"photo_{i+1}_frame_{frame_w:.1f}x{frame_h:.1f}"
            
            # For the print, we'll use the virtual mount size plus sticking margin
            print_w_cm = virtual_mount_w + STICKING_MARGIN_CM * 2
            print_h_cm = virtual_mount_h + STICKING_MARGIN_CM * 2
            closest_w, closest_h = find_closest_print_size(print_w_cm, print_h_cm)
            print_w_px = cm_to_pixels(closest_w)
            print_h_px = cm_to_pixels(closest_h)
            
            # For the visual, we'll show the frame with virtual mount
            frame_w_px = cm_to_pixels(frame_w)
            frame_h_px = cm_to_pixels(frame_h)
            mount_w_px = cm_to_pixels(virtual_mount_w)
            mount_h_px = cm_to_pixels(virtual_mount_h)
            
            # THE KEY FIX: Use the same dimensions for both crops
            # We'll use the virtual mount size for both
            generate_print_file(img_path, mount_w_px, mount_h_px, output_name, seed)
            generate_visual(img_path, frame_w_px, frame_h_px, mount_w_px, mount_h_px, output_name, seed)

# Example batch usage
os.makedirs("output_random", exist_ok=True)
photo_folder = "input_photos"
photos = [os.path.join(photo_folder, f) for f in os.listdir(photo_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
process_all_photos(photos)