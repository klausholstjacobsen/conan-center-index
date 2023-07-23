from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.gnu import Autotools, AutotoolsToolchain, AutotoolsDeps, PkgConfigDeps
from conan.tools.files import collect_libs, copy, get, load, replace_in_file, rmdir, save, patch, export_conandata_patches
from conan.tools.layout import basic_layout
import os

required_conan_version = ">=1.60.0"


class TarConan(ConanFile):
    name = "tar"
    description = "GNU Tar provides the ability to create tar archives, as well as various other kinds of manipulation."
    topics = ("tar", "archive")
    license = "GPL-3-or-later"
    homepage = "https://www.gnu.org/software/tar/"
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "arch", "compiler", "build_type"

    _autotools = None

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def requirements(self):
        self.requires("bzip2/1.0.8")
        self.requires("lzip/1.21")
        self.requires("xz_utils/5.2.5")
        self.requires("zstd/1.5.2")

    def validate(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("This recipe does not support Windows builds of tar")  # FIXME: fails on MSVC and mingw-w64
        if not self.options["bzip2"].build_executable:
            raise ConanInvalidConfiguration("bzip2:build_executable must be enabled")

    def package_id(self):
        del self.info.settings.compiler

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        ad = AutotoolsDeps(self)
        ad.generate()

        tc = AutotoolsToolchain(self)
        if 'Neutrino' in self.settings.os:
            tc.extra_ldflags = ["-lsocket"]
        tc.generate()

    def _patch_sources(self):
        print("patching for {}-{}-{}".format(self.version, str(self.settings.os).lower(), self.settings.get_safe("os.version")))

        # general patches
        for p in self.conan_data["patches"].get(self.version, []):
            print(f"patching general files: {p['patch_file']}")
            patch(self, **p, base_path=self.source_folder)
        
        # os specific patches
        for p in self.conan_data["patches"].get("{}-{}".format(self.version, str(self.settings.os).lower()), []):
            print(f"patching os specific files: {p['patch_file']}")
            patch(self, **p, base_path=self.source_folder)

        # os version specific patches
        for p in self.conan_data["patches"].get("{}-{}-{}".format(self.version, str(self.settings.os).lower(), self.settings.get_safe("os.version")), []):
            print(f"patching os version specific: {p['patch_file']}")
            patch(self, **p, base_path=self.source_folder)

    def _configure_autotools(self):
        bzip2_exe = "bzip2"  # FIXME: get from bzip2 recipe
        lzip_exe = "lzip"  # FIXME: get from lzip recipe
        lzma_exe = "lzma"  # FIXME: get from xz_utils recipe
        xz_exe = "xz"  # FIXME: get from xz_utils recipe
        zstd_exe = "zstd"  # FIXME: get from xz_utils recipe
        args = [
            "--disable-acl",
            "--disable-nls",
            "--disable-rpath",
            # "--without-gzip",  # FIXME: this will use system gzip
            "--without-posix-acls",
            "--without-selinux",
            "--with-bzip2={}".format(bzip2_exe),
            "--with-lzip={}".format(lzip_exe),
            "--with-lzma={}".format(lzma_exe),
            # "--without-lzop",  # FIXME: this will use sytem lzop
            "--with-xz={}".format(xz_exe),
            "--with-zstd={}".format(zstd_exe),
        ]
        return args


    def build(self):
        self._patch_sources()

        if self.settings.compiler == "Visual Studio":
            tools.replace_in_file(os.path.join(self._source_subfolder, "gnu", "faccessat.c"),
                                  "_GL_INCLUDING_UNISTD_H", "_GL_INCLUDING_UNISTD_H_NOP")

        self._patch_sources()

        autotools = Autotools(self)
        autotools.configure(args=self._configure_args)
        autotools.make()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()

        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bin_path))
        self.env_info.PATH.append(bin_path)

        tar_bin = os.path.join(self.package_folder, "bin", "tar")
        self.user_info.tar = tar_bin
        self.env_info.TAR = tar_bin
