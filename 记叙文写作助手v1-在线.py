import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QTextEdit, QGridLayout, QWidget, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt
import requests
import os
import random
import string
from datetime import datetime

class WritingAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("记叙文写作助手")
        self.setGeometry(100, 100, 800, 1000)
        self._initUI()

    def _initUI(self):
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QGridLayout()
        widget.setLayout(layout)

        # 输入区域
        self._add_input_field(layout, "主要人物:", 0)
        self._add_input_field(layout, "事件起因:", 1)
        self._add_input_field(layout, "事件经过:", 2)
        self._add_input_field(layout, "事件结果:", 3)
        self._add_input_field(layout, "环境描写:", 4)
        self._add_input_field(layout, "人物描写:", 5)
        self._add_input_field(layout, "情感表达:", 6)

        # 功能按钮
        self.generate_btn = QPushButton("生成记叙文", self)
        self.generate_btn.clicked.connect(self.generate_content)
        layout.addWidget(self.generate_btn, 7, 0, 1, 2)

        # 保存按钮
        self.save_btn = QPushButton('保存作文', self)
        self.save_btn.clicked.connect(self.save_generated_content)
        layout.addWidget(self.save_btn, 8, 0, 1, 2)

        # 输出区域
        self.output_edit = QTextEdit()
        self.output_edit.setReadOnly(True)
        layout.addWidget(QLabel('生成内容:'), 9, 0)
        layout.addWidget(self.output_edit, 9, 1)

        # 版权信息
        copyright_label = QLabel('@天津市南开区南开小学-7jul', self)
        # 在 PyQt5 中，正确的属性名应该是 Qt.AlignHCenter | Qt.AlignVCenter 来实现居中对齐
        copyright_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.addWidget(copyright_label, 10, 0, 1, 2)

    def _add_input_field(self, layout, label, row):
        layout.addWidget(QLabel(label), row, 0)
        text_edit = QTextEdit()
        height = 40 if '主要人物' in label else 80
        text_edit.setFixedHeight(height)
        layout.addWidget(text_edit, row, 1)
        setattr(self, f'input_{row}', text_edit)

    def generate_content(self):
        # 获取输入内容
        inputs = [self.input_0.toPlainText().strip(),
                 self.input_1.toPlainText().strip(),
                 self.input_2.toPlainText().strip(),
                 self.input_3.toPlainText().strip(),
                 self.input_4.toPlainText().strip(),
                 self.input_5.toPlainText().strip(),
                 self.input_6.toPlainText().strip()]
        
        if not all(inputs):
            QMessageBox.warning(self, "输入错误", "请填写所有写作要素！")
            return

        prompt = f"""根据以下写作要素创作一篇中小学生记叙文：
        主要人物：{inputs[0]}
        事件起因：{inputs[1]}
        事件经过：{inputs[2]}
        事件结果：{inputs[3]}
        环境描写：{inputs[4]}
        人物描写：{inputs[5]}
        情感表达：{inputs[6]}
        
        要求语言生动，结构清晰，人物神态、动作等描写生动，适合中小学生阅读。"""

        try:
            response = self._call_ollama_api(prompt)
            if response:
                cleaned = self._remove_think_content(response)
                self.output_edit.setPlainText(cleaned.strip())
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成失败：{str(e)}")

    def _call_ollama_api(self, prompt):
        api_key = self._get_api_key()
        if not api_key:
            raise Exception("未找到API密钥，请创建api.key文件")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的写作助手"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 1600
        }

        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            json=data,
            headers=headers
        )

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            error_msg = f"API请求失败：{response.status_code}\n响应内容：{response.text}\n请求头：{headers}\n请求体：{data}"
            QMessageBox.critical(self, "API错误", error_msg)
            raise Exception(error_msg)

    def _get_api_key(self):
        key_file = os.path.join(os.path.dirname(__file__), "api.key")
        if os.path.exists(key_file):
            with open(key_file, "r") as f:
                return f.read().strip()
        return None

    def _remove_think_content(self, text):
        start = text.find("<think>")
        end = text.find("</think>")
        return text[:start] + text[end + len("</think>"):] if start != -1 and end != -1 else text

    def save_generated_content(self):
        content = self.output_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, '保存失败', '没有可保存的内容，请先生成作文！')
            return

        current_date = datetime.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        filename = f'{current_date}_{random_str}.txt'

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, '保存成功', f'文件已保存为：{filename}')
        except Exception as e:
            QMessageBox.critical(self, '保存失败', f'保存时出错：{str(e)}')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WritingAssistant()
    window.show()
    sys.exit(app.exec())
