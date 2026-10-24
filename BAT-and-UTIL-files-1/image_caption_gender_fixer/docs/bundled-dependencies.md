# Bundle, provenance, and notices

The runtime is a directly usable **Windows CPython 3.10 x64** package tree,
selected relative to the launcher. Python itself is supplied by the machine.
No venv with stale absolute launcher paths is renamed or blindly relocated.
Active rebuilt trees are versioned directories under `environment`, verified in
an isolated child process, marked ready, then selected through an atomic owned
metadata record. Incomplete trees are never selected. Existing trees remain.

| Component | Delivered version | Location / notice |
| --- | --- | --- |
| Pillow | 10.3.0 | packages/PIL; pillow dist-info/LICENSE |
| NumPy | 1.26.4 | packages/numpy + numpy.libs; numpy dist-info/LICENSE.txt |
| OpenCV headless | 4.10.0.84 (cv2 4.10.0) | packages/cv2; LICENSE.txt and LICENSE-3RD-PARTY.txt |
| regex | 2024.4.16 | packages/regex; dist-info/LICENSE.txt |
| tqdm | 4.66.2 | packages/tqdm; dist-info/LICENCE |
| pytest | 7.4.0 | packages/pytest + _pytest; dist-info/LICENSE |
| Test/runtime helpers | pinned in requirements.lock | Respective dist-info notices |
| Claire progress | unchanged bundled shared module | packages/clairecjs_utils/claire_progressbar.py |
| Tesseract | 5.5.3.20260724 | tools/tesseract; doc/LICENSE |
| English fast data | commit 923915d4ced2a7235221788285785a29c4a42d4a | tessdata/eng.traineddata; docs/licenses/tessdata-fast-LICENSE.txt |
| Chafa | 1.18.2 | tools/chafa; docs/licenses/chafa-* notices |
| ImageMagick | 7.1.1-10 Q16-HDRI | tools/magick; License.txt, NOTICE.txt, www/license.html |
| 7-Zip | 23.01 | tools/7zip; License.txt |

The version lock is `environment/requirements.lock`. SHA-256/size/platform
records are in `environment/manifest.json`; download origins and original payload
hashes are in `environment/metadata/provenance.json`. Tests and `doctor` verify
the selected private files, including native libraries. Original wheel downloads
are optional once installed and are safely recyclable. The complete offline
repair archive, `environment/wheels/runtime-bundle.zip`, is intentionally kept.

NumPy/OpenCV wheels were downloaded from the pinned PyPI versions after explicit
user approval and matched published SHA-256 values. Pillow, regex, tqdm, pytest,
helpers, native ImageMagick/Chafa/7-Zip, and the shared progress module were copied
from existing local installations and verified. The canonical shared utility
and its mirrors were not modified.

Tesseract/English downloads were explicitly approved. A Chocolatey system attempt
installed no packages because administrator access was unavailable; the approved
installer payload was instead hash-verified and privately extracted with 7-Zip.
No downloaded arbitrary installer was executed. Normal runtime prefers bundled
tools; a missing dependency requires a new explicit installation/repair decision.
The plan distinguishes private extraction from any trusted system-manager fallback.

## Reproduce or repair without manual pip

The shipped offline archive is the reproducible Python-package payload. Repair
verifies the archive hash and every member against the manifest, extracts to a
new final directory, imports all required packages in isolation, and publishes
readiness only afterward. A real test performs this rebuild and then moves the
rebuilt tool directory and verifies private NumPy/OpenCV operation again.

For developer rebuilding, `environment/build_bundle.py` contains explicit actions
for copying verified existing inputs and approved pinned wheel/native preparation;
`environment/package_offline.py` packages the private tree and CRC-checks it.
Generate the manifest last. These build actions are not end-user setup commands.
Do not run developer-time downloads without the same informed dependency consent.
The existing-input builder deliberately preserves differing existing bundle files;
the shipped lock/manifest/archive is the authoritative reproducible payload.

Native payloads are distributed as the unmodified verified local files described
in the provenance record. Preserve their notices with them. Reproducing a native
payload from upstream requires its matching source/distribution and consent;
normal use requires neither compilation nor downloading.

## Licensing references

[Chafa upstream](https://github.com/hpjansson/chafa) identifies its library and
frontend as LGPLv3-or-later. Its authors and standard LGPL/GPL notice texts are
included under docs/licenses. The pinned English model predates addition of its
repository LICENSE file; the current upstream
[Apache-2.0 notice](https://github.com/tesseract-ocr/tessdata_fast/blob/main/LICENSE)
is included with that provenance recorded. These notices were fetched as text;
no additional executable or model was installed for documentation.

Python package notices include transitive native-library notices such as OpenBLAS
and OpenCV's bundled third-party components. ImageMagick's copied distribution
also includes optional native components; its own notices remain in place.
Consult the component notices/source distributions before redistributing altered
native binaries. This local build does not claim to audit the licensing of every
possible third-party binary modification or a future redistribution arrangement.
