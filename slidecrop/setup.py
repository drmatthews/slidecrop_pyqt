from setuptools import setup

setup(name='slidecrop_pyqt',
      version='0.1',
      description='Python app for cropping slide scanner images',
      url='http://github.com/drmatthews/slidecrop_pyqt',
      author='Dan Matthews',
      author_email='dr.dan.matthews@gmail.com',
      license='MIT',
      packages=['slidecrop_pyqt'],
      install_requires=[
        'h5py',
        'numpy',
        'PyQt5',
        'PyQt5-sip',
        'pyqtgraph',
        'scipy',        
        'scikit-image',
        'tifffile'
      ],      
      zip_safe=False)