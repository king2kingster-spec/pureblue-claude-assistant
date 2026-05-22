from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

setup(
	name="claude_assistant",
	version="1.0.0",
	description="Claude AI Assistant for ERPNext",
	author="PureBlue",
	author_email="ahad@pureblue.co.in",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires,
)
