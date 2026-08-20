import subprocess


def main() -> None:
    subprocess.run(
        [
            "fastapi",
            "dev",
            "src/shigavox/main.py",
        ],
        check=True,
    )