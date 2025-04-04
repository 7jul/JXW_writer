import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QTextEdit, QGridLayout,QHBoxLayout,QWidget, QPushButton, QMessageBox, QVBoxLayout, QLineEdit, QComboBox, QDoubleSpinBox)
from PyQt5.QtCore import Qt
from openai import OpenAI
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

        # 功能按钮 - 第一行
        btn_row1 = QHBoxLayout()
        
        self.generate_btn = QPushButton("生成记叙文", self)
        self.generate_btn.clicked.connect(self.generate_content)
        btn_row1.addWidget(self.generate_btn)
        
        self.save_btn = QPushButton('保存作文', self)
        self.save_btn.clicked.connect(self.save_generated_content)
        btn_row1.addWidget(self.save_btn)
        
        layout.addLayout(btn_row1, 7, 0, 1, 2)

        # 功能按钮 - 第二行
        btn_row2 = QHBoxLayout()
        
        self.config_btn = QPushButton("API设置", self)
        self.config_btn.clicked.connect(self.open_config)
        btn_row2.addWidget(self.config_btn)
        
        layout.addLayout(btn_row2, 8, 0, 1, 2)

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
            response = self._call_deepseek_api(prompt)
            if response:
                cleaned = self._remove_think_content(response)
                self.output_edit.setPlainText(cleaned.strip())
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成失败：{str(e)}")

    def _call_deepseek_api(self, prompt):
        settings = self.get_api_settings()
        if not settings or not settings.get("api_key"):
            raise Exception("未找到有效的API配置，请检查api.key文件")
            
        client = OpenAI(
            api_key=settings.get("api_key", ""),
            base_url=settings.get("url", "https://api.deepseek.com")
        )
        
        try:
            response = client.chat.completions.create(
                model=settings.get("model", "deepseek-chat"),
                messages=[
                    {"role": "system", "content": "你是一个专业的写作助手"},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.get("temperature", 0.8),
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"API请求失败：{str(e)}"
            QMessageBox.critical(self, "API错误", error_msg)
            raise Exception(error_msg)

    def get_api_settings(self):
        """读取api.key文件中的所有设置，包括URL、API密钥、模型和temperature参数"""
        key_file = os.path.join(os.path.dirname(__file__), "api.key")
        if not os.path.exists(key_file):
            return None
            
        try:
            with open(key_file, "r") as f:
                content = f.read().strip()
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # 兼容旧格式：只有API密钥的纯文本文件
                    return {"api_key": content}
        except Exception as e:
            QMessageBox.warning(self, "警告", f"读取API设置失败: {str(e)}")
            return None
        return None

    def _remove_think_content(self, text):
        start = text.find("<think>")
        end = text.find("</think>")
        return text[:start] + text[end + len("</think>"):] if start != -1 and end != -1 else text

    def open_config(self):
        """打开API配置窗口"""
        self.config_window = DeepSeekConfigWindow()
        self.config_window.show()

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

class DeepSeekConfigWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeepSeek API 配置工具")
        self.setGeometry(100, 100, 450, 300)
        
        # 主部件
        layout = QVBoxLayout()
        
        # API URL
        layout.addWidget(QLabel("DeepSeek API URL:"))
        self.url_input = QLineEdit("https://api.deepseek.com")
        layout.addWidget(self.url_input)
        
        # API Key
        layout.addWidget(QLabel("API Key:"))
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.key_input)
        
        # 模型选择
        layout.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["deepseek-chat", "deepseek-reasoner"])
        layout.addWidget(self.model_combo)
        
        # Temperature设置
        layout.addWidget(QLabel("Temperature:"))
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 1.5)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(1.0)
        layout.addWidget(self.temp_spin)

        # 按钮
        self.save_btn = QPushButton("保存并关闭")
        self.save_btn.clicked.connect(self.save_and_close)
        layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton("加载设置")
        self.load_btn.clicked.connect(self.load_settings)
        layout.addWidget(self.load_btn)
        
        self.setLayout(layout)
        
        # 尝试加载已有设置
        self.load_settings()
    
    def save_settings(self):
        """保存设置到api.key文件"""
        settings = {
            "url": self.url_input.text(),
            "api_key": self.key_input.text(),
            "model": self.model_combo.currentText(),
            "temperature": round(self.temp_spin.value(), 2)
        }
        
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            api_key_path = os.path.join(current_dir, "api.key")
            with open(api_key_path, "w") as f:
                json.dump(settings, f)
            QMessageBox.information(self, "成功", "设置已保存到api.key文件")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def load_settings(self):
        """从api.key文件加载设置"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            api_key_path = os.path.join(current_dir, "api.key")
            with open(api_key_path, "r") as f:
                settings = json.load(f)
                self.url_input.setText(settings.get("url", "https://api.deepseek.com"))
                self.key_input.setText(settings.get("api_key", ""))
                model = settings.get("model", "deepseek-chat")
                index = self.model_combo.findText(model)
                if index >= 0:
                    self.model_combo.setCurrentIndex(index)
                self.temp_spin.setValue(float(settings.get("temperature", 1.0)))
        except FileNotFoundError:
            pass  # 文件不存在时不报错
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载设置失败: {str(e)}")
            
    def save_and_close(self):
        """保存设置并关闭窗口"""
        self.save_settings()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WritingAssistant()
    window.show()
    sys.exit(app.exec())
