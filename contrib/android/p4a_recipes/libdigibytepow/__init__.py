import os
import shlex
from pathlib import Path

from pythonforandroid.recipe import Recipe
from pythonforandroid.util import current_directory
from sh import cp, mkdir, Command


class DigiBytePowRecipe(Recipe):
    version = "c5449487c59e09171847255213d2d7b90122207b"
    url = "https://github.com/DigiByte-Core/digibyte/archive/{version}.tar.gz"
    depends = []
    built_libraries = {"libdigibytepow.so": ".libs"}
    need_stl_shared = True

    def build_arch(self, arch):
        build_dir = self.get_build_dir(arch.arch)
        recipe_dir = self.get_recipe_dir()
        env = self.get_recipe_env(arch)
        cxx_parts = shlex.split(env["CXX"])
        cxx = Command(cxx_parts[0])
        source_dir = os.path.join(build_dir, "src")
        output_dir = os.path.join(build_dir, ".libs")
        os.makedirs(output_dir, exist_ok=True)
        # Reuse the canonical adapter from the project root so the Android
        # recipe cannot silently drift from the desktop/Windows build.
        contrib_dir = Path(recipe_dir).parents[2]
        cp(str(contrib_dir / "digibyte_pow_adapter.cpp"), build_dir)

        sources = [
            "crypto/sha256.cpp", "crypto/hmac_sha256.cpp", "crypto/scrypt.cpp",
            "crypto/groestl.cpp", "crypto/skein.cpp", "crypto/luffa.cpp",
            "crypto/cubehash.cpp", "crypto/shavite.cpp", "crypto/simd.cpp",
            "crypto/echo.cpp", "crypto/keccak.cpp",
            "crypto/KeccakP-800-reference.cpp", "crypto/odocrypt.cpp",
            "crypto/aes.cpp",
        ]
        with current_directory(build_dir):
            cxx(
                *cxx_parts[1:],
                "-shared", "-fPIC", "-O2", "-std=c++20", "-pthread",
                "-I" + source_dir, "-I" + os.path.join(source_dir, "crypto"),
                "digibyte_pow_adapter.cpp",
                *[os.path.join(source_dir, source) for source in sources],
                "-o", os.path.join(output_dir, "libdigibytepow.so"),
                _env=env,
            )


recipe = DigiBytePowRecipe()
