from setuptools import setup

with open("README.md", encoding="utf-8") as f:
    readme = f.read()

setup(
    name="chessGPT",
    version="0.1",
    description="Play chess against ChatGPT.",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Maximilian Stollmayer",
    author_email="max.stollmayer@gmail.com",
    url="https://github.com/maxstolly/chessGPT",
    license="MIT License",
    py_modules=["main"],
    python_requires=">=3.9.0",
    install_requires=["chess==1.9.4", "click==8.1.3", "openai==0.27.2", "rich==13.3.2"],
    entry_points="""
        [console_scripts]
        chess=main:main
    """,
)
