import sys
from pathlib import Path

# إضافة مجلد src إلى مسار Python
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# إضافة مجلد المشروع بأكمله
project_path = Path(__file__).parent.parent
sys.path.insert(0, str(project_path))