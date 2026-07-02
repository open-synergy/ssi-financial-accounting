.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==============================
SSI PDF Image Statement Import
==============================

Import bank statements from scanned/image-only PDF files (e.g. photocopied or
scanned passbook pages) using local Tesseract OCR. Each bank passbook layout
can have its own mapping record with custom extraction logic written in a
restricted Python environment (safe_eval), applied to the OCR-extracted text.

This module requires the system binaries ``tesseract-ocr`` and
``poppler-utils`` to be installed on the Odoo image, in addition to the
Python packages ``pytesseract``, ``pdf2image``, ``opencv-python-headless``
and ``numpy``.

Each mapping record can optionally enable image preprocessing (grayscale,
auto contrast, binarization, deskew, upscale) applied to every rendered page
before OCR. This is disabled by default and is intended for low-quality
scans (e.g. photocopied passbooks) where raw OCR output is too noisy for
``parser_code`` to parse.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/open-synergy/ssi-financial-accounting/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.


Credits
=======

Contributors
------------

* Andhitia Rama <andhitia.r@gmail.com>

Maintainer
----------

.. image:: https://simetri-sinergi.id/logo.png
   :alt: PT. Simetri Sinergi Indonesia
   :target: https://simetri-sinergi.id

This module is maintained by the PT. Simetri Sinergi Indonesia.
