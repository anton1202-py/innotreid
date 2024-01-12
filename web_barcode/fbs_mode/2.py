import os

from msoffice2pdf import convert
from spire.xls import *
from spire.xls.common import *

filename = "data_for_barcodes/pivot_excel/file.xlsx"
full_path = os.path.abspath(filename)
print(full_path)
folder_path = os.path.dirname(os.path.abspath(full_path))
new_pdf_name = f"{folder_path}/new.pdf"
print(folder_path)


output = convert(source=full_path, output_dir=folder_path, soft=0)

print(output)
