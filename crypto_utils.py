"""
加密工具模块 - 用于加密和解密记住的账号密码
使用 Fernet 对称加密
"""

import base64
import hashlib
from cryptography.fernet import Fernet


# 固定密钥种子
_KEY_SEED = "130108"


def _derive_key():
    """从固定种子派生 Fernet 密钥"""
    key = hashlib.sha256(_KEY_SEED.encode()).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_text(plain_text: str) -> str:
    """加密明文字符串，返回密文字符串"""
    f = Fernet(_derive_key())
    return f.encrypt(plain_text.encode()).decode()


def decrypt_text(cipher_text: str) -> str:
    """解密密文字符串，返回明文字符串"""
    f = Fernet(_derive_key())
    return f.decrypt(cipher_text.encode()).decode()


if __name__ == "__main__":
    # 简单测试
    test_email = "test@example.com"
    test_password = "mypassword123"

    enc_email = encrypt_text(test_email)
    enc_password = encrypt_text(test_password)
    print(f"加密邮箱: {enc_email}")
    print(f"加密密码: {enc_password}")

    dec_email = decrypt_text(enc_email)
    dec_password = decrypt_text(enc_password)
    print(f"解密邮箱: {dec_email}")
    print(f"解密密码: {dec_password}")
