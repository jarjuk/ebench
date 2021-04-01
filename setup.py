import setuptools

import ebench.CMDS as CMDS


with open("VERSION", "r") as fh:
    version = fh.read().rstrip()

scripts =[ "tmp/apu.sh" ]
name="ebench"


print( "version", version, ", packages", setuptools.find_packages())
    
setuptools.setup(
    name=name, # Replace with your own username
    packages=setuptools.find_packages(),
    version=version,
    zip_safe= True,
    install_requires = [ "pyvisa-py", "absl-py",  ],
    author="jj",
    author_email="author@example.com",
    description="ebench - Misc tools to control electronic lab intrumens",
    long_description="",
    long_description_content_type="text/markdown",
    url="https://github.com/jarjuk/ebench",
    package_data={
        "ebench": ['../VERSION', '../RELEASES.md' ]
    },
    scripts=scripts,
    entry_points = {
        "console_scripts": [ f"{CMDS.CMD_RIGOL}=ebench.Rigol:main"
                             , f"{CMDS.CMD_UNIT}=ebench.Unit:main", ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)
