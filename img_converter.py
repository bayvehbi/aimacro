import base64
import os

input_dir = "storage/icons"
output_file = "images_base64_output.py"

images_base64 = {}

for filename in os.listdir(input_dir):
    if filename.lower().endswith(".png"):
        filepath = os.path.join(input_dir, filename)
        with open(filepath, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            images_base64[filename] = encoded

with open(output_file, "w", encoding="utf-8") as out:
    out.write("images_base64 = {\n")
    for fname, b64 in images_base64.items():
        out.write(f'    "{fname}": """{b64}""",\n')
    out.write("}\n")

print(f"All PNG files converted ('{output_file}').")
