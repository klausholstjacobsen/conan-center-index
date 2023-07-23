from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, cmake_layout
from conan.tools.files import copy, get, load, replace_in_file, rmdir, save, rm, check_sha256
from conan.errors import ConanException
import os
from io import StringIO

class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def test(self):
        if not can_run(self):
            return

        output = StringIO()
        self.run(f"tar --version", output, env="conanrun")


        input_file_sha256 = "6a7ef9d581b577bbe8415d69ccc2549287eb99b5d856a213df742f8b89986a6a"
        input_file = "input.txt"
        if os.path.exists(input_file):
            rm(self, input_file, ".")

        save(self, input_file, "Klaus is king!")

        #Ensure output test file does not exist
        output_file = input_file + ".tgz"
        if os.path.exists(output_file):
            rm(self, output_file, ".")

        #Zip the input file
        self.run(f"tar czvf {output_file} {input_file}", env="conanrun")
        if not os.path.exists(f"{output_file}"):
            raise ConanException(f"{output_file} does not exist")

        rm(self, input_file, ".")

        #Unzip the input file
        self.run(f"tar xzvf {output_file}", env="conanrun")
        if not os.path.exists(f"{input_file}"):
            raise ConanException(f"{input_file} does exist")

        #Compare checksum of unzipped file with expected value
        check_sha256(self, input_file, input_file_sha256)