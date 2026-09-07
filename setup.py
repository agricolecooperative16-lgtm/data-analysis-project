from setuptools import setup, find_packages

setup(
    name="data-analysis-project",
    version="1.0.0",
    description="نظام تحليل المبيعات والعملاء - متكامل مع RFM والتنبؤ والتحليل الموسمي",
    author="agricolecooperative16-lgtm",
    packages=find_packages(),
    install_requires=[
        'pandas>=1.3.0',
        'numpy>=1.21.0',
        'matplotlib>=3.4.0',
        'seaborn>=0.11.0',
        'scikit-learn>=1.0.0',
        'statsmodels>=0.13.0',
        'plotly>=5.0.0',
        'streamlit>=1.0.0',
        'python-dotenv>=0.19.0',
        'openpyxl>=3.0.0'
    ],
    entry_points={
        'console_scripts': [
            'data-analysis=app:main',
        ],
    },
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)