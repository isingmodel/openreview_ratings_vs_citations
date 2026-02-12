import subprocess
import textwrap
from pathlib import Path


def run(cmd, cwd: Path, log_path: Path):
    """Run command, capture stdout/stderr to log file, and raise on failure."""
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
    )
    with log_path.open("a", encoding="utf-8") as f:
        f.write(
            f"$ {' '.join(cmd)}\n\n"
            f"--- STDOUT ---\n{proc.stdout}\n\n"
            f"--- STDERR ---\n{proc.stderr}\n"
        )
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd, proc.stdout, proc.stderr)


def convert_to_pdf(input_file: str, output_file: str):
    input_path = Path(input_file).resolve()
    out_path = Path(output_file).resolve()
    workdir = input_path.parent

    header_tex = workdir / "_pandoc_header.tex"
    header_tex.write_text(
        textwrap.dedent(r"""
        \usepackage{amsmath,amssymb}
        \usepackage{microtype}
        \usepackage{graphicx}
        \usepackage{booktabs}
        \usepackage{caption}
        \usepackage{fancyhdr}

        \setlength{\columnsep}{0.8cm}

        \pagestyle{fancy}
        \fancyhf{}
        \fancyhead[C]{\textit{Draft}}
        \fancyhead[R]{\thepage}
        \renewcommand{\headrulewidth}{0.2pt}
        """).lstrip(),
        encoding="utf-8",
    )

    log_path = workdir / "pandoc_build.log"
    log_path.write_text("", encoding="utf-8") # Clear log

    base = [
        "pandoc",
        str(input_path),
        "-o", str(out_path),
        "--from=markdown+tex_math_dollars+tex_math_single_backslash",
        "-V", "documentclass=article",
        "-V", "classoption=twocolumn",
        "-V", "fontsize=10pt",
        "-V", "geometry=margin=2cm",
        "-V", "papersize=a4",
        "-H", str(header_tex),
        f"--resource-path={workdir}",
        "--verbose",
        "--pdf-engine-opt=-halt-on-error",
        "--pdf-engine-opt=-interaction=nonstopmode",
    ]

    attempts = [
        # 1) xelatex + fontspec fonts (mac에서 폰트 없으면 여기서 자주 터짐)
        base + [
            "--pdf-engine=xelatex",
            "-V", "mainfont=Times New Roman",
            "-V", "mathfont=TeX Gyre Termes Math",
        ],
        # 2) xelatex but NO explicit fonts (폰트 문제 제거)
        base + [
            "--pdf-engine=xelatex",
        ],
        # 3) lualatex fallback
        base + [
            "--pdf-engine=lualatex",
        ],
    ]

    last_err = None
    for i, cmd in enumerate(attempts, start=1):
        try:
            run(cmd, cwd=workdir, log_path=log_path)
            print(f"✅ Success (attempt {i}): {out_path}")
            print(f"🧾 Log saved: {log_path}")
            return
        except subprocess.CalledProcessError as e:
            last_err = e
            # 다음 시도로 넘어감

    print("❌ All attempts failed.")
    print(f"🧾 See detailed log: {log_path}")
    # 마지막 에러를 다시 던져서 CI/스크립트가 실패를 감지하게 함
    raise last_err


if __name__ == "__main__":
    convert_to_pdf("./paper/draft.md", "./paper/draft.pdf") #"draft.md"
