import base64
import os

# Get the project root directory (two levels up from this script)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))

input_dir = os.path.join(project_root, "storage", "icons")
output_file = os.path.join(project_root, "aimacro", "resources", "images_base64_output.py")

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
