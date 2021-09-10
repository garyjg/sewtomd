
from pathlib import Path
from sewtomd import ConfluenceConverter


def test_image_rename():
    cc = ConfluenceConverter()
    # This sets the resource path.
    cc.set_html_path("SEW/page.html")
    src = "SEW/attachments/1234.jpg"
    # No alt means just change the directory.
    assert cc.rename_image(src, None) == Path("1234.jpg")
    # Use alt if given and add extension.
    assert cc.rename_image(src, "Big Blue World") == Path("Big_Blue_World.jpg")

