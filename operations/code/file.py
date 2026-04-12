# Python reading files 

txt_data = "I like Pokemon"
file_path = 'operations/code/output.txt'

with open(file_path, "w") as file:
    file.write(txt_data)
    print("Output 'file_path' was created!")