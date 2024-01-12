import os

import uno
from com.sun.star.beans import PropertyValue

# from com.sun.star.beans import PropertyValue


# запускаем LibreOffice в режиме без графического интерфейса
local_context = uno.getComponentContext()
resolver = local_context.ServiceManager.createInstanceWithContext(
    "com.sun.star.bridge.UnoUrlResolver", local_context)
ctx = resolver.resolve(
    "uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
smgr = ctx.ServiceManager
desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)

input_file = os.path.abspath(
    "web_barcode/fbs_mode/data_for_barcodes/pivot_excel/На производство ИП 10.01.2024 22-10-45.xlsx")
folder_path = os.path.dirname(os.path.abspath(input_file))
doc = desktop.loadComponentFromURL(
    f"file://{input_file}", "_blank", 0, ())

output_file = f"{folder_path}/new.pdf"
pdf_export = "writer_pdf_Export"
pdf_filter_data = (
    PropertyValue("FilterName", 0, pdf_export, 0),
    PropertyValue("Overwrite", 0, True, 0),
)
doc.storeToURL(f"file://{output_file}", pdf_filter_data)
doc.close(True)
