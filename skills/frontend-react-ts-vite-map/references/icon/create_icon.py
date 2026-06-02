"""_summary_
このスクリプトは、指定された画像ファイルを指定したピクセルサイズのICO/SVG/PNG形式に変換します。黒い部分は透明化されます。
デフォルトでは、"image_e40e92.png"というファイルを入力として使用しますが、コマンドライン引数で別のファイルを指定することもできます。変換された画像は"default_icon_16x16.ico"という名前で保存されます。
使用方法:
python main.py -i <入力画像のパス> -f <出力形式> -o <出力ファイル名のベース>
例:
python main.py -i my_image.jpg -f ico -o my_icon
この例では、my_image.jpgを16x16ピクセルのICO形式に変換し、my_icon.icoとして保存します。
"""

import argparse
from pathlib import Path
from PIL import Image

OUTPUT_SIZE = {
    'png': (24, 24),
    'ico': (16, 16)
}
INTERPOLATION_METHOD = Image.Resampling.LANCZOS  # 高品質なリサイズのための補間方法
BLACK_THRESHOLD = 20  # この値以下のRGBを黒背景として透明化

def make_black_background_transparent(img, threshold=BLACK_THRESHOLD):
    rgba = img.convert("RGBA")
    pixels = []

    for r, g, b, a in rgba.getdata():
        if r <= threshold and g <= threshold and b <= threshold:
            pixels.append((r, g, b, 0))
        else:
            pixels.append((r, g, b, a))

    rgba.putdata(pixels)
    return rgba


def save_as_svg(img, output_path):
    rgba = img.convert("RGBA")
    width, height = rgba.size
    rects = []

    for y in range(height):
        for x in range(width):
            r, g, b, a = rgba.getpixel((x, y))
            if a == 0:
                continue
            opacity = a / 255
            rects.append(
                f'<rect x="{x}" y="{y}" width="1" height="1" fill="rgb({r},{g},{b})" fill-opacity="{opacity:.6f}" />'
            )

    svg_content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" shape-rendering="crispEdges">\n'
        + "\n".join(rects)
        + "\n</svg>\n"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"SVG変換が完了しました: {output_path}")


def prepare_image_for_size(img, size):
    resized_img = img.resize(size, INTERPOLATION_METHOD)
    return make_black_background_transparent(resized_img)


def resize_icon(input_path, output_stem, formats):
    # 画像を開く
    with Image.open(input_path) as img:
        if "png" in formats:
            png_img = prepare_image_for_size(img, OUTPUT_SIZE['png'])
            png_output = f"{output_stem}.png"
            png_img.save(png_output, format="PNG")
            print(f"PNG変換が完了しました: {png_output}")

        if "svg" in formats:
            svg_img = prepare_image_for_size(img, OUTPUT_SIZE['png'])
            svg_output = f"{output_stem}.svg"
            save_as_svg(svg_img, svg_output)

        if "ico" in formats:
            ico_img = prepare_image_for_size(img, OUTPUT_SIZE['ico'])
            ico_output = f"{output_stem}.ico"
            ico_img.save(ico_output, format="ICO", sizes=[OUTPUT_SIZE['ico']])
            print(f"ICO変換が完了しました: {ico_output}")

def parse_args():
    parser = argparse.ArgumentParser(description=f"画像を{OUTPUT_SIZE['png'][0]}x{OUTPUT_SIZE['png'][1]}のPNG/SVG/ICOに変換します")
    parser.add_argument(
        "-i",
        "--input",
        default="image_e40e92.png",
        help="入力画像のパス（未指定時: image_e40e92.png）",
    )
    parser.add_argument(
        "-f",
        "--format",
        nargs="+",
        choices=["png", "svg", "ico"],
        default=["svg"],
        help="出力形式（複数指定可） 例: -f png svg ico",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=f"default_icon_{OUTPUT_SIZE['png'][0]}x{OUTPUT_SIZE['png'][1]}",
        help="出力ファイル名のベース（拡張子なし）",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    input_file = args.input  # 元の画像パス（jpegでも読み込めます）
    output_file_stem = str(Path(args.output).with_suffix(""))

    resize_icon(input_file, output_file_stem, args.format)
