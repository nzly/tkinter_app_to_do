from pathlib import Path

from fpdf.enums import XPos, YPos
from fpdf import FPDF

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

def generate_pdf_with_screenshots(txt_path: Path, image_path_list: list[Path], pdf_path: Path):
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
            
    pdf.ln(10) # Add some spacing before the screenshot
    
    # 2. Add section title for the image
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "System UI Screenshot:", 0, 1)
    pdf.ln(3)
    
    # 3. Embed the screenshot
    # w=160 sets the width to 160mm (leaving margins on standard A4/Letter width)
    # Height scales automatically to preserve aspect ratio
    for image_path in image_path_list:
        pdf.image(image_path, w=160)

    #pdf.ln(10) # Add some spacing before the screenshot

    # 4. Save output
    pdf.output(pdf_path)
    print(f"Successfully generated PDF with image at {pdf_path}")

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    app_guide_file = project_root / "app_guide.txt"
    product_guide_file = project_root / "product_guide.txt"
    application_main_win_screenshot = project_root / "resources" / "app_screenshots" / "App_main" / "01_App_main_window.png"
    events_to_tasks_to_attachment_screenshot = project_root / "resources" / "app_screenshots" / "App_main" / "06_Events_to_tasks_to_attachments.png"
    output_app_guide_pdf = project_root / "app_guide.pdf"
    output_product_guide_pdf = project_root / "product_guide.pdf"
    generate_pdf_with_screenshots(app_guide_file, [application_main_win_screenshot, events_to_tasks_to_attachment_screenshot], output_app_guide_pdf)
    generate_pdf_with_screenshots(product_guide_file, [application_main_win_screenshot, events_to_tasks_to_attachment_screenshot], output_product_guide_pdf)
