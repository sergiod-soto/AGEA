from ebooklib import epub
import os
import re
from pathlib import Path

ROOT_FOLDER = r"Tomodachi game"
OUTPUT_FOLDER = r"epubs"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def natural_sort_key(s):
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r'(\d+)', s)
    ]


def create_epub_from_volume(volume_path):
    volume_name = volume_path.name

    print(f"Generando EPUB: {volume_name}")

    book = epub.EpubBook()

    book.set_identifier(volume_name)
    book.set_title(volume_name)
    book.set_language("es")

    chapters = []

    # Carpetas 01, 02, 03...
    chapter_folders = sorted(
        [f for f in volume_path.iterdir() if f.is_dir()],
        key=lambda x: natural_sort_key(x.name)
    )

    for chapter_folder in chapter_folders:

        chapter_name = chapter_folder.name

        chapter = epub.EpubHtml(
            title=f"Capítulo {chapter_name}",
            file_name=f"{chapter_name}.xhtml",
            lang="es"
        )

        html = [
            "<html><body style='margin:0;padding:0;'>"
        ]

        image_files = sorted(
            [
                f for f in chapter_folder.iterdir()
                if f.suffix.lower() in [".jpg", ".jpeg", ".png"]
            ],
            key=lambda x: natural_sort_key(x.name)
        )

        for idx, image_path in enumerate(image_files):

            with open(image_path, "rb") as f:
                image_content = f.read()

            image_name = f"{chapter_name}_{idx}{image_path.suffix}"

            media_type = "image/jpeg"
            if image_path.suffix.lower() == ".png":
                media_type = "image/png"

            img_item = epub.EpubItem(
                uid=f"{chapter_name}_{idx}",
                file_name=f"images/{image_name}",
                media_type=media_type,
                content=image_content
            )

            book.add_item(img_item)

            html.append(f"""
                <div style="text-align:center; page-break-after:always;">
                    <img src="images/{image_name}"
                         style="width:100%; height:auto;" />
                </div>
            """)

        html.append("</body></html>")

        chapter.content = "\n".join(html)

        book.add_item(chapter)
        chapters.append(chapter)

    book.toc = chapters
    book.spine = ["nav"] + chapters

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    output_path = os.path.join(
        OUTPUT_FOLDER,
        f"{volume_name}.epub"
    )

    epub.write_epub(output_path, book)

    print(f"OK -> {output_path}")


root = Path(ROOT_FOLDER)

volumes = sorted(
    [f for f in root.iterdir() if f.is_dir()],
    key=lambda x: natural_sort_key(x.name)
)

for volume in volumes:
    create_epub_from_volume(volume)

print("Finalizado")