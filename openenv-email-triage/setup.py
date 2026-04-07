from setuptools import setup, find_packages

setup(
    name="openenv-email-triage",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["pydantic>=2.0", "openai>=1.0"],
    python_requires=">=3.10",
)
