#!/usr/bin/env python3
"""Gera infográfico PNG das tecnologias de teste do projeto."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "infograficos" / "Infografico-Tecnologias-de-Teste.png"

# Paleta alinhada aos infográficos existentes
NAVY = (26, 54, 93)
BLUE = (44, 82, 130)
SLATE = (45, 55, 72)
MUTED = (74, 85, 104)
WHITE = (255, 255, 255)
LIGHT = (247, 250, 252)
GREEN = (56, 161, 105)
ORANGE = (221, 107, 32)
RED_SOFT = (229, 62, 62)
CARD_BG = (255, 255, 255)
BORDER = (203, 213, 224)

W, H = 1600, 1000


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] | None = None,
) -> None:
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=2 if outline else 0)


def _center_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
) -> None:
    x0, y0, x1, y1 = box
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=4, align="center")
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = x0 + (x1 - x0 - tw) // 2
    y = y0 + (y1 - y0 - th) // 2
    draw.multiline_text((x, y), text, font=font, fill=fill, spacing=4, align="center")


def _draw_header(draw: ImageDraw.ImageDraw, title: str, subtitle: str) -> None:
    draw.rectangle((0, 0, W, 110), fill=NAVY)
    draw.text((40, 22), title, font=_font(34, True), fill=WHITE)
    draw.text((40, 68), subtitle, font=_font(16), fill=(203, 213, 224))


def _draw_tool_bar(draw: ImageDraw.ImageDraw, y: int) -> None:
    tools = [
        ("pytest", "Testes unitários"),
        ("Ruff", "Lint E/F/I/UP/B"),
        ("GitHub Actions", "CI ubuntu-latest"),
        ("Python 3.11", "Runner + local"),
    ]
    gap = 20
    card_w = (W - 80 - gap * 3) // 4
    for i, (name, desc) in enumerate(tools):
        x0 = 40 + i * (card_w + gap)
        _rounded_rect(draw, (x0, y, x0 + card_w, y + 72), 10, BLUE)
        _center_text(draw, (x0, y + 8, x0 + card_w, y + 42), name, _font(17, True), WHITE)
        _center_text(draw, (x0, y + 38, x0 + card_w, y + 68), desc, _font(11), (226, 232, 240))


def _draw_section_title(draw: ImageDraw.ImageDraw, x: int, y: int, num: str, title: str) -> int:
    draw.ellipse((x, y, x + 36, y + 36), fill=BLUE)
    _center_text(draw, (x, y, x + 36, y + 36), num, _font(18, True), WHITE)
    draw.text((x + 48, y + 6), title, font=_font(20, True), fill=NAVY)
    return y + 48


def _draw_test_files(draw: ImageDraw.ImageDraw, x: int, y: int, w: int) -> int:
    y = _draw_section_title(draw, x, y, "1", "Arquivos de teste (tests/)")
    files = [
        ("test_config.py", "PipelineConfig.from_environ()\nvars obrigatórias + defaults"),
        ("test_violence.py", "is_violence_detected()\nkeypoints falsos (NumPy)"),
        ("test_transcribe_config.py", "TranscribePipelineConfig\nparse URIs S3 + prefixos"),
        ("test_transcribe_imports.py", "transcribe_cli não importa\npipeline nem cv2"),
    ]
    gap = 16
    cw = (w - gap) // 2
    ch = 118
    for i, (fname, desc) in enumerate(files):
        col, row = i % 2, i // 2
        x0 = x + col * (cw + gap)
        y0 = y + row * (ch + gap)
        _rounded_rect(draw, (x0, y0, x0 + cw, y0 + ch), 10, CARD_BG, BORDER)
        draw.text((x0 + 14, y0 + 12), fname, font=_font(14, True), fill=BLUE)
        draw.multiline_text((x0 + 14, y0 + 40), desc, font=_font(12), fill=SLATE, spacing=3)
    return y + 2 * (ch + gap) + 8


def _draw_support_tech(draw: ImageDraw.ImageDraw, x: int, y: int, w: int) -> int:
    y = _draw_section_title(draw, x, y, "2", "Recursos de apoio nos testes")
    items = [
        ("pytest.MonkeyPatch", "Simula env vars\nsem AWS / OpenAI real"),
        ("NumPy", "Arrays sintéticos\nde keypoints"),
        ("_FakeKpts", "Mock leve da API\nUltralytics (sem modelo)"),
        ("pytest.raises", "Validação de erros\nde configuração"),
    ]
    gap = 14
    cw = (w - 3 * gap) // 4
    ch = 100
    for i, (name, desc) in enumerate(items):
        x0 = x + i * (cw + gap)
        _rounded_rect(draw, (x0, y, x0 + cw, y + ch), 10, LIGHT, BORDER)
        draw.text((x0 + 12, y + 10), name, font=_font(12, True), fill=NAVY)
        draw.multiline_text((x0 + 12, y + 36), desc, font=_font(11), fill=MUTED, spacing=2)
    return y + ch + 20


def _draw_ci_pipeline(draw: ImageDraw.ImageDraw, x: int, y: int, w: int) -> int:
    y = _draw_section_title(draw, x, y, "3", "Esteira CI — .github/workflows/ci-cd.yml")
    steps = [
        ("Ruff", "lint-test"),
        ("Pytest", "lint-test"),
        ("Docker\nbuild", "docker-build"),
        ("Terraform\nfmt+validate", "terraform-check"),
    ]
    arrow_w = 36
    n = len(steps)
    box_w = (w - arrow_w * (n - 1)) // n
    bh = 88
    for i, (label, job) in enumerate(steps):
        x0 = x + i * (box_w + arrow_w)
        color = GREEN if i < 2 else BLUE
        _rounded_rect(draw, (x0, y, x0 + box_w, y + bh), 10, color)
        _center_text(draw, (x0, y + 8, x0 + box_w, y + 52), label, _font(15, True), WHITE)
        _center_text(draw, (x0, y + 52, x0 + box_w, y + 82), f"job: {job}", _font(10), (226, 232, 240))
        if i < n - 1:
            ax = x0 + box_w + 6
            draw.polygon([(ax, y + bh // 2 - 12), (ax + 24, y + bh // 2), (ax, y + bh // 2 + 12)], fill=MUTED)

    note_y = y + bh + 14
    draw.text(
        (x, note_y),
        "Instalação CI: pip install -e \".[dev,transcribe]\"  |  Comando: pytest -q --tb=short",
        font=_font(12),
        fill=MUTED,
    )
    return note_y + 28


def _draw_out_of_scope(draw: ImageDraw.ImageDraw, x: int, y: int, w: int) -> int:
    y = _draw_section_title(draw, x, y, "4", "Fora do escopo dos testes (proposital)")
    excluded = [
        "Ultralytics / YOLO",
        "OpenCV (cv2)",
        "boto3 / S3 real",
        "ECS / Fargate",
        "pytest-cov*",
        "Vídeos de exemplo",
    ]
    gap = 12
    cw = (w - 5 * gap) // 6
    ch = 56
    for i, label in enumerate(excluded):
        x0 = x + i * (cw + gap)
        _rounded_rect(draw, (x0, y, x0 + cw, y + ch), 8, (254, 242, 242), RED_SOFT)
        # linha diagonal "proibido"
        draw.line((x0 + 8, y + 10, x0 + cw - 8, y + ch - 10), fill=RED_SOFT, width=2)
        _center_text(draw, (x0 + 4, y + 8, x0 + cw - 4, y + ch - 4), label, _font(10), RED_SOFT)
    draw.text(
        (x, y + ch + 10),
        "* pytest-cov declarado em pyproject.toml [dev], mas não executado no CI",
        font=_font(11),
        fill=MUTED,
    )
    return y + ch + 36


def build_image() -> Image.Image:
    img = Image.new("RGB", (W, H), LIGHT)
    draw = ImageDraw.Draw(img)

    _draw_header(
        draw,
        "Cobertura de Testes",
        "Pipeline YOLOv8 Pose — testes leves, offline e sem download de pesos YOLO",
    )

    _draw_tool_bar(draw, 130)

    left_x, right_x = 40, W // 2 + 20
    col_w = W // 2 - 60

    y_left = 230
    y_left = _draw_test_files(draw, left_x, y_left, col_w)
    y_left = _draw_support_tech(draw, left_x, y_left, col_w)

    y_right = 230
    y_right = _draw_ci_pipeline(draw, right_x, y_right, col_w)
    y_right = _draw_out_of_scope(draw, right_x, y_right, col_w)

    # Rodapé — resumo
    footer_y = max(y_left, y_right) + 10
    _rounded_rect(draw, (40, footer_y, W - 40, footer_y + 70), 12, NAVY)
    _center_text(
        draw,
        (50, footer_y + 10, W - 50, footer_y + 60),
        "~12 casos de teste  •  4 arquivos  •  Qualidade: Ruff + Pytest + Docker build + Terraform validate\n"
        "Princípio: validar lógica e config sem custo de GPU, rede AWS ou modelos pesados",
        _font(14),
        WHITE,
    )

    return img


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    img = build_image()
    img.save(OUTPUT, "PNG", optimize=True)
    print(f"Infográfico gerado: {OUTPUT}")


if __name__ == "__main__":
    main()
