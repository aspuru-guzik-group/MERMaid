from setuptools import setup, find_packages

setup(
    name="visualheist",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pdf2image",
        "Pillow",
        "transformers",
        "safetensors",
        "torch", 
        "huggingface_hub"
    ],
    entry_points={
        "console_scripts": [
            "visualheist=scripts.run_visualheist:main"
        ]
    },
)
