from conan import ConanFile
from conan.tools.files import get, copy, rmdir
from conan.tools.gnu import Autotools, AutotoolsDeps, AutotoolsToolchain, PkgConfigDeps
from conan.errors import ConanInvalidConfiguration
from contextlib import contextmanager
from conan.tools.build import cross_building
from conan.tools.env import VirtualRunEnv, VirtualBuildEnv
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rm, rmdir
import os

required_conan_version = ">=1.33.0"


class IslConan(ConanFile):
  name = "isl"
  description = "isl is a library for manipulating sets and relations of integer points bounded by linear constraints."
  topics = ("isl", "integer", "set", "library")
  license = "MIT"
  homepage = "https://libisl.sourceforge.io"
  url = "https://github.com/conan-io/conan-center-index"
  settings = "os", "arch", "compiler", "build_type"
  options = {
    "shared": [True, False],
    "fPIC": [True, False],
    "with_int": ["gmp", "imath", "imath-32"],
  }
  default_options = {
    "shared": False,
    "fPIC": True,
    "with_int": "gmp",
  }

  def export_sources(self):
      export_conandata_patches(self)

  def config_options(self):
    if self.settings.os == "Windows":
      del self.options.fPIC

  def configure(self):
    if self.options.shared:
      del self.options.fPIC
    del self.settings.compiler.libcxx
    del self.settings.compiler.cppstd

  def validate(self):
    if self.settings.os == "Windows" and self.options.shared:
      raise ConanInvalidConfiguration("Cannot build shared isl library on Windows (due to libtool refusing to link to static/import libraries)")
    if self.settings.os == "Macos" and self.settings.arch == "armv8":
      raise ConanInvalidConfiguration("Apple M1 is not yet supported. Contributions are welcome")
    #if self.options.with_int != "gmp":
      # FIXME: missing imath recipe
      #raise ConanInvalidConfiguration("imath is not (yet) available on cci")
    if self.settings.compiler == "msvc" and tools.Version(self.settings.compiler.version) < 16 and self.settings.compiler.runtime == "MDd":
      # gmp.lib(bdiv_dbm1c.obj) : fatal error LNK1318: Unexpected PDB error; OK (0)
      raise ConanInvalidConfiguration("isl fails to link with this version of visual studio and MDd runtime")

  def requirements(self):
    if self.options.with_int == "gmp":
      self.requires("gmp/6.3.0")
    if self.options.with_int == "imath":
      self.requires("imath/3.1.9")

  def build_requirements(self):
    pass

  def generate(self):
    pc = PkgConfigDeps(self)
    pc.generate()
    #env = VirtualBuildEnv(self)
    #env.generate()

    yes_no = lambda v: "yes" if v else "no"
    rootpath_no = lambda v, req: self.dependencies[req].package_folder if v else "no"
    gmp_dir = self.dependencies["gmp"].package_folder

    tc = AutotoolsToolchain(self)
    tc.configure_args.extend([
      f"--with-int={self.options.with_int}",
      #f"--with-gmp-builddir={gmp_dir}",
      "--enable-portable-binary",
      "--enable-shared={}".format(yes_no(self.options.shared)),
      "--enable-static={}".format(yes_no(not self.options.shared)),
    ])
    tc.generate()

    deps = AutotoolsDeps(self)
    deps.generate()

  def source(self):
    get(self, **self.conan_data["sources"][self.version], strip_root=True, filename=f"isl-{self.version}.tar.gz")

  def build(self):
    apply_conandata_patches(self)

    autotools = Autotools(self)
    autotools.configure()
    autotools.make()
      

  def package(self):
    autotools = Autotools(self)
    autotools.install()
    copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
    

    os.unlink(os.path.join(os.path.join(self.package_folder, "lib", "libisl.la")))
    rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

  def package_info(self):
    #self.cpp_info.names["pkg_config"] = "isl"
    self.cpp_info.libs = ["isl"]
