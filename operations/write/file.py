# Python reading files 
# w - it is for writing a file
# x - writes a file if it already exists.
# a - for appending a data

import json
import csv


txt_data = "I like Pokemon"
file_path = 'operations/code/pron.csv'

students = ["Sid", "Pran", "Kir"]

proverbs = {
    "sr": 1,
    "name": "pokemon",
    "job": "cook"
}

employees =[["Name", "Age", "Job"], ["Spongebob", 30, "Cook"]]
try:
    # with open(file_path, "a") as file:
    #     file.write("\n" + txt_data)
    #     for student in students:
    #         file.write("\n" + student)
    #     file.write("\n" + students[0])
    #     print("Output 'file_path' was created!")
    # with open(file_path, "a") as file:
    #     json.dump(proverbs, file, indent=4)
    #     print("Output 'file_path' was created!")
    with open(file_path, "x", newline="") as file:
        writer = csv.writer(file)
        for row in employees:
            writer.writerow(row)
        print("Output 'file_path' was created!")

except FileExistsError:
    print("That file already exists")