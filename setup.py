import setuptools

setuptools.setup(
    name='wellannotator',
    version='0.0.1',
    description='Tools to classify good and bad wells',
    url='https://github.com/Tierpsy/WellAnnotator',
    author='Luigi Feriani',
    author_email='l.feriani@lms.mrc.ac.uk',
    license='MIT',
    packages=setuptools.find_packages(),
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "well_annotator="
            + "well_annotator.WellAnnotator:"
            + "launch_app",
            "read_working_dir="
            + "well_annotator.helper:"
            + "read_working_dir",
            "rebase_annotations="
            + "well_annotator.helper:"
            + "rebase_annotations",
        ]
    },
    )
