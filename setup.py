import setuptools

setuptools.setup(name='slidecrop_pyqt',
      version='0.1',
      description='Python app for cropping slide scanner images',
      url='http://github.com/drmatthews/slidecrop_pyqt',
      author='Dan Matthews',
      author_email='dr.dan.matthews@gmail.com',
      license='MIT',
      packages=setuptools.find_packages(exclude=['docs', 'test_data']),
      install_requires=[
        'pyqt5',
        'pyqtgraph',        
        'h5py',
        'numpy',
        'scipy',
        'matplotlib',        
        'scikit-image',
        'tifffile'
      ],      
      zip_safe=False)