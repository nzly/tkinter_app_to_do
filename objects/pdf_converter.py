from pathlib import Path

from fpdf.enums import XPos, YPos
from fpdf import FPDF
from PIL import Image

IMAGE_WIDTH_MM = 160


# Map '01_App_main_window.png' to {1: 'App_main_window'} for every PNG in the folder.
def build_screenshot_dict(folder: Path) -> dict[int, str]:
    screenshots: dict[int, str] = {}
    for image_file in folder.glob("*.png"):
        number, _, name = image_file.stem.partition("_")
        if number.isdigit() and name:
            screenshots[int(number)] = name
    return dict(sorted(screenshots.items()))


# 'App_main_window' -> 'App Main Window'
def build_screenshot_title(name: str) -> str:
    return " ".join(word[:1].upper() + word[1:] for word in name.split("_") if word)

class PDFWithImages(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 14)
        self.cell(
            0,
            10,
            "EasyNotes App Guide",
            border=0,
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

def generate_pdf_with_screenshots(txt_path: Path, screenshot_sections: list[tuple[Path, dict[int, str]]], pdf_path: Path):
    pdf = PDFWithImages()
    pdf.add_page()
    
    pdf.set_font("helvetica", size=11)
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # 1. Add introductory text from file
    with open(txt_path, "r", encoding="utf-8") as file:
        for line in file:
            pdf.multi_cell(
                0,
                7,
                text=line.rstrip(),
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            
    pdf.ln(10)

    # 2. Add each screenshot (title first, then image) in numeric order
    for folder, screenshots in screenshot_sections:
        for key, value in screenshots.items():
            image_path = folder / f"{key:02d}_{value}.png"
            with Image.open(image_path) as image:
                image_height_mm = IMAGE_WIDTH_MM * image.height / image.width

            # Keep the title on the same page as its image.
            if pdf.get_y() + 8 + 3 + image_height_mm > pdf.page_break_trigger:
                pdf.add_page()

            pdf.set_font("helvetica", "B", 12)
            pdf.cell(0, 8, build_screenshot_title(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(3)
            pdf.image(image_path, w=IMAGE_WIDTH_MM)
            pdf.ln(10)

    # 3. Save output
    pdf.output(pdf_path)
    print(f"Successfully generated PDF with image at {pdf_path}")

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    app_guide_file = project_root / "app_guide.txt"
    product_guide_file = project_root / "product_guide.txt"
    screenshots_root = project_root / "resources" / "app_screenshots"
    App_main = build_screenshot_dict(screenshots_root / "App_main")
    EventFinda = build_screenshot_dict(screenshots_root / "EventFinda")
    User_login = build_screenshot_dict(screenshots_root / "User_login")
    screenshot_sections = [
        (screenshots_root / "User_login", User_login),
        (screenshots_root / "App_main", App_main),
        (screenshots_root / "EventFinda", EventFinda),
    ]
    output_app_guide_pdf = project_root / "app_guide.pdf"
    output_product_guide_pdf = project_root / "product_guide.pdf"
    generate_pdf_with_screenshots(app_guide_file, screenshot_sections, output_app_guide_pdf)
    generate_pdf_with_screenshots(product_guide_file, screenshot_sections, output_product_guide_pdf)
