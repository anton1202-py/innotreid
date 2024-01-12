import os

from msoffice2pdf import convert

filename = "web_barcode/fbs_mode/data_for_barcodes/pivot_excel/На производство ИП 10.01.2024 22-10-45.xlsx"
full_path = os.path.abspath(filename)
folder_path = os.path.dirname(os.path.abspath(full_path))
new_pdf_name = f"{folder_path}/new.pdf"
print(folder_path)

output = convert(source=full_path, output_dir=folder_path, soft=0)
