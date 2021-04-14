from distutils.core import setup

pkg = 'Extensions.AntiLogo'
setup(name='enigma2-plugin-extensions-antilogo',
       version='0.1',
       description='Prevent logo retention',
       packages=[pkg],
       package_dir={pkg: 'plugin'}
      )
