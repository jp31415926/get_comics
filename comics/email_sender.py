import smtplib
from datetime import date
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from .downloaders.base import ComicResult

_MIME_TYPES = {
    ".gif": "gif",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".png": "png",
}


def _build_html(results: list[ComicResult]) -> str:
    parts = [
        "<html><head><title>Comics</title></head><body>",
        "<font size='-1'>Please report problems (i.e. missing comics) to "
        "<a href='mailto:comics-owner@gcfl.net'>comics-owner@gcfl.net</a>"
        "</font><br>",
    ]

    for result in results:
        parts.append(f"<h2>{result.comic_name}</h2>")
        for img in result.images:
            parts.append(
                f'<p><a href="{result.page_url}">'
                f'<img src="cid:{img.cid}" border=0>'
                f"</a>"
            )
            if img.caption:
                parts.append(img.caption)
            parts.append("</p>\n<hr>")

    parts.append("</body></html>")
    return "\n".join(parts)


def _build_comics_message(results: list[ComicResult], config: dict) -> MIMEMultipart:
    email_cfg = config["email"]

    msg = MIMEMultipart("related")
    msg["From"] = email_cfg["from_addr"]
    msg["To"] = email_cfg["to_addr"]
    msg["Subject"] = date.today().strftime("%Y-%m-%d")

    msg.attach(MIMEText(_build_html(results), "html", "utf-8"))

    for result in results:
        for img_result in result.images:
            path = Path(img_result.image_path)
            mime_subtype = _MIME_TYPES.get(path.suffix.lower(), "jpeg")
            img_data = path.read_bytes()
            img_part = MIMEImage(img_data, _subtype=mime_subtype)
            img_part.add_header("Content-ID", f"<{img_result.cid}>")
            img_part.add_header("Content-Disposition", "inline", filename=path.name)
            msg.attach(img_part)

    return msg


def send_comics_email(results: list[ComicResult], config: dict) -> None:
    email_cfg = config["email"]
    msg = _build_comics_message(results, config)

    with smtplib.SMTP(email_cfg["smtp_host"], email_cfg["smtp_port"]) as smtp:
        smtp.send_message(msg)

    print(f"Comics email sent to {email_cfg['to_addr']}")


def send_error_email(failures: list[tuple[str, str]], config: dict) -> None:
    email_cfg = config["email"]
    errors_to = email_cfg["errors_to"]
    if isinstance(errors_to, list):
        errors_to = ", ".join(errors_to)

    today = date.today().strftime("%Y-%m-%d")
    body = (
        f"The following comics failed to download on {today}:\n\n"
        + "\n".join(f"  - {name}: {error}" for name, error in failures)
        + "\n\nThe comics email was NOT sent."
    )

    msg = MIMEText(body, "plain")
    msg["From"] = email_cfg["from_addr"]
    msg["To"] = errors_to
    msg["Subject"] = f"Comics for {today} failed to download!"

    with smtplib.SMTP(email_cfg["smtp_host"], email_cfg["smtp_port"]) as smtp:
        smtp.send_message(msg)

    print(f"Error notification sent to {errors_to}")
