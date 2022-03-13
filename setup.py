import setuptools

import ebench.CMDS as CMDS
import os

name="ebench"

with open(os.path.join(name, "VERSION"), "r") as fh:
    version = fh.read().rstrip()


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
    include_package_data=True,
    package_data={
        "ebench": ['VERSION', 'RELEASES.md', "ebMenu.yaml" ]
    },
    data_files=[
        ("", ['VERSION', 'RELEASES.md' ])
        ],
    #  scripts=[f"{CMDS.CMD_RIGOL}", f"{CMDS.CMD_UNIT}"],
    entry_points = {
        "console_scripts": [ f"{CMDS.CMD_RIGOL}=ebench.ebRigol_main:main"
                             , f"{CMDS.CMD_UNIT}=ebench.ebUnit_main:main"
                             , f"{CMDS.CMD_MENU}=ebench.ebMenu:main"
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)
