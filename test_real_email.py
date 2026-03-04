import os
import sys
from dotenv import load_dotenv

# 1. 强制将项目根目录加入系统路径，避免找不到 src 模块
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# 2. 加载 .env 文件中的真实密码和配置
load_dotenv(os.path.join(project_root, '.env'))

from src.notifier.email_sender import EmailNotifier

def main():
    # 检查环境变量是否成功加载
    if not os.getenv("SMTP_PASSWORD"):
        print("❌ 错误：未能从 .env 加载到 SMTP_PASSWORD，请检查 .env 文件名和路径！")
        return

    print(f"正在使用 SMTP 服务器: {os.getenv('SMTP_HOST')}:{os.getenv('SMTP_PORT')}")
    print(f"发件人账号: {os.getenv('SMTP_USERNAME')}")

    # ==========================================
    # 请在这里填入你想测试接收邮件的真实邮箱地址！
    # ==========================================
    receiver = "realandrewfeng@163.com"  
    
    subject = "🚀 ArXiv Agent - 真实环境发信测试"
    html_test = """
    <html>
        <body style="background:#f4f7f6; padding:20px; font-family:sans-serif;">
            <div style="background:white; padding:20px; border-radius:8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color: #2b6cb0;">你好！这是一封真实的联调测试邮件。</h2>
                <p>如果能在收件箱看到这封信，说明你的 <strong>SMTP 和 .env 配置</strong> 已经完美工作！</p>
                <p style="color: #718096; font-size: 14px;">我们马上就可以开始组装主程序 main.py 了。</p>
            </div>
        </body>
    </html>
    """
    
    notifier = EmailNotifier()
    print(f"\n⏳ 正在尝试发送测试邮件到 {receiver} ...")
    
    success = notifier.send_email(receiver, subject, html_test)
    
    if success:
        print("🎉 测试大成功！请去邮箱（或垃圾邮件箱）查收。")
    else:
        print("❌ 发送失败。请检查：")
        print("   1. 授权码是否正确填入 .env 的 SMTP_PASSWORD")
        print("   2. 邮箱是否开启了 SMTP 服务")
        print("   3. 端口是否被云服务器厂商安全组拦截")

if __name__ == "__main__":
    main()