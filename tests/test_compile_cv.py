from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

import compile_cv


class CompileCvCliTests(unittest.TestCase):
    def test_pdf_is_default(self) -> None:
        args = compile_cv.build_parser().parse_args([])
        self.assertEqual(args.output_format, "pdf")

    def test_docx_is_case_insensitive(self) -> None:
        args = compile_cv.build_parser().parse_args(["--format", "DOCX"])
        self.assertEqual(args.output_format, "docx")

    def test_docx_install_help_uses_repository_virtual_environment(self) -> None:
        self.assertIn("python3 -m venv .venv", compile_cv.DOCX_INSTALL_HELP)
        self.assertIn(".venv/bin/python -m pip", compile_cv.DOCX_INSTALL_HELP)
        self.assertIn(r".venv\Scripts\python.exe -m pip", compile_cv.DOCX_INSTALL_HELP)
        self.assertIn("do not use --break-system-packages", compile_cv.DOCX_INSTALL_HELP)

    def test_dispatches_pdf(self) -> None:
        source = Path("resume.tex")
        with patch.object(compile_cv, "compile_pdf", return_value=Path("resume.pdf")) as compiler:
            self.assertEqual(compile_cv.compile_cv(source), Path("resume.pdf"))
            compiler.assert_called_once_with(source)

    def test_dispatches_docx(self) -> None:
        source = Path("resume.tex")
        with patch.object(compile_cv, "compile_docx", return_value=Path("resume.docx")) as compiler:
            self.assertEqual(compile_cv.compile_cv(source, "docx"), Path("resume.docx"))
            compiler.assert_called_once_with(source)

    def test_pdf_compiler_runs_two_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "resume.tex"
            source.write_text(r"\documentclass{article}", encoding="utf-8")

            def successful_run(*args, **kwargs):
                (root / "resume__build.pdf").write_bytes(b"%PDF-1.5")
                (root / "resume__build.log").write_text("clean", encoding="utf-8")
                return CompletedProcess(args[0], 0, stdout="", stderr="")

            with (
                patch.object(compile_cv, "find_pdflatex", return_value=Path("pdflatex")),
                patch.object(compile_cv.subprocess, "run", side_effect=successful_run) as runner,
            ):
                output = compile_cv.compile_pdf(source)

            self.assertEqual(output, root / "resume.pdf")
            self.assertEqual(runner.call_count, 2)

    def test_pdf_compiler_reports_first_pass_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "resume.tex"
            source.write_text(r"\documentclass{article}", encoding="utf-8")
            failure = CompletedProcess(["pdflatex"], 1, stdout="failed", stderr="")

            with (
                patch.object(compile_cv, "find_pdflatex", return_value=Path("pdflatex")),
                patch.object(compile_cv.subprocess, "run", return_value=failure),
            ):
                with self.assertRaisesRegex(RuntimeError, "pass 1"):
                    compile_cv.compile_pdf(source)

    def test_pdf_compiler_reports_second_pass_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "resume.tex"
            source.write_text(r"\documentclass{article}", encoding="utf-8")
            calls = 0

            def fail_second_pass(*args, **kwargs):
                nonlocal calls
                calls += 1
                (root / "resume__build.pdf").write_bytes(b"%PDF-1.5")
                return CompletedProcess(args[0], 0 if calls == 1 else 1, stdout="failed", stderr="")

            with (
                patch.object(compile_cv, "find_pdflatex", return_value=Path("pdflatex")),
                patch.object(compile_cv.subprocess, "run", side_effect=fail_second_pass),
            ):
                with self.assertRaisesRegex(RuntimeError, "pass 2"):
                    compile_cv.compile_pdf(source)

    def test_resolves_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_dir = root / "job"
            source_dir.mkdir()
            expected = source_dir / compile_cv.MASTER_TEX_NAME
            expected.write_text("test", encoding="utf-8")
            self.assertEqual(compile_cv.resolve_tex("job", root), expected.resolve())


if __name__ == "__main__":
    unittest.main()
