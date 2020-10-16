from . import csv
with open("U.csv") as csvfile:
    reader = csv.DictReader(csvfile, delimiter="\t")
    print(reader.fieldnames)
    print(reader.reader)
