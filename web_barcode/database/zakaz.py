from zak import data
x = 0
for d in data:
    if d['supplierArticle'] == "N271-1" and d["oblastOkrugName"] == "Центральный федеральный округ":
        x += 1

print(x)