# Third-party components

The game code, character art, pet art, scenery and synthesized audio were created for this project. The MIT game license does not replace the licenses of its runtime dependencies.

- **Python 3.12**: Python Software Foundation license. Python sources and licensing: https://www.python.org/downloads/source/ .
- **pygame-ce 2.5.8**: GNU LGPL 2.1. The included dynamic extensions and SDL libraries can be replaced or the editable game can be rebuilt with another compatible installation. pygame-ce source: https://github.com/pygame-community/pygame-ce/tree/2.5.8 .
- **SDL2, SDL2_image, SDL2_mixer, SDL2_ttf**: zlib licenses; their bundled optional codec dependencies retain their individual licenses. Upstream source and notices: https://github.com/libsdl-org .
- **DejaVu fonts**: Bitstream Vera license and public-domain DejaVu changes. This project uses Latin-subset fonts. The complete installed font copyright and license notice is in `assets/FONT-LICENSE.txt`.
- **PyInstaller**: GPL 2.0 or later with the special bootloader distribution exception. The corresponding notice is copied to packaged `licenses/` from the installed PyInstaller distribution. Sources: https://github.com/pyinstaller/pyinstaller .
- Bundled media/text dependencies include FreeType, HarfBuzz, libpng, libjpeg-turbo, libtiff, libwebp, zlib, libogg/libvorbis, FLAC, mpg123, Opus, libsndfile, libxmp, WavPack, FluidSynth and GLib where present in pygame-ce's manylinux wheel. Their upstream licenses apply. The application includes the corresponding GNU LGPL and commonly used system license texts in `licenses/`. Exact library filenames are retained in `_internal/pygame_ce.libs/`.

pygame-ce's source includes its manylinux dependency build scripts and attribution information. Dependency libraries are loaded dynamically, and editable game source is included in the portable download to make modification and rebuilding possible. System glibc, libgcc, libstdc++ and desktop libraries are used from the Linux installation rather than relicensed by this game.
