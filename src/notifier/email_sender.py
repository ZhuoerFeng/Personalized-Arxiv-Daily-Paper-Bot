import os
import smtplib
from email.message import EmailMessage
import logging

logger = logging.getLogger(__name__)

class EmailNotifier:
    def __init__(self):
        """
        初始化邮件发送器，从环境变量读取 SMTP 配置。
        """
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.qq.com") # 默认以QQ邮箱为例
        self.smtp_port = int(os.getenv("SMTP_PORT", 465))      # 465 通常为 SSL 端口
        self.username = os.getenv("SMTP_USERNAME")
        self.password = os.getenv("SMTP_PASSWORD")             # 通常是授权码，而非登录密码
        self.sender_email = os.getenv("SENDER_EMAIL", self.username)

    def send_email(self, receiver_email: str, subject: str, html_content: str) -> bool:
        """
        发送 HTML 格式的邮件。
        
        :param receiver_email: 收件人邮箱
        :param subject: 邮件主题
        :param html_content: 渲染好的 HTML 邮件正文
        :return: 发送是否成功
        """
        if not self.username or not self.password:
            logger.error("未配置 SMTP_USERNAME 或 SMTP_PASSWORD 环境变量，取消发送。")
            return False

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = receiver_email
        
        # 设定邮件内容为 HTML 格式
        msg.set_content("请使用支持 HTML 的邮件客户端查看此邮件。") # 纯文本 Fallback
        msg.add_alternative(html_content, subtype='html')

        try:
            # 针对 465 端口使用 SMTP_SSL，针对 587/25 端口通常使用 SMTP + starttls()
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.username, self.password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.username, self.password)
                    server.send_message(msg)
                    
            logger.info(f"✅ 邮件成功发送至 {receiver_email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("❌ SMTP 认证失败，请检查账号和授权码是否正确。")
            return False
        except Exception as e:
            logger.error(f"❌ 邮件发送异常: {e}")
            return False