import asyncio
import random
import string
import time
import re
import os
import csv
import argparse
from datetime import datetime
from DrissionPage import Chromium
import requests
from mailtmapi import MailTM
from colorama import init, Fore, Style

# 初始化colorama
init()


def setup_argparse():
    """设置命令行参数"""
    parser = argparse.ArgumentParser(description='Cursor账号注册工具')
    parser.add_argument('-n', '--number', type=int, default=10,
                        help='要注册的账号数量 (默认: 10)')
    parser.add_argument('--save-tokens', action='store_true',
                        help='将有效token保存到单独的文件')
    parser.add_argument('--skip-null-tokens', action='store_true',
                        help='跳过没有有效token的账号')
    return parser.parse_args()


def handle_turnstile(tab):
    """处理 Turnstile 验证"""
    print("准备处理验证")
    try:
        while True:
            try:
                challengeCheck = (tab.ele('@id=cf-turnstile', timeout=2)
                                  .child()
                                  .shadow_root
                                  .ele("tag:iframe")
                                  .ele("tag:body")
                                  .sr("tag:input"))

                if challengeCheck:
                    print("验证框加载完成")
                    time.sleep(random.uniform(1, 3))
                    challengeCheck.click()
                    print("验证按钮已点击，等待验证完成...")
                    time.sleep(2)
                    return True
            except:
                pass

            if tab.ele('@name=password'):
                print("无需验证")
                break
            if tab.ele('@data-index=0'):
                print("无需验证")
                break
            if tab.ele('Account Settings'):
                print("无需验证")
                break

            time.sleep(random.uniform(1, 2))
    except Exception as e:
        print(e)
        print('跳过验证')
        return False
def log_info(message):
    """输出信息日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.GREEN}[{timestamp}] INFO: {message}{Style.RESET_ALL}")


def log_error(message):
    """输出错误日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.RED}[{timestamp}] ERROR: {message}{Style.RESET_ALL}")


def log_warning(message):
    """输出警告日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.YELLOW}[{timestamp}] WARNING: {message}{Style.RESET_ALL}")


def generate_password(length=12):
    """生成随机密码"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def get_token_from_cookies(cookies):
    """从cookies中提取WorkosCursorSessionToken"""
    return cookies.get('WorkosCursorSessionToken', 'null')


def setup_output_files(args):
    """设置输出文件"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(current_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = os.path.join(output_dir, f'cursor_accounts_{timestamp}.csv')
    token_file = os.path.join(output_dir, f'cursor_tokens_{timestamp}.txt')

    # 创建CSV文件并写入头
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'password', 'cookie', 'token'])

    log_info(f"CSV输出文件: {csv_file}")
    if args.save_tokens:
        log_info(f"Token输出文件: {token_file}")

    return csv_file, token_file


async def get_verification_code(mailtm, token):
    """获取验证码"""
    log_info("等待接收验证码邮件...")
    BASE_URL = "https://api.mail.tm"
    messages = await mailtm.get_messages(token, 1)
    log_info("等待接收验证码邮件11...")
    print(messages)
    message = messages.hydra_member[0]
    log_info("等待接收验证码邮件22...")

    response = requests.get(
        BASE_URL + message.downloadUrl,
        headers={'Authorization': f'Bearer {token}'}
    )
    message_text = response.text.strip().replace('\n', '').replace('\r', '').replace('=', '')
    verify_code = re.search(r'Your verification code is (\d+)', message_text).group(1).strip()
    log_info(f"获取到验证码: {verify_code}")
    return verify_code


async def register_account():
    """注册一个新账户"""
    log_info("开始创建临时邮箱...")
    mailtm = MailTM()
    temp_mail = await mailtm.get_account()
    password = generate_password()
    log_info(f"临时邮箱创建成功: {temp_mail.address}")

    # 初始化浏览器
    log_info("打开注册页面...")
    tab = Chromium().latest_tab
    tab.get("https://authenticator.cursor.sh/sign-up")

    # 输入邮箱
    log_info("输入邮箱地址...")
    email_input = tab.ele("@id=radix-:R2bapnltbnla:")
    email_input.input(temp_mail.address)
    time.sleep(1)
    tab.ele('@text()=Continue').click()
    time.sleep(3)
    # handle_turnstile(tab)
    # try:
    #     if tab.ele('Continue'):
    #         tab.ele('Continue').click()
    #         print("点击Continue")
    # except Exception as e:
    #     print(f"点击Continue失败: {str(e)}")
    # time.sleep(3)
    # handle_turnstile(tab)

    # 输入密码
    log_info("输入密码...")
    tab.wait(3)

    password_input =tab.ele('@name=password')
    password_input.input(password)
    time.sleep(1)
    tab.ele('@text()=Continue').click()
    time.sleep(15)

    # 获取并输入验证码
    verify_code = await get_verification_code(mailtm, temp_mail.token.token)
    log_info("输入验证码...")
    for digit in verify_code:
        tab.actions.key_down(str(digit))
        time.sleep(0.1)
        tab.actions.key_up(str(digit))
    time.sleep(3)
    time.sleep(10)

    # handle_turnstile(tab)
    # 获取cookies
    cookies = tab.cookies().as_dict()
    token = get_token_from_cookies(cookies)
    log_info("注册完成，获取到账号信息")

    return {
        'username': temp_mail.address,
        'password': password,
        'cookie': str(cookies),
        'token': token
    }


async def main():
    args = setup_argparse()
    csv_file, token_file = setup_output_files(args)

    log_info(f"开始注册 {args.number} 个账号...")
    successful_registrations = 0

    for i in range(args.number):
        try:
            log_info(f"\n=== 开始注册第 {i + 1}/{args.number} 个账号 ===")
            account_info = await register_account()

            # 检查token是否为null
            if args.skip_null_tokens and account_info['token'] == 'null':
                log_warning(f"跳过没有token的账号: {account_info['username']}")
                continue

            # 写入CSV文件
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    account_info['username'],
                    account_info['password'],
                    account_info['cookie'],
                    account_info['token']
                ])

            # 如果需要，将token写入单独的文件
            if args.save_tokens and account_info['token'] != 'null':
                with open(token_file, 'a', encoding='utf-8') as f:
                    f.write(f"{account_info['token']}\n")

            successful_registrations += 1
            log_info(f"账号注册成功: {account_info['username']}")
            log_info(f"Token: {account_info['token']}")

        except Exception as e:
            log_error(f"注册失败: {str(e)}")
            continue

    log_info("\n=== 注册完成 ===")
    log_info(f"成功注册账号: {successful_registrations}/{args.number}")
    log_info(f"账号信息已保存到: {csv_file}")
    if args.save_tokens:
        log_info(f"Token已保存到: {token_file}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_warning("\n程序被用户中断")
    except Exception as e:
        log_error(f"程序异常退出: {str(e)}")