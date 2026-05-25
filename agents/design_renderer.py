import math
import re
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CANVAS_WIDTH = 4500
CANVAS_HEIGHT = 5400


def sanitize_text(text):
    if not text:
        return ""

    text = text.strip()
    text = text.replace("**", "")
    text = text.replace("*", "")
    text = text.replace('"', "")
    text = text.replace("'", "")
    text = re.sub(r"[{}[\]<>`~]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def get_font(size, bold=True):
    possible_fonts = []

    if bold:
        possible_fonts.extend([
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
        ])
    else:
        possible_fonts.extend([
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
        ])

    for font_path in possible_fonts:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size=size)

    return ImageFont.load_default()


def text_bbox(draw, text, font):
    return draw.textbbox((0, 0), text, font=font)


def text_width(draw, text, font):
    bbox = text_bbox(draw, text, font)
    return bbox[2] - bbox[0]


def text_height(draw, text, font):
    bbox = text_bbox(draw, text, font)
    return bbox[3] - bbox[1]


def wrap_text_to_fit(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = word if not current else current + " " + word

        if text_width(draw, test, font) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def find_best_font_and_lines(draw, text, starting_size, min_size, max_width, max_lines=3):
    size = starting_size

    while size >= min_size:
        font = get_font(size, bold=True)
        lines = wrap_text_to_fit(draw, text, font, max_width)

        too_wide = any(text_width(draw, line, font) > max_width for line in lines)

        if not too_wide and len(lines) <= max_lines:
            return font, lines

        size -= 20

    font = get_font(min_size, bold=True)
    lines = wrap_text_to_fit(draw, text, font, max_width)
    return font, lines


def draw_centered_lines(draw, lines, font, center_y, image_width, fill, spacing=55):
    heights = [text_height(draw, line, font) for line in lines]
    total_height = sum(heights) + spacing * (len(lines) - 1)

    y = center_y - total_height // 2

    for line, height in zip(lines, heights):
        width = text_width(draw, line, font)
        x = (image_width - width) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += height + spacing


def draw_text_with_shadow(draw, position, text, font, fill, shadow_fill=(0, 0, 0, 90), offset=18):
    x, y = position
    draw.text((x + offset, y + offset), text, font=font, fill=shadow_fill)
    draw.text((x, y), text, font=font, fill=fill)


def draw_text_with_outline(draw, position, text, font, fill, outline_fill, stroke_width=12):
    draw.text(
        position,
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=outline_fill
    )


def crop_to_content(image, padding=220):
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()

    if not bbox:
        return image

    left, top, right, bottom = bbox

    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(image.width, right + padding)
    bottom = min(image.height, bottom + padding)

    return image.crop((left, top, right, bottom))


def color_tuple(color_name):
    colors = {
        "black": (0, 0, 0, 255),
        "white": (255, 255, 255, 255),
        "cream": (245, 235, 220, 255),
        "tan": (180, 140, 90, 255),
        "brown": (95, 65, 40, 255),
        "pink": (220, 120, 150, 255),
        "red": (190, 50, 50, 255),
        "orange": (210, 110, 45, 255),
        "green": (70, 125, 85, 255),
        "blue": (65, 105, 160, 255),
    }

    return colors.get(color_name, colors["black"])


def create_canvas():
    return Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (255, 255, 255, 0))


def draw_star(draw, x, y, size, fill):
    points = []
    for i in range(10):
        angle = math.pi / 5 * i - math.pi / 2
        radius = size if i % 2 == 0 else size * 0.45
        px = x + math.cos(angle) * radius
        py = y + math.sin(angle) * radius
        points.append((px, py))

    draw.polygon(points, fill=fill)


def draw_heart(draw, x, y, size, fill):
    # Simple heart made from circles and triangle
    r = size // 3
    draw.ellipse((x - r * 2, y - r, x, y + r), fill=fill)
    draw.ellipse((x, y - r, x + r * 2, y + r), fill=fill)
    points = [(x - r * 2, y), (x + r * 2, y), (x, y + size)]
    draw.polygon(points, fill=fill)


def draw_sparkles(draw, fill):
    for x, y, size in [
        (850, 1450, 95),
        (3650, 1500, 85),
        (1050, 3850, 75),
        (3450, 3850, 95),
    ]:
        draw_star(draw, x, y, size, fill)


def draw_small_hearts(draw, fill):
    for x, y, size in [
        (850, 1600, 130),
        (3600, 1600, 120),
        (1000, 3800, 110),
        (3450, 3800, 120),
    ]:
        draw_heart(draw, x, y, size, fill)


def render_retro_bold(main_text, sub_text, output_path, text_color="black"):
    image = create_canvas()
    draw = ImageDraw.Draw(image)

    fill = color_tuple(text_color)
    accent = color_tuple("orange")

    main_text = sanitize_text(main_text).upper()
    sub_text = sanitize_text(sub_text).upper()

    # Retro decorative lines
    draw.arc((650, 900, 3850, 4400), start=205, end=335, fill=accent, width=35)
    draw.arc((850, 1050, 3650, 4250), start=205, end=335, fill=accent, width=20)

    draw_sparkles(draw, accent)

    font, lines = find_best_font_and_lines(
        draw,
        main_text,
        starting_size=620,
        min_size=220,
        max_width=3100,
        max_lines=3
    )

    draw_centered_lines(
        draw=draw,
        lines=lines,
        font=font,
        center_y=2600,
        image_width=CANVAS_WIDTH,
        fill=fill,
        spacing=65
    )

    if sub_text:
        sub_font = get_font(170, bold=True)
        sub_width = text_width(draw, sub_text, sub_font)
        x = (CANVAS_WIDTH - sub_width) // 2
        draw.text((x, 3600), sub_text, font=sub_font, fill=fill)

    cropped = crop_to_content(image)
    cropped.save(output_path, "PNG")
    return cropped.width, cropped.height


def render_arched_text(main_text, sub_text, output_path, text_color="black"):
    image = create_canvas()
    draw = ImageDraw.Draw(image)

    fill = color_tuple(text_color)
    accent = color_tuple("tan")

    main_text = sanitize_text(main_text).upper()
    sub_text = sanitize_text(sub_text).upper()

    # Badge circle
    draw.ellipse((850, 950, 3650, 4250), outline=accent, width=28)
    draw.ellipse((1050, 1150, 3450, 4050), outline=accent, width=14)

    font, lines = find_best_font_and_lines(
        draw,
        main_text,
        starting_size=520,
        min_size=200,
        max_width=2500,
        max_lines=3
    )

    draw_centered_lines(
        draw=draw,
        lines=lines,
        font=font,
        center_y=2650,
        image_width=CANVAS_WIDTH,
        fill=fill,
        spacing=50
    )

    if sub_text:
        sub_font = get_font(155, bold=True)
        sub_width = text_width(draw, sub_text, sub_font)
        x = (CANVAS_WIDTH - sub_width) // 2
        draw.text((x, 3650), sub_text, font=sub_font, fill=fill)

    draw_star(draw, 2250, 1375, 90, accent)
    draw_star(draw, 2250, 3925, 90, accent)

    cropped = crop_to_content(image)
    cropped.save(output_path, "PNG")
    return cropped.width, cropped.height


def render_minimal_badge(main_text, sub_text, output_path, text_color="black"):
    image = create_canvas()
    draw = ImageDraw.Draw(image)

    fill = color_tuple(text_color)

    main_text = sanitize_text(main_text).upper()
    sub_text = sanitize_text(sub_text).upper()

    # Rounded rectangle badge using thick lines
    draw.rounded_rectangle(
        (600, 1550, 3900, 3850),
        radius=260,
        outline=fill,
        width=35
    )

    font, lines = find_best_font_and_lines(
        draw,
        main_text,
        starting_size=520,
        min_size=200,
        max_width=2700,
        max_lines=3
    )

    draw_centered_lines(
        draw=draw,
        lines=lines,
        font=font,
        center_y=2650,
        image_width=CANVAS_WIDTH,
        fill=fill,
        spacing=55
    )

    # Small divider marks
    draw.line((1100, 3400, 1800, 3400), fill=fill, width=20)
    draw.line((2700, 3400, 3400, 3400), fill=fill, width=20)

    if sub_text:
        sub_font = get_font(150, bold=True)
        sub_width = text_width(draw, sub_text, sub_font)
        x = (CANVAS_WIDTH - sub_width) // 2
        draw.text((x, 3575), sub_text, font=sub_font, fill=fill)

    cropped = crop_to_content(image)
    cropped.save(output_path, "PNG")
    return cropped.width, cropped.height


def render_cute_doodle(main_text, sub_text, output_path, text_color="black"):
    image = create_canvas()
    draw = ImageDraw.Draw(image)

    fill = color_tuple(text_color)
    accent = color_tuple("pink")

    main_text = sanitize_text(main_text).upper()
    sub_text = sanitize_text(sub_text).upper()

    draw_small_hearts(draw, accent)

    # Doodle underline
    draw.arc((1000, 3300, 3500, 3900), start=200, end=340, fill=accent, width=30)

    font, lines = find_best_font_and_lines(
        draw,
        main_text,
        starting_size=560,
        min_size=210,
        max_width=3000,
        max_lines=3
    )

    draw_centered_lines(
        draw=draw,
        lines=lines,
        font=font,
        center_y=2550,
        image_width=CANVAS_WIDTH,
        fill=fill,
        spacing=60
    )

    if sub_text:
        sub_font = get_font(150, bold=True)
        sub_width = text_width(draw, sub_text, sub_font)
        x = (CANVAS_WIDTH - sub_width) // 2
        draw.text((x, 3550), sub_text, font=sub_font, fill=fill)

    cropped = crop_to_content(image)
    cropped.save(output_path, "PNG")
    return cropped.width, cropped.height


def render_design(style, main_text, sub_text, output_path, text_color="black"):
    style = (style or "retro_bold").lower().strip()

    if style == "retro_bold":
        return render_retro_bold(main_text, sub_text, output_path, text_color)

    if style == "arched_text":
        return render_arched_text(main_text, sub_text, output_path, text_color)

    if style == "minimal_badge":
        return render_minimal_badge(main_text, sub_text, output_path, text_color)

    if style == "cute_doodle":
        return render_cute_doodle(main_text, sub_text, output_path, text_color)

    # Fallback
    return render_retro_bold(main_text, sub_text, output_path, text_color)