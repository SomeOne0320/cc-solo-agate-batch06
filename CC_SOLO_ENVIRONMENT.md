# Reproducible local environment

This snapshot is agate1.14.2 with Linux ARM64/Python3.11 in the standard target image. Runtime and local test dependencies are locked in requirements-cc-solo.txt. No remote service or user credentials are needed.

```bash
curl -fsSL https://bootstrap.pypa.io/get-pip.py -o /tmp/agate-get-pip.py
python3 /tmp/agate-get-pip.py --user --break-system-packages pip==24.3.1
python3 -m pip install --user --break-system-packages -r requirements-cc-solo.txt
python3 -m pip install --user --break-system-packages --no-build-isolation --no-deps -e .
curl -fsSL https://deb.debian.org/debian/pool/main/g/glibc/locales-all_2.36-9+deb12u14_arm64.deb -o /tmp/agate-locales.deb
mkdir -p /tmp/agate-locales
dpkg-deb -x /tmp/agate-locales.deb /tmp/agate-locales
export LOCPATH=/tmp/agate-locales/usr/lib/locale
python3 -m pytest -q tests/test_table/test_join.py tests/test_table/test_homogenize.py
```

The test package sets en_US.UTF-8 at import time. Extracting the matching official Debian locale package locally supplies this data without root access or changing system settings. Optional PyICU-dependent tests are outside this minimal dependency set. Run tests for changed components as well. Preserve commands and actual results, distinguishing collection/environment errors from implementation failures.
