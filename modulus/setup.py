from setuptools import setup, find_packages

setup(
    name="modulus",
    version="1.1.0",
    description="Modular Machine Learning Pipeline with Clean Architecture",
    author="Your Team / Name",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scikit-learn>=1.3.0",
        "pyyaml>=6.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "mypy>=1.5.0",
        ],
        "xgboost": ["xgboost>=1.7.0"],
    },
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "modulus=modulus.cli:main",
        ],
    },
)
