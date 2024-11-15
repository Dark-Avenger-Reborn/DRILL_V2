import subprocess

# Define your Docker command
command = [
    "docker", "run",
    "--volume", "$(pwd):/src/",
    "batonogov/pyinstaller-linux:latest",
    "pyinstaller", "--onefile", "your-script.py"
]

# Run the command
subprocess.run(command, shell=True)