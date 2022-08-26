from PIL import Image, ImageEnhance
import pygame as pg


def pg2pil(img: pg.Surface):
    return Image.frombytes('RGBA', img.get_size(), pg.image.tostring(img, 'RGBA', False))


def pil2pg(img: Image):
    return pg.image.frombuffer(img.tobytes(), img.size, 'RGBA')


def grayscale(img: pg.surface.Surface):
    img = pg2pil(img)
    img = img.convert("LA").convert("RGBA")
    return pil2pg(img)


def reduce_opacity(im, opacity):
    """Returns an image with reduced opacity."""
    opacity = max(min(1, opacity), 0)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im


def overlay(bg: pg.surface.Surface, fg: pg.surface.Surface, fg_alpha: float = 1):
    img = Image.new('RGBA', bg.get_size())
    bg = pg2pil(bg)
    fg = pg2pil(fg)
    fg = fg.resize(bg.size)
    fg = reduce_opacity(fg, fg_alpha)
    img = Image.alpha_composite(img, bg)
    img = Image.alpha_composite(img, fg)
    bg.paste(fg, (0, 0), fg)
    return pil2pg(img)
