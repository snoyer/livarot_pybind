from glob import glob
import os
import sys
import sysconfig
import shutil
import subprocess
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import platform



class cmake_build_ext(build_ext):
    # adapted from https://martinopilia.com/posts/2018/09/15/building-python-extension.html
    def build_extensions(self):
        
        # Ensure that CMake is present and working
        try:
            _ = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError('Cannot find CMake executable')

        for _ in self.extensions:

            extdir = os.path.abspath(os.path.dirname(__file__))

            if not os.path.exists(self.build_temp):
                os.makedirs(self.build_temp)
            env = os.environ
            possible_gcc_paths = ['/usr/bin/gcc-8', '/c/msys64/mingw64/bin/gcc', 'C://msys64/mingw64/bin/gcc.exe']
            for possible_path in possible_gcc_paths:
                if os.path.exists(possible_path):
                    env['CC'] = possible_path
                    break
            possible_gpp_paths = ['/usr/bin/g++-8', '/c/msys64/mingw64/bin/g++', 'C://msys64/mingw64/bin/g++.exe']
            for possible_path in possible_gpp_paths:
                if os.path.exists(possible_path):
                    env['CXX'] = possible_path
                    break
            # Config
            extra_config_args = []
            # LDLIBRARY libpython3.9.so
            # BINLIBDEST /usr/lib/x86_64-linux-gnu/python3.9
            # LIBDIR /usr/lib/x86_64-linux-gnu 
            extra_config_args.append(f"-DPYTHON_LIBRARY={sysconfig.get_config_var('LIBDIR')}/{sysconfig.get_config_var('LDLIBRARY')}")
            extra_config_args.append(f"-DPYTHON_INCLUDE_DIRS={sysconfig.get_config_var('INCLUDEPY')}") # this might need to be the subdir
            extra_config_args.append(f"-DPYTHON_EXECUTABLE={sys.executable}")
            extra_config_args.append("-DCMAKE_POSITION_INDEPENDENT_CODE=ON")
            extra_config_args.append("-DCMAKE_CXX_COMPILER_LAUNCHER=ccache")
            if env.get('CC'):
                extra_config_args.append(f"-DCMAKE_C_COMPILER={env['CC']}")
            if env.get('CXX'):
                extra_config_args.append(f"-DCMAKE_CXX_COMPILER={env['CXX']}")
            if os.path.exists('/usr/include/boost69'):
                extra_config_args.append(f"-DBOOST_INCLUDEDIR=/usr/include/boost169")
            if os.path.exists('/usr/lib64/boost169/'):
                extra_config_args.append(f"-DBOOST_LIBRARYDIR=/usr/lib64/boost169")
            if platform.system() == "Windows":
                extra_config_args += ["-G","MinGW Makefiles"]
            #    extra_config_args += ["-G","Ninja"]
            config_vars = ['cmake', "-S", extdir]+extra_config_args
            try:
                subprocess.check_call(config_vars, cwd=self.build_temp, env=env)
            except Exception as e:
                print(f"failed to run command {' '.join(config_vars)}")
                raise e
            # Build
            if platform.system() == 'Windows':
                subprocess.check_call(['cmake', '--build', '.', '--config', 'Release'],
                            cwd=self.build_temp)
            else:
                subprocess.check_call(['cmake', '--build', '.'],
                            cwd=self.build_temp)
        # copy all the built files into the lib dir. Not sure why this is needed; it feels like setuptools should 
        # copy the built files into the bdist by default
        lib_dir = os.path.join(self.build_lib, "pylivarot")
        pylivarot_sos = glob(os.path.join(self.build_temp, f"*{sys.version_info.major}{sys.version_info.minor}*.so"))
        if len(pylivarot_sos) == 0:
            raise FileNotFoundError(f"could not find *{sys.version_info.major}{sys.version_info.minor}*.so in {os.listdir(self.build_temp)}")
        for _file in pylivarot_sos:
            print("copying ", _file," to ", os.path.join(lib_dir, os.path.basename(_file)))
            shutil.move(_file, os.path.join(lib_dir, os.path.basename(_file)))
        

setup(
      packages=['pylivarot'],
      ext_modules = [Extension("pylivarot", ["pybind11"])],
      cmdclass = {'build_ext': cmake_build_ext}
)
