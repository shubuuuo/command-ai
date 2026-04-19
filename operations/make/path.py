from pathlib import Path

# 1. Building a cross-platform path
# Notice we don't use slashes here; we let Path() handle it
my_path = Path('projects', 'python_scripts', 'data.txt')

print(f"Path object: {my_path}")
print(f"Path as a string: {str(my_path)}")

# 2. Joining paths using the / operator (The modern way)
home_dir = Path.home()
target_file = home_dir / 'Documents' / 'example.txt'

print(f"My Home Directory: {home_dir}")
print(f"Target file path: {target_file}")