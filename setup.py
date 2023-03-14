from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()
setup(
   name='StateSpace',
   version='0.0.1',
   description='Package of functions to calculate gradient correlations for task battery maps.',
   author='Bronte Mckeown & Will Strawson',
   author_email='bronte.mckeown@gmail.com',
   packages=find_packages(include=['StateSpace']),
   install_requires=required,
   include_package_data=True,
   package_data={'StateSpace': [
    'data/gradients/*nii.gz',
    'data/masks/*.nii.gz',
    'data/realTaskNiftis/*.nii.gz',
    'data/lesionedOutputs/*/*.nii.gz'
    ]
    }
)
