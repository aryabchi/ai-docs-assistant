from setuptools import setup, find_packages

setup(
    name="ai-docs-assistant",
    version="0.1.0",
    author="",
    author_email="email@example.com",
    description="AI agentic mini-project with RAG",
    # Automatically find packages in your project
    packages=find_packages(exclude=["tests*"]),
    # Metadata for PyPI
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    extras_require={
        "test": ["pytest", "pytest-cov"],
    },
)
