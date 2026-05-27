from setuptools import setup, find_packages

setup(
    name="claude_assistant",
    version="1.0.1",
    description="Claude AI Assistant for ERPNext - PureBlue",
    author="PureBlue",
    author_email="ahad@pureblue.co.in",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=["requests"],
)
