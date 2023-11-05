from distutils.core import setup
import setup_translate

pkg = 'Extensions.AntiLogo'
setup(name='enigma2-plugin-extensions-antilogo',
       version='0.1',
       description='Prevent logo retention',
       packages=[pkg],
       package_dir={pkg: 'plugin'},
       package_data={pkg: ['locale/*/LC_MESSAGES/*.mo']},
       cmdclass=setup_translate.cmdclass, # for translation
      )
