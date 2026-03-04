import unittest
from unittest.mock import patch, MagicMock
import os

# 假设你的根目录在 PYTHONPATH 中，或者用相对/绝对路径导入
from src.notifier.email_sender import EmailNotifier

class TestEmailNotifier(unittest.TestCase):
    
    def setUp(self):
        """测试前的环境准备，注入虚拟的测试环境变量"""
        os.environ["SMTP_HOST"] = "smtp.test.com"
        os.environ["SMTP_PORT"] = "465"
        os.environ["SMTP_USERNAME"] = "test@test.com"
        os.environ["SMTP_PASSWORD"] = "fake_auth_code"
        os.environ["SENDER_EMAIL"] = "test@test.com"
        self.notifier = EmailNotifier()

    @patch('src.notifier.email_sender.smtplib.SMTP_SSL')
    def test_send_email_success(self, mock_smtp_ssl):
        """测试配置正确时的发送逻辑"""
        # 设置 mock 对象的行为
        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server
        
        # 执行发送
        result = self.notifier.send_email(
            receiver_email="receiver@test.com",
            subject="Test Subject",
            html_content="<h1>Test</h1>"
        )
        
        # 验证结果
        self.assertTrue(result)
        # 验证底层方法是否被正确调用
        mock_smtp_ssl.assert_called_once_with("smtp.test.com", 465)
        mock_server.login.assert_called_once_with("test@test.com", "fake_auth_code")
        mock_server.send_message.assert_called_once()

    def test_missing_credentials(self):
        """测试缺少环境变量时的防御逻辑"""
        # 清除密码环境变量
        os.environ.pop("SMTP_PASSWORD", None)
        bad_notifier = EmailNotifier()
        
        result = bad_notifier.send_email(
            receiver_email="receiver@test.com",
            subject="Test Subject",
            html_content="<h1>Test</h1>"
        )
        
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
    